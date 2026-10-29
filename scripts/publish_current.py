#!/usr/bin/env python3
"""
publish_current.py - refresh current_results/ for the PROMOTED model only.

    python3 scripts/publish_current.py --tag v1.3

Run this only when a version becomes the new Agent1 - never for trial or
experiment runs. It (re)writes:

    current_results/CONTEXT.md        copy of the project context
    current_results/model_agent.py    src/student/agent.py, experiment
                                      classes stripped (what we submit)
    current_results/match_stats.csv   history.csv rows for --tag
    current_results/SUMMARY.md        W/D/L, goals, averaged telemetry,
                                      per-match table, replays to watch
    current_results/reports/*.txt     match_report.py output per match

STRATEGY.md and README.md are written by hand and are left alone.
"""
import argparse
import contextlib
import csv
import io
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))
import match_report as mr  # noqa: E402

OUT = os.path.join(HERE, "current_results")
EXP_MARK = "# EXPERIMENTS"


def strip_experiments(src):
    """Drop the experiment section (between the EXPERIMENTS banner and
    class Agent2), keep everything else."""
    lines = src.splitlines(keepends=True)
    try:
        i = next(n for n, l in enumerate(lines) if l.startswith(EXP_MARK))
    except StopIteration:
        return src
    i -= 1                                   # the dashed line above it
    j = next(n for n, l in enumerate(lines) if l.startswith("class Agent2"))
    return "".join(lines[:i] + lines[j:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True, help="history.csv tag of the "
                    "promoted model, e.g. v1.3")
    ap.add_argument("--model", default=os.path.join(HERE, "src", "student",
                                                    "agent.py"))
    a = ap.parse_args()

    os.makedirs(os.path.join(OUT, "reports"), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, "reports")):
        os.remove(os.path.join(OUT, "reports", f))
    shutil.copy(os.path.join(HERE, "CONTEXT.md"), os.path.join(OUT,
                                                               "CONTEXT.md"))
    with open(a.model) as fh:
        model = strip_experiments(fh.read())
    with open(os.path.join(OUT, "model_agent.py"), "w") as fh:
        fh.write(model)

    with open(os.path.join(HERE, "runlogs", "history.csv")) as fh:
        rd = csv.DictReader(fh)
        fields, rows = rd.fieldnames, [r for r in rd if r["tag"] == a.tag]
    if not rows:
        sys.exit(f"no history.csv rows tagged {a.tag!r}")
    with open(os.path.join(OUT, "match_stats.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    agg, table = {}, []
    keys = ("shots", "on_target", "pass_ok", "pass_att", "turnovers",
            "tackles_won", "fouls")
    for r in rows:
        rcg = os.path.join(HERE, "logs", r["stamp"] + ".rcg")
        if not os.path.exists(rcg):
            continue
        ns = argparse.Namespace(team=r["team"], events=20, no_history=True,
                                tag=None, json=False)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            o = mr.report(rcg, ns)
        with open(os.path.join(OUT, "reports", r["stamp"] + ".txt"),
                  "w") as fh:
            fh.write(buf.getvalue())
        for side in ("us", "them"):
            for k in keys:
                agg[(side, k)] = agg.get((side, k), 0) + o[side].get(k, 0)
        for k in ("possession", "in_their_half", "final_third", "our_box"):
            agg[k] = agg.get(k, 0) + o["pos"][k]
        table.append((r["stamp"], r["opp"], int(r["gf"]), int(r["ga"]),
                      o["pos"]["possession"], o["us"].get("shots", 0),
                      o["them"].get("shots", 0)))

    n = len(table)
    gf = sum(t[2] for t in table)
    ga = sum(t[3] for t in table)
    w = sum(t[2] > t[3] for t in table)
    d = sum(t[2] == t[3] for t in table)
    per = lambda k: agg[k] / n
    lines = [
        f"# Current model: {a.tag}",
        "",
        f"_Generated {time.strftime('%Y-%m-%d %H:%M')} by "
        "`scripts/publish_current.py`. Only promoted models go here._",
        "",
        f"**{n} matches: W{w} D{d} L{n - w - d}, goals {gf}-{ga} "
        f"({(gf - ga) / n:+.2f} per match)**",
        "",
        "| per match | us | opponent |",
        "|---|---|---|",
        f"| possession % | {per('possession'):.0f} | "
        f"{100 - per('possession'):.0f} |",
        f"| shots (on target) | {per(('us', 'shots')):.1f} "
        f"({per(('us', 'on_target')):.1f}) | {per(('them', 'shots')):.1f} "
        f"({per(('them', 'on_target')):.1f}) |",
        f"| passes ok/att | {per(('us', 'pass_ok')):.0f}/"
        f"{per(('us', 'pass_att')):.0f} | {per(('them', 'pass_ok')):.0f}/"
        f"{per(('them', 'pass_att')):.0f} |",
        f"| turnovers | {per(('us', 'turnovers')):.1f} | "
        f"{per(('them', 'turnovers')):.1f} |",
        f"| tackles won | {per(('us', 'tackles_won')):.1f} | "
        f"{per(('them', 'tackles_won')):.1f} |",
        f"| fouls | {per(('us', 'fouls')):.1f} | "
        f"{per(('them', 'fouls')):.1f} |",
        "",
        f"Ball in their half {per('in_their_half'):.0f}% · final third "
        f"{per('final_third'):.0f}% · our box {per('our_box'):.1f}%",
        "",
        "## Matches",
        "",
        "| match (replay name) | opp | score | poss % | shots us/them | "
        "report |",
        "|---|---|---|---|---|---|",
    ]
    for stamp, opp, f_, a_, poss, su, st in sorted(table):
        lines.append(f"| {stamp} | {opp} | {f_}-{a_} | {poss:.0f} | "
                     f"{su}/{st} | reports/{stamp}.txt |")
    lines += ["", "Watch any of them with `python3 a3.py watch`.", ""]
    with open(os.path.join(OUT, "SUMMARY.md"), "w") as fh:
        fh.write("\n".join(lines))
    print(f"published {a.tag}: {n} matches -> {OUT}")


if __name__ == "__main__":
    main()
