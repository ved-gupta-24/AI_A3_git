#!/usr/bin/env python3
"""
match_report.py - what happened in a match, and where it went wrong.

    python3 scripts/match_report.py                    latest logs/*.rcg
    python3 scripts/match_report.py logs/X.rcg --team V1
    python3 scripts/match_report.py --tag v1 --json    also dump JSON
    python3 scripts/match_report.py --no-history       don't append history.csv

Sources (all written by `a3.py match`):
    logs/<stamp>.rcg                    ground truth: every touch is exact,
                                        from the per-player kick/tackle/catch
                                        counters and state flags
    runlogs/trace/<stamp>/<TEAM>/*.jsonl  our note() labels -> intent
    runlogs/timing/<stamp>/<TEAM>_*.json  cpu/wall per decision

Everything is reported from OUR side: we attack +x, our goal is x = -52.5.
A row per match is appended to runlogs/history.csv to compare versions.
"""
import argparse
import csv
import glob
import json
import math
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(HERE, "logs")
RUNLOGS = os.path.join(HERE, "runlogs")
REFERENCE = {"FULL", "AGENT2", "STARTER"}

L, GH, PBOX_X, PBOX_W = 52.5, 7.01, 36.0, 20.16
DECAY = 0.94

# rcssserver player state bits
KICK, KICK_FAULT, CATCH, CATCH_FAULT = 0x2, 0x4, 0x10, 0x20
TACKLE, TACKLE_FAULT = 0x1000, 0x2000
YELLOW, RED = 0x40000, 0x80000

RE_BALL = re.compile(r"\(\(b\) (\S+) (\S+) (\S+) (\S+)\)")
RE_HEAD = re.compile(r"^\((l|r) (\d+)\) (\d+) (0x[0-9a-fA-F]+|\d+) "
                     r"(\S+) (\S+) (\S+) (\S+) (\S+)")
RE_STAM = re.compile(r"\(s (\S+)")
RE_CNT = re.compile(r"\(c ([\d ]+)\)")
RE_TEAM = re.compile(r"^\(team (\d+) (\S+) (\S+) (\d+) (\d+)")
RE_MODE = re.compile(r"^\(playmode (\d+) (\S+?)\)")

# playmodes whose suffix names the OFFENDING side
OFFENCES = ("foul_charge", "foul_push", "back_pass", "offside",
            "free_kick_fault", "catch_fault", "foul_multiple_attack",
            "illegal_defense")
# playmodes whose suffix names the side that gets the ball
RESTARTS = ("kick_in", "corner_kick", "goal_kick", "free_kick",
            "indirect_free_kick", "goalie_catch_ball", "kick_off")


# ---------------------------------------------------------------- parsing

class Touch:
    __slots__ = ("t", "side", "unum", "kind", "mode", "x", "y", "speed",
                 "ux", "uy", "outcome", "nxt", "intent")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


def parse(path):
    """-> dict(teams, score, modes[(t, mode)], touches[Touch], cycles[...],
    players{(side,unum): stats}, cards)"""
    m = {"teams": ("?", "?"), "score": (0, 0), "modes": [], "touches": [],
         "cycles": [], "cards": defaultdict(set), "players": {}}
    prev, mode, last_t = {}, "before_kick_off", None
    prev_ball = (0.0, 0.0)
    run = defaultdict(float)
    stam = defaultdict(lambda: 8000.0)
    with open(path, errors="replace") as fh:
        for line in fh:
            if line.startswith("(playmode"):
                mm = RE_MODE.match(line)
                if mm:
                    mode = mm.group(2)
                    m["modes"].append((int(mm.group(1)), mode))
                continue
            if line.startswith("(team"):
                mt = RE_TEAM.match(line)
                if mt:
                    m["teams"] = (mt.group(2), mt.group(3))
                    m["score"] = (int(mt.group(4)), int(mt.group(5)))
                continue
            if not line.startswith("(show"):
                continue
            t = int(line.split(None, 2)[1])
            mb = RE_BALL.search(line)
            bx, by, bvx, bvy = (float(v) for v in mb.groups())
            new_cycle = t != last_t
            for chunk in line.split("((")[2:]:
                mh = RE_HEAD.match("(" + chunk)
                if not mh:
                    continue
                side, unum = mh.group(1), int(mh.group(2))
                st = mh.group(4)
                st = int(st, 16) if st.startswith("0x") else int(st)
                if st == 0:
                    continue
                x, y = float(mh.group(5)), float(mh.group(6))
                mc = RE_CNT.search(chunk)
                if not mc:
                    continue
                cnt = [int(v) for v in mc.group(1).split()]
                ms = RE_STAM.search(chunk)
                key = (side, unum)
                if ms:
                    stam[key] = min(stam[key], float(ms.group(1)))
                if st & YELLOW:
                    m["cards"]["yellow"].add(key)
                if st & RED:
                    m["cards"]["red"].add(key)
                if key in prev:
                    pc, px, py = prev[key]
                    if new_cycle and mode == "play_on":
                        run[key] += math.hypot(x - px, y - py)
                    kind = None
                    if cnt[0] > pc[0] and st & KICK and not st & KICK_FAULT:
                        kind = "kick"
                    elif cnt[8] > pc[8]:
                        kind = "tackle_fail" if st & TACKLE_FAULT else "tackle"
                    elif cnt[3] > pc[3] and st & CATCH and not st & CATCH_FAULT:
                        kind = "catch"
                    if kind:
                        sp = math.hypot(bvx, bvy) / DECAY
                        u = (bvx / sp / DECAY, bvy / sp / DECAY) if sp > 1e-6 \
                            else (0.0, 0.0)
                        m["touches"].append(Touch(
                            t=t, side=side, unum=unum, kind=kind, mode=mode,
                            x=prev_ball[0], y=prev_ball[1], speed=sp,
                            ux=u[0], uy=u[1]))
                prev[key] = (cnt, x, y)
            if new_cycle:
                m["cycles"].append((t, mode, bx, by))
            prev_ball, last_t = (bx, by), t
    for key in prev:
        m["players"][key] = {"run": run[key], "min_stamina": stam[key]}
    return m


# ---------------------------------------------------------------- analysis

def flip(side, x, y):
    return (x, y) if side == "l" else (-x, -y)


def classify(m):
    """Give every touch an outcome: what happened next."""
    touches = [t for t in m["touches"] if t.kind != "tackle_fail"]
    modes = m["modes"]
    for i, a in enumerate(touches):
        b = touches[i + 1] if i + 1 < len(touches) else None
        end = b.t if b else 10 ** 9
        stop = next(((mt, md) for mt, md in modes
                     if a.t < mt <= end and md != "play_on"), None)
        if stop:
            a.outcome, a.nxt = "stop", stop[1]
        elif b is None:
            a.outcome = "end"
        elif b.side == a.side and b.unum == a.unum:
            a.outcome, a.nxt = "kept", b
        elif b.side == a.side:
            a.outcome, a.nxt = "to_mate", b
        else:
            a.outcome, a.nxt = "to_opp", b
    return touches


def is_shot(a):
    """Release that would cross the opponent goal line near the goal."""
    if a.kind != "kick" or a.speed < 1.2:
        return None
    x, y = flip(a.side, a.x, a.y)
    ux, uy = flip(a.side, a.ux, a.uy)
    if ux < 0.2:
        return None
    dist = (L - x) / ux
    if dist > 40.0 or dist > a.speed / (1.0 - DECAY) + 1.0:
        return None
    cy = y + uy * dist
    if abs(cy) > GH + 2.0:
        return None
    return {"on_target": abs(cy) <= GH, "dist": round(dist, 1)}


def label(a):
    """-> one of kept, pass_ok, pass_lost, dispossessed, shot, out, offside,
    foul, goal, setplay ... from the toucher's point of view."""
    if a.mode != "play_on":
        return "setplay"
    if a.outcome == "kept":
        return "kept"
    shot = is_shot(a)
    if a.outcome == "stop":
        md = a.nxt
        if md == "goal_" + a.side:
            return "goal"
        if shot:
            return "shot"
        for o in OFFENCES:
            if md.startswith(o):
                if not md.endswith("_" + a.side):
                    return "won_restart"       # they offended
                return "offside" if o == "offside" else "foul"
        for r in RESTARTS:
            if md.startswith(r):
                return "out" if not md.endswith("_" + a.side) else "won_restart"
        return "stop"
    if shot:
        return "shot"
    if a.outcome == "to_mate":
        return "pass_ok"
    if a.outcome == "to_opp":
        return "pass_lost" if a.speed >= 1.0 else "dispossessed"
    return a.outcome


def third(x):
    return "def" if x < -17.5 else ("att" if x > 17.5 else "mid")


def team_stats(m, touches, side):
    s = Counter()
    zones = Counter()
    per = defaultdict(Counter)
    shots = []
    for a in touches:
        if a.side != side:
            continue
        lab = label(a)
        s["touches"] += 1
        per[a.unum]["touches"] += 1
        if a.kind == "tackle":
            s["tackles_won"] += 1
            per[a.unum]["tackles"] += 1
        if lab in ("pass_ok", "pass_lost"):
            s["pass_att"] += 1
            per[a.unum]["pass_att"] += 1
            if lab == "pass_ok":
                s["pass_ok"] += 1
                per[a.unum]["pass_ok"] += 1
        if lab in ("pass_lost", "dispossessed", "out", "offside", "foul"):
            s["turnovers"] += 1
            s["to_" + lab] += 1
            per[a.unum]["turnovers"] += 1
            zones[third(flip(side, a.x, a.y)[0])] += 1
        if lab in ("shot", "goal"):
            sh = is_shot(a) or {"on_target": True, "dist": 0}
            shots.append(sh)
            s["shots"] += 1
            s["on_target"] += sh["on_target"] or lab == "goal"
            per[a.unum]["shots"] += 1
    fails = [t for t in m["touches"]
             if t.side == side and t.kind == "tackle_fail"]
    s["tackles_failed"] = len(fails)
    s["fouls"] = sum(1 for _t, md in m["modes"]
                     if md.endswith("_" + side) and not md.startswith("offside")
                     and any(md.startswith(o) for o in OFFENCES))
    s["offsides"] = sum(1 for _t, md in m["modes"] if md == "offside_" + side)
    s["yellow"] = sum(1 for k in m["cards"]["yellow"] if k[0] == side)
    s["red"] = sum(1 for k in m["cards"]["red"] if k[0] == side)
    return s, zones, per, shots


def possession(m, touches, side):
    """Share of play_on cycles where we touched the ball last, plus tilt."""
    events = sorted((a.t, a.side) for a in touches)
    i, last = 0, None
    ours = total = tilt = att = defn = box = 0
    for t, mode, bx, by in m["cycles"]:
        while i < len(events) and events[i][0] <= t:
            last = events[i][1]
            i += 1
        if mode != "play_on":
            continue
        total += 1
        ours += last == side
        x, y = flip(side, bx, by)
        tilt += x > 0
        att += x > 17.5
        defn += x < -17.5
        box += x < -L + 16.5 and abs(y) < PBOX_W
    pct = lambda v: round(100.0 * v / total, 1) if total else 0.0
    return {"play_on_cycles": total, "possession": pct(ours),
            "in_their_half": pct(tilt), "final_third": pct(att),
            "def_third": pct(defn), "our_box": pct(box)}


def goal_stories(m, touches, side, limit):
    """For each goal: who lost the ball where, and how fast it went in."""
    out = []
    for gt, md in m["modes"]:
        if md not in ("goal_l", "goal_r"):
            continue
        scorer = md[-1]
        before = [a for a in touches if a.t <= gt]
        if not before:
            continue
        last = before[-1]
        loser = "r" if scorer == "l" else "l"
        lost = next((a for a in reversed(before) if a.side == loser), None)
        stops = [md2 for mt, md2 in m["modes"] if mt <= gt
                 and md2 not in ("play_on", "goal_l", "goal_r")]
        restart = stops[-1] if stops else None
        if len(stops) > 1 and any(stops[-2].startswith(o) for o in OFFENCES):
            restart = f"{stops[-2]}->{restart}"   # e.g. our foul -> their FK
        story = {"t": gt, "for": "us" if scorer == side else "them",
                 "scorer": f"{scorer}{last.unum}",
                 "shot_from": [round(v, 1) for v in flip(side, last.x,
                                                         last.y)]}
        if lost:
            story["lost_by"] = f"{loser}{lost.unum}"
            story["lost_at"] = [round(v, 1) for v in flip(side, lost.x,
                                                          lost.y)]
            story["lost_how"] = label(lost)
            story["lost_intent"] = lost.intent
            story["cycles_to_goal"] = gt - lost.t
            story["their_touches"] = sum(1 for a in before
                                         if a.t > lost.t and a.side == scorer)
        story["last_restart"] = restart
        out.append(story)
    return out[:limit]


# ---------------------------------------------------------------- our logs

def load_trace(stamp, team):
    rows = []
    for f in glob.glob(os.path.join(RUNLOGS, "trace", stamp, team, "*.jsonl")):
        with open(f) as fh:
            for line in fh:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    pass
    return rows


def attach_intent(touches, rows, side):
    """Our touch at rcg time t was decided at trace cycle t-1."""
    by = {}
    for r in rows:
        for n in r.get("notes", []):
            if n["note"].startswith("on:"):
                by[(r["unum"], r["c"])] = n
    for a in touches:
        if a.side == side:
            n = by.get((a.unum, a.t - 1))
            a.intent = n["note"][3:] if n else None
    return by


def intent_table(touches, side, notes):
    """Planned action -> what actually happened, plus P calibration."""
    tab = defaultdict(Counter)
    for a in touches:
        if a.side == side and a.intent:
            tab[a.intent][label(a)] += 1
    calib = defaultdict(lambda: [0, 0, 0.0])
    for a in touches:
        if a.side != side or a.intent not in ("pass", "pass1"):
            continue
        lab = label(a)
        if lab == "kept":
            continue                       # multi-touch kick, not released
        p = (notes.get((a.unum, a.t - 1)) or {}).get("p")
        if p is None:
            continue
        b = ("<0.5" if p < 0.5 else "0.5-0.7" if p < 0.7
             else "0.7-0.85" if p < 0.85 else ">=0.85")
        calib[b][0] += 1
        calib[b][1] += lab == "pass_ok"
        calib[b][2] += p
    return tab, calib


def coordination(rows):
    """Cycles where 2+ of us chased, from the off:intercept labels."""
    per = defaultdict(list)
    for r in rows:
        for n in r.get("notes", []):
            per[r["c"]].append(n["note"])
    multi = sum(1 for v in per.values() if v.count("off:intercept") >= 2)
    roles = Counter(n for v in per.values() for n in v)
    return {"cycles": len(per), "double_chase": multi,
            "labels": dict(roles.most_common())}


def load_timing(stamp, team):
    res = {}
    for f in glob.glob(os.path.join(RUNLOGS, "timing", stamp, f"{team}_*.json")):
        d = json.load(open(f))
        cpu = d.get("cpu_ms") or [0.0]
        s = sorted(cpu)
        res[d["unum"]] = {
            "n": len(cpu), "avg": statistics.mean(cpu),
            "p95": s[int(0.95 * (len(s) - 1))], "max": max(cpu),
            "wall_max": max(d.get("wall_ms") or [0.0]),
            "spent": d.get("spent_ms", 0.0), "killed": d.get("killed", 0),
            "budget": d.get("match_ms", 0.0)}
    return res


# ---------------------------------------------------------------- output

def pick_team(teams, want):
    if want:
        if want not in teams:
            sys.exit(f"team {want!r} not in {teams}")
        return want, "l" if teams[0] == want else "r"
    for i, name in enumerate(teams):
        if name.upper() not in REFERENCE:
            return name, "lr"[i]
    return teams[0], "l"


def fmt_pct(a, b):
    return f"{a}/{b} ({100.0 * a / b:.0f}%)" if b else f"{a}/{b}"


def report(path, a):
    stamp = os.path.basename(path)[:-4]
    m = parse(path)
    team, side = pick_team(m["teams"], a.team)
    other = "r" if side == "l" else "l"
    opp = m["teams"][1] if side == "l" else m["teams"][0]
    gf, ga = m["score"] if side == "l" else m["score"][::-1]

    touches = classify(m)
    rows = load_trace(stamp, team)
    notes = attach_intent(touches, rows, side)
    us, uz, uper, _ = team_stats(m, touches, side)
    them, tz, _, _ = team_stats(m, touches, other)
    pos = possession(m, touches, side)
    stories = goal_stories(m, touches, side, a.events)
    tab, calib = intent_table(touches, side, notes)
    coord = coordination(rows) if rows else None
    timing = load_timing(stamp, team)

    out = {"stamp": stamp, "team": team, "opp": opp, "gf": gf, "ga": ga,
           "us": dict(us), "them": dict(them), "pos": pos,
           "turnover_zones": dict(uz), "goals": stories,
           "intent": {k: dict(v) for k, v in tab.items()},
           "calibration": {k: v for k, v in calib.items()},
           "coordination": coord, "timing": timing}

    p = print
    p(f"\n=== {team} {gf}-{ga} {opp}   ({stamp}, side {side}, "
      f"{pos['play_on_cycles']} play_on cycles)")
    p(f"{'':22}{team:>14}{opp:>14}")
    rowsx = [
        ("possession %", pos["possession"], round(100 - pos["possession"], 1)),
        ("passes ok/att", fmt_pct(us["pass_ok"], us["pass_att"]),
         fmt_pct(them["pass_ok"], them["pass_att"])),
        ("turnovers", us["turnovers"], them["turnovers"]),
        ("  intercepted", us["to_pass_lost"], them["to_pass_lost"]),
        ("  dispossessed", us["to_dispossessed"], them["to_dispossessed"]),
        ("  out of play", us["to_out"], them["to_out"]),
        ("  offside", us["offsides"], them["offsides"]),
        ("shots (on target)", f"{us['shots']} ({us['on_target']})",
         f"{them['shots']} ({them['on_target']})"),
        ("tackles won/failed", f"{us['tackles_won']}/{us['tackles_failed']}",
         f"{them['tackles_won']}/{them['tackles_failed']}"),
        ("fouls / yellow / red", f"{us['fouls']}/{us['yellow']}/{us['red']}",
         f"{them['fouls']}/{them['yellow']}/{them['red']}"),
    ]
    for name, x, y in rowsx:
        p(f"  {name:20}{str(x):>14}{str(y):>14}")
    p(f"  ball in their half {pos['in_their_half']}%  final third "
      f"{pos['final_third']}%  our third {pos['def_third']}%  "
      f"our box {pos['our_box']}%")
    p(f"  our turnovers by zone: def {uz['def']}  mid {uz['mid']}  "
      f"att {uz['att']}")

    if timing:
        allcpu = [v for v in timing.values()]
        p(f"\n  cpu ms/decision     avg {statistics.mean(v['avg'] for v in allcpu):.2f}"
          f"  p95 {max(v['p95'] for v in allcpu):.2f}"
          f"  max {max(v['max'] for v in allcpu):.1f}"
          f"  wall max {max(v['wall_max'] for v in allcpu):.1f}"
          f"  total(max player) {max(v['spent'] for v in allcpu)/1000:.2f}s"
          f" of {allcpu[0]['budget']/1000:.0f}s"
          f"  cut-offs {sum(v['killed'] for v in allcpu)}")

    p("\n  per player     touch  pass ok/att  turnover  shots  tackles"
      "   run m  min stam")
    for u in sorted(uper):
        c = uper[u]
        pl = m["players"].get((side, u), {})
        p(f"    #{u:<11}{c['touches']:>6}  {fmt_pct(c['pass_ok'], c['pass_att']):>11}"
          f"{c['turnovers']:>10}{c['shots']:>7}{c['tackles']:>9}"
          f"{pl.get('run', 0):>8.0f}{pl.get('min_stamina', 0):>10.0f}")

    if tab:
        p("\n  planned (note) -> actual outcome of that touch")
        for k in sorted(tab, key=lambda k: -sum(tab[k].values())):
            p(f"    {k:8} " + "  ".join(f"{o}:{n}" for o, n in
                                         tab[k].most_common()))
    if calib:
        p("\n  pass P calibration   n   predicted  actual")
        for b in ("<0.5", "0.5-0.7", "0.7-0.85", ">=0.85"):
            if b in calib:
                n, ok, ps = calib[b]
                p(f"    {b:12}{n:>9}{ps / n:>11.2f}{ok / n:>8.2f}")
    if coord:
        p(f"\n  coordination: {coord['double_chase']} of {coord['cycles']} "
          "cycles had 2+ of us chasing")
    if stories:
        p("\n  goals")
        for g in stories:
            how = (f"lost by {g.get('lost_by')} at {g.get('lost_at')} "
                   f"({g.get('lost_how')}"
                   + (f", planned {g['lost_intent']}" if g.get('lost_intent') else "")
                   + f"), {g.get('cycles_to_goal')} cycles / "
                   f"{g.get('their_touches')} touches to goal") \
                if "lost_by" in g else ""
            p(f"    t={g['t']:<5} {g['for']:5} shot from {g['shot_from']}  {how}"
              f"  [last restart: {g['last_restart']}]")
    p("")

    if not a.no_history:
        hist = os.path.join(RUNLOGS, "history.csv")
        new = not os.path.exists(hist)
        allcpu = list(timing.values())
        with open(hist, "a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["stamp", "tag", "team", "opp", "gf", "ga", "poss",
                            "pass_ok", "pass_att", "turnovers", "shots",
                            "on_target", "opp_shots", "tilt", "cpu_avg",
                            "cpu_max", "cpu_total_s"])
            w.writerow([stamp, a.tag or "", team, opp, gf, ga,
                        pos["possession"], us["pass_ok"], us["pass_att"],
                        us["turnovers"], us["shots"], us["on_target"],
                        them["shots"], pos["in_their_half"],
                        round(statistics.mean(v["avg"] for v in allcpu), 3)
                        if allcpu else "",
                        round(max(v["max"] for v in allcpu), 2) if allcpu else "",
                        round(max(v["spent"] for v in allcpu) / 1000, 2)
                        if allcpu else ""])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("rcg", nargs="*")
    ap.add_argument("--team")
    ap.add_argument("--tag")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--events", type=int, default=12)
    ap.add_argument("--no-history", action="store_true")
    a = ap.parse_args()
    paths = a.rcg or sorted(glob.glob(os.path.join(LOGS, "*.rcg")),
                            key=os.path.getmtime)[-1:]
    if not paths:
        sys.exit("no rcg logs found")
    res = [report(p, a) for p in paths]
    if a.json:
        print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
