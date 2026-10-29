# Your agent goes here. The Agent1 class must hold your final submission.
#
# Model (see report.txt):
#   on_ball  - depth-limited expectiminimax over a sampled action set.
#              MAX = our kick/dribble/hold, MIN = the opponent that reaches
#              the ball first, CHANCE = sigmoid of the reach-time margin.
#              Leaves are scored by one linear Eval(s) in goal units.
#   off_ball - every player solves the same 4! role assignment from the
#              shared full state (no communication needed), then picks its
#              spot by the same Eval the ball carrier will use.

import math
import time
from bisect import bisect_left
from itertools import permutations

from pyrusgeom.geom_2d import Sector2D, Vector2D
from src.student.interface import StarterAgent, Action, Tools, note


INF = 1000
KICKS = ("pass", "shot3")          # emitted through Action.kick, may shield
SLOW = ("pass", "shot3", "dribble", "hold")   # ball stays at our feet a while


def _dash_table(accel=0.6, decay=0.4, vmax=1.05, n=150):
    """Cumulative metres covered from rest after k full-power dashes."""
    cum, v, x = [], 0.0, 0.0
    for _ in range(n):
        v = min(vmax, v + accel)
        x += v
        cum.append(x)
        v *= decay
    return cum


_DASH = _dash_table()


class _P:
    """A player as plain floats. f* = where it coasts to if it stops."""
    __slots__ = ("unum", "x", "y", "fx", "fy", "bc", "bs", "fast", "goalie")

    def __init__(self, p):
        self.unum = p.uniform_number
        self.x, self.y = p.position.x(), p.position.y()
        vx, vy = p.velocity.x(), p.velocity.y()
        self.fx, self.fy = self.x + vx * 0.67, self.y + vy * 0.67
        b = math.radians(p.body_direction)
        self.bc, self.bs = math.cos(b), math.sin(b)
        self.fast = vx * vx + vy * vy > 0.16
        self.goalie = bool(p.is_goalie)


class _Ctx:
    """One cycle's world, built once by snapshot()."""
    __slots__ = ("cycle", "bx", "by", "bvx", "bvy", "me", "mates", "ours",
                 "onside", "opps", "offside_x", "our_gk", "opp_tackle",
                 "no_smart", "L", "Wd", "gh", "decay", "vmax",
                 "max_accel", "gk", "gk_shot", "kick_mate", "kick_opp", "stamina",
                 "stamina_max", "body", "opp_reach_ball", "pbox_x", "pbox_w")


class Cand:
    __slots__ = ("kind", "tx", "ty", "v0", "delay", "arrive", "unum",
                 "ub", "eu", "p", "bonus")

    def __init__(self, kind, tx, ty, v0=0.0, delay=0, arrive=1, unum=0):
        self.kind, self.tx, self.ty = kind, tx, ty
        self.v0, self.delay, self.arrive, self.unum = v0, delay, arrive, unum
        self.ub = self.eu = self.p = 0.0
        self.bonus = 0.0


def reach_steps(p, x, y, r=1.0):
    """Cycles for player p to get within r of (x, y): dashes + turns."""
    dx, dy = x - p.fx, y - p.fy
    raw = math.sqrt(dx * dx + dy * dy)
    d = raw - r
    if d <= 0:
        return 0
    n = bisect_left(_DASH, d) + 1
    c = (dx * p.bc + dy * p.bs) / raw
    if c < 0.9:
        n += 1
        if c < -0.2 and p.fast:
            n += 1
    return n


def _first_t(p, pts, r, out, limit=INF, gk=None):
    """First cycle t (pts[t-1]) at which p can be on the ball, else INF.
    gk = (box_x, box_half_w, catch_r, back_penalty, back_thr, speed,
    react) for their keeper: speed scales his sprint, react = cycles before
    he moves (fitted on real shots, see Agent1._shot_value)."""
    fx, fy, bc, bs, fast = p.fx, p.fy, p.bc, p.bs, p.fast
    for i in range(len(pts)):
        t = i + 1
        if t >= limit:
            return INF
        x, y = pts[i]
        rr, pen, sc = r, 0, 1.0
        if gk is not None and x > gk[0] and -gk[1] < y < gk[1]:
            rr, sc, pen = gk[2], gk[5], gk[6]
            if x > fx + gk[4]:     # keeper cannot dash backwards (quirk)
                pen += gk[3]
        dx, dy = x - fx, y - fy
        raw = math.sqrt(dx * dx + dy * dy)
        d = (raw - rr) / sc
        if d <= 0:
            return t
        if t - 1 < len(_DASH) and d > _DASH[t - 1]:
            continue
        n = bisect_left(_DASH, d) + 1 + pen
        c = (dx * bc + dy * bs) / raw
        if c < 0.9:
            n += 1
            if c < -0.2 and fast:
                n += 1
        if n <= t:
            return t
    if out or not pts:
        return INF
    x, y = pts[-1]                 # ball has stopped: race to its rest point
    t = max(len(pts) + 1, reach_steps(p, x, y, r))
    return t if t < limit else INF


class Agent1(StarterAgent):
    """Expectiminimax on the ball, CSP role assignment off it."""

    SUPPORT_RINGS = ((4.0, 0.0), (8.0, 22.5))   # support_spot sampling

    W = {
        # Eval(s), in goal units (a goal = 1.0). v1.2: steeper progress and
        # a much bigger shot-threat term - FULL scored 8 of its 10 shots on
        # target, all from 14-20m, so the ball there is worth far more.
        "goal": 1.0, "base": 0.01, "prog_lin": 0.05, "prog": 0.06,
        "xg": 0.9, "xg_scale": 12.0, "xg_range": 35.0, "xg_ang": 0.5,
        "space_r": 8.0, "space_min": 0.55, "out_frac": 0.7,
        # chance node: P = p_max * sigmoid(k * (margin - m0))
        "k": 1.1, "m0": 1.0, "p_max": 0.97, "k_shot": 1.0, "shot_m0": 0.5,
        "shot_noise": 0.03, "shot_noise0": 0.3,   # shot_m0 measured: 15 of
        # our 22 shots scored, even ones the old model put at P=0.3-0.5
        "pass_calib": 0.90,          # measured: P>=0.85 passes landed 82-88%
        # reach radii
        "r_our": 1.0, "r_opp": 1.2, "r_drib": 1.2, "catch_r": 1.3,
        "gk_back_pen": 1,
        # their keeper vs a SHOT, fitted on 98 unblocked shots at FULL's
        # keeper: full sprint after 1 cycle, 1.2m catch, and he saves all
        # he can reach - P = sig(1.2 (margin - 2)) (log-loss 0.13)
        "gk_speed": 1.0, "gk_shot_r": 1.2, "gk_back_thr": 0.5,
        "gk_react": 1, "gk_k": 1.2, "gk_m0": 2.0,
        # candidate generation
        "pass_end_speed": 1.4, "pass_min": 3.0, "pass_max": 40.0,
        "rings": ((3.0, 12), (6.0, 12)), "lead_r": 10.0, "lead_n": 12,
        "space_d": (12.0, 18.0, 25.0), "space_a": (-50, -25, 0, 25, 50),
        "press_steps": 3, "pass1_min": 1.2,
        "two_step_gain": 1.0, "shot_range": 30.0, "shot_range_gk_out": 40.0,
        "gk_out_dist": 6.0, "shot1_min": 2.2, "n_shots": 9,
        # measured: smart-kick shots leave at median 2.42 m/s, not vmax
        # (49 shot3: 41% scored; 58 shot1 at 2.94: 67%)
        "shot3_v": 2.4,
        "drib_dists": (3.5, 7.0, 11.0),
        "drib_offs": (0, 20, -20, 40, -40, 65, -65, 90, -90, 135, -135),
        # measured: ~2 dribble touches lost in 120, so an opponent reaching
        # the path a cycle or two early is a contest, not a loss
        "drib_speed": 0.7, "drib_m0": -2.0, "hold_decay": 0.92,
        "clear_dist": 30.0, "offside_margin": 0.3, "tmax": 40,
        # search
        "on_ms": 60.0, "off_ms": 15.0, "on_mult": 6.0, "wall_margin": 300.0,
        "beam": 16, "disc": 0.9, "commit": 0.01, "max_repeat": 4,
        "accept_late": 3,
        # off ball
        "contest": 2, "trail_dx": 9.0, "trail_dy": 7.0,
        "fwd_dx": 12.0, "wide_dx": 3.0, "wide_dy": 14.0,
        "back_dx": 15.0, "back_max_x": -5.0, "press_gap": 1.5, "mark_gap": 2.0,
        "cover_frac": 0.55, "cover_min": 8.0, "mark_skip_r": 3.0,
        "w_press": 1.6, "w_mark": 1.0, "w_cover": 0.8,
        "threat_speed": 0.8, "threat_stop": 12.0, "press_lead": 0,
        "space_min_x": -17.5,
        "crowd_r": 7.0, "crowd": 0.03, "travel": 0.01, "spot_keep": 0.004,
        # stamina: librcsc stops dashing at ~2446, where a player crawls
        "stam_low": 3000.0, "stam_mid": 4500.0, "trot": 45.0,
        "stam_floor": 2800.0, "stam_guard": 3400.0,   # even when urgent
        "danger_r": 35.0,
        # tackle (foul_risk measured: 4 of 5 tackles on a controlled ball)
        "tackle_p_min": 0.6, "foul_risk": 0.7, "tackle_accel": 2.7,
        "tackle_margin": 0.0, "emerg_r": 20.0, "emerg_p": 0.8,
        # MIN's immediate reply (measured: 12 of 14 lost dribbles had an
        # opponent within ~1.6m): steal before a slow action completes
        "tight_w": 0.8, "stuck_max": 3,
        # our keeper catching our own ball = back-pass, indirect FK
        "gk_avoid": 3.5,
    }

    def __init__(self):
        super().__init__()
        self._plan = None          # (cycle, kind, tx, ty, repeats)
        self._black = {}           # (kind, x, y) -> cycle it expires
        self._spot = None          # last support spot, for hysteresis
        self._stuck = 0            # consecutive smart kicks, ball not gone

    # ------------------------------------------------------------------
    # 1. DISPATCHERS
    # ------------------------------------------------------------------

    def on_ball(self, agent) -> None:
        t0 = time.perf_counter()
        c = self.snapshot(agent)
        deadline = t0 + self._allow_ms(agent, c, True) / 1000.0
        cands = (self.gen_shots(c) + self.gen_passes(c)
                 + self.gen_dribbles(c) + self.gen_safe(c))
        self._apply_memory(c, cands)
        ranked, deep = self.search(c, cands, deadline)
        best = ranked[0]
        self.emit(agent, ranked)
        self._remember(c, best)
        shot = next((k for k in ranked if k.kind in ("shot1", "shot3")), None)
        note(agent, "on:" + best.kind, to=best.unum,
             t=[round(best.tx, 1), round(best.ty, 1)], eu=round(best.eu, 4),
             p=round(best.p, 3), n=len(ranked), d2=deep,
             sh=[round(shot.eu, 3), round(shot.p, 3)] if shot else None,
             ms=round((time.perf_counter() - t0) * 1000.0, 2))

    def off_ball(self, agent) -> None:
        c = self.snapshot(agent)
        d = self.should_tackle(c, agent)
        if d is not None:
            Action.tackle(agent, d, False)
            Action.intercept(agent)
            note(agent, "off:tackle", pr=round(agent.wm.self.tackle_probability, 2),
                 dir=d)
            return

        phase, roles, q = self.assign_roles(c)
        role, spot = roles.get(c.me.unum, ("home", None))
        it = agent.wm.intercept_table
        if (role != "intercept" and not c.kick_mate
                and it.self_reach_steps <= 1
                and it.self_reach_steps < it.first_opponent_reach_steps):
            role = "intercept"     # the proxy says the ball is at my feet

        if role == "intercept":
            Action.intercept(agent)
            Action.go_to_point(agent, Vector2D(c.bx, c.by))
            note(agent, "off:intercept", ph=phase)
            return

        if role in ("fwd", "wide", "back"):
            spot = self.support_spot(c, spot, q)
        if spot is None:
            h = Tools.home_position(agent)
            spot = (h.x(), h.y())
        dist = math.hypot(spot[0] - c.me.x, spot[1] - c.me.y)
        urgent = role == "press" or (
            role in ("mark", "cover")
            and (math.hypot(c.bx + c.L, c.by) < self.W["danger_r"]
                 or c.me.x > c.bx - 1.0))      # recovery run: get goal-side
        Action.go_to_point(agent, Vector2D(spot[0], spot[1]),
                           max_dash_power=self._dash(c, role, dist, urgent))
        Action.turn_to_ball(agent)
        note(agent, "off:" + role, ph=phase,
             s=[round(spot[0], 1), round(spot[1], 1)])

    # ------------------------------------------------------------------
    # 2. STATE
    # ------------------------------------------------------------------

    def snapshot(self, agent):
        wm, sp = agent.wm, agent.server_params
        c = _Ctx()
        c.cycle = wm.cycle
        c.bx, c.by = wm.ball.position.x(), wm.ball.position.y()
        c.bvx, c.bvy = wm.ball.velocity.x(), wm.ball.velocity.y()
        c.me = _P(wm.self)
        c.mates = [_P(p) for p in wm.teammates
                   if p.uniform_number > 0 and not p.is_goalie]
        c.ours = sorted(c.mates + [c.me], key=lambda p: p.unum)
        c.opps = [_P(p) for p in wm.opponents if p.uniform_number > 0]
        c.offside_x = wm.offside_line_x
        line = c.offside_x - self.W["offside_margin"]
        c.onside = [m for m in c.mates if not (m.x > 0 and m.x > line)]
        c.L, c.Wd = sp.pitch_half_length, sp.pitch_half_width
        c.gh = sp.goal_width / 2.0
        c.decay, c.vmax = sp.ball_decay, sp.ball_speed_max
        c.max_accel = min(sp.max_power * wm.self.kick_rate, sp.ball_accel_max)
        c.pbox_x = c.L - sp.penalty_area_length
        c.pbox_w = sp.penalty_area_half_width
        W = self.W
        c.gk = (c.pbox_x, c.pbox_w, W["catch_r"], W["gk_back_pen"], 1.0,
                1.0, 0)
        c.gk_shot = (c.pbox_x, c.pbox_w, W["gk_shot_r"], W["gk_back_pen"],
                     W["gk_back_thr"], W["gk_speed"], W["gk_react"])
        c.kick_mate = wm.kickable_teammate_existance
        c.kick_opp = wm.kickable_opponent_existance
        c.stamina, c.stamina_max = wm.self.stamina, sp.stamina_max
        c.body = wm.self.body_direction
        c.opp_reach_ball = min((reach_steps(o, c.bx, c.by, self.W["r_drib"])
                                for o in c.opps), default=INF)
        c.our_gk = next((_P(p) for p in wm.teammates
                         if p.is_goalie and p.uniform_number > 0), None)
        c.opp_tackle = 0.0                     # MIN's reply next cycle
        for o in c.opps:
            d = math.hypot(o.x - c.bx, o.y - c.by)
            if d < sp.tackle_dist:
                c.opp_tackle = max(c.opp_tackle,
                                   1.0 - (d / sp.tackle_dist) ** 6)
        c.no_smart = self._stuck >= self.W["stuck_max"]
        return c

    def ball_path(self, c, x, y, ux, uy, v0, delay=0, steps=None):
        """Ball positions for t = 1, 2, ...; the first `delay` cycles it is
        still being wound up at the kicker's feet. -> (pts, went_out)."""
        pts = [(x, y)] * delay
        v, lim = v0, (steps or self.W["tmax"]) + delay
        while len(pts) < lim:
            x += ux * v
            y += uy * v
            v *= c.decay
            pts.append((x, y))
            if abs(x) > c.L or abs(y) > c.Wd:
                return pts, True
            if steps is None and v < 0.15:
                break
        return pts, False

    def one_step_max(self, c, ux, uy):
        """Fastest ball we can send along (ux, uy) in ONE touch."""
        uv = ux * c.bvx + uy * c.bvy
        disc = c.max_accel ** 2 - (c.bvx ** 2 + c.bvy ** 2) + uv * uv
        if disc < 0:
            return 0.0
        return min(c.vmax, uv + math.sqrt(disc))

    # ------------------------------------------------------------------
    # 3. CANDIDATE GENERATORS (MAX's moves)
    # ------------------------------------------------------------------

    def gen_shots(self, c):
        W = self.W
        gk = next((o for o in c.opps if o.goalie), None)
        rng = W["shot_range"]
        if gk is not None and c.L - gk.x > W["gk_out_dist"]:
            rng = W["shot_range_gk_out"]      # keeper is off his line
        if math.hypot(c.L - c.bx, c.by) > rng:
            return []
        out, n = [], W["n_shots"]
        span = c.gh - 0.6
        for i in range(n):
            gy = -span + 2.0 * span * i / (n - 1)
            d = math.hypot(c.L - c.bx, gy - c.by)
            ux, uy = (c.L - c.bx) / d, (gy - c.by) / d
            v1 = self.one_step_max(c, ux, uy)
            if v1 >= W["shot1_min"]:
                out.append(Cand("shot1", c.L, gy, v1, 0))
            if v1 < 0.95 * c.vmax and not c.no_smart:
                delay = 1 if c.vmax - v1 < 0.8 else 2
                out.append(Cand("shot3", c.L, gy, W["shot3_v"], delay))
        return out

    def gen_passes(self, c):
        W = self.W
        out = []
        pressed = c.opp_reach_ball <= W["press_steps"]
        targets = []                           # (x, y, ring radius, unum)
        for m in c.onside:                     # offside receiver: -inf
            centre = Vector2D(m.fx, m.fy)
            targets.append((m.fx, m.fy, 0.0, m.unum))
            for r, n in W["rings"]:
                targets += [(v.x(), v.y(), r, m.unum)
                            for v in Tools.points_around(centre, r, n)]
            targets += [(v.x(), v.y(), W["lead_r"], m.unum)   # through balls
                        for v in Tools.points_around(centre, W["lead_r"],
                                                     W["lead_n"])
                        if v.x() > m.fx + 2.0]
        base = math.degrees(math.atan2(-c.by, c.L - c.bx))
        space = W["space_d"] if c.bx > W["space_min_x"] else ()
        for d in space:                        # into space: first one there
            for a in W["space_a"]:
                r = math.radians(base + a)
                targets.append((c.bx + d * math.cos(r), c.by + d * math.sin(r),
                                99.0, 0))
        for tx, ty, r, unum in targets:
            if not self._target_ok(c, tx, ty):
                continue
            d = math.hypot(tx - c.bx, ty - c.by)
            ux, uy = (tx - c.bx) / d, (ty - c.by) / d
            v0 = min(c.vmax, W["pass_end_speed"] + (1.0 - c.decay) * d)
            v1 = self.one_step_max(c, ux, uy)
            delay = 0 if v0 <= v1 else (
                1 if v0 - v1 < W["two_step_gain"] else 2)
            if not c.no_smart:
                out.append(Cand("pass", tx, ty, v0, delay,
                                self._arrive_in(c, d, v0), unum))
            if ((pressed and r < 5.0) or c.no_smart) and v1 >= W["pass1_min"]:
                out.append(Cand("pass1", tx, ty, v1, 0, 1, unum))
        return out

    def gen_dribbles(self, c):
        W = self.W
        base = math.degrees(math.atan2(-c.by, c.L - c.bx))
        out = []
        for off in W["drib_offs"]:
            a = math.radians(base + off)
            for D in W["drib_dists"]:
                tx, ty = c.bx + D * math.cos(a), c.by + D * math.sin(a)
                if abs(tx) > c.L - 1.5 or abs(ty) > c.Wd - 1.5:
                    continue
                out.append(Cand("dribble", tx, ty, W["drib_speed"], 0))
        return out

    def gen_safe(self, c):
        side = 1.0 if c.by >= 0 else -1.0
        a = math.radians(35.0 * side)
        D = self.W["clear_dist"]
        tx = max(-c.L + 2, min(c.L - 2, c.bx + D * math.cos(a)))
        ty = max(-c.Wd + 2, min(c.Wd - 2, c.by + D * math.sin(a)))
        return [Cand("hold", c.bx, c.by), Cand("clear", tx, ty, c.vmax, 0)]

    def _target_ok(self, c, tx, ty):
        W = self.W
        if abs(tx) > c.L - 1.0 or abs(ty) > c.Wd - 1.0:
            return False
        if tx < -c.pbox_x and abs(ty) < c.pbox_w:
            return False                       # back-pass to keeper: -inf
        d = math.hypot(tx - c.bx, ty - c.by)
        return W["pass_min"] <= d <= W["pass_max"]

    def _arrive_in(self, c, d, v0):
        q = 1.0 - d * (1.0 - c.decay) / v0
        if q <= 0.01:
            return 60
        return max(1, int(math.ceil(math.log(q) / math.log(c.decay))))

    # ------------------------------------------------------------------
    # 4. MIN AND CHANCE NODES
    # ------------------------------------------------------------------

    def opp_response(self, c, pts, out, r=None):
        """MIN: first cycle any opponent is on the ball path."""
        r = self.W["r_opp"] if r is None else r
        best = INF
        for o in c.opps:
            t = _first_t(o, pts, r, out, best, c.gk if o.goalie else None)
            if t < best:
                best = t
        return best

    def our_response(self, c, pts, out):
        """First cycle an ONSIDE teammate is on the ball path (an offside
        one touching it gives a free kick, so it does not count)."""
        best = INF
        for m in c.onside:
            t = _first_t(m, pts, self.W["r_our"], out, best)
            if t < best:
                best = t
        return best

    def success_prob(self, margin, k=None, m0=None):
        W = self.W
        if margin >= INF // 2:
            return W["p_max"]
        if margin <= -INF // 2:
            return 0.0
        k = W["k"] if k is None else k
        m0 = W["m0"] if m0 is None else m0
        z = max(-30.0, min(30.0, k * (margin - m0)))
        return W["p_max"] / (1.0 + math.exp(-z))

    # ------------------------------------------------------------------
    # 5. EVALUATION
    # ------------------------------------------------------------------

    def eval_state(self, c, x, y, ours):
        """Eval(s) with the ball at (x, y). ours=False is the same function
        from the opponent's side (mirrored), negated."""
        if ours:
            return self._v_pos(c, x, y, self._nearest(c.opps, x, y))
        return -self._v_pos(c, -x, -y, self._nearest(c.ours, x, y))

    def _v_pos(self, c, ax, ay, press_d):
        W, L = self.W, c.L
        prog = (ax + L) / (2.0 * L)
        v = W["base"] + W["prog_lin"] * prog + W["prog"] * prog * prog
        gx = L - ax
        g = math.hypot(gx, ay)
        if g < W["xg_range"]:
            ang = abs(math.atan2(ay + c.gh, gx) - math.atan2(ay - c.gh, gx))
            v += (W["xg"] * math.exp(-g / W["xg_scale"])
                  * min(1.0, ang / W["xg_ang"]))
        s = min(1.0, press_d / W["space_r"])
        return v * (W["space_min"] + (1.0 - W["space_min"]) * s)

    @staticmethod
    def _nearest(players, x, y):
        return min((math.hypot(p.x - x, p.y - y) for p in players),
                   default=99.0)

    def _lost_value(self, c, pt, out):
        v = self.eval_state(c, pt[0], pt[1], False)
        return v * self.W["out_frac"] if out else v

    # ------------------------------------------------------------------
    # 6. SEARCH
    # ------------------------------------------------------------------

    def expectimax(self, c, k, depth=1):
        """EU of candidate k: P * V(we keep it) + (1-P) * V(MIN gets it)."""
        W = self.W
        kind = k.kind
        if kind in ("pass", "pass1", "clear"):
            d = math.hypot(k.tx - c.bx, k.ty - c.by)
            ux, uy = (k.tx - c.bx) / d, (k.ty - c.by) / d
            pts, out = self.ball_path(c, c.bx, c.by, ux, uy, k.v0, k.delay)
            our_t = self.our_response(c, pts, out)
            opp_t = self.opp_response(c, pts, out)
            if our_t >= INF:
                k.p = 0.0
                lost = pts[min(opp_t, len(pts)) - 1]
                k.eu = self._lost_value(c, lost, out and opp_t >= INF)
                return k.eu
            if (self._near_keeper(c, pts[:our_t])
                    or self._keeper_first(c, pts) <= min(our_t, opp_t)):
                k.p, k.eu = 0.0, self._backpass_value(c)
                return k.eu
            k.p = self.success_prob(opp_t - our_t) * W["pass_calib"]
            rx, ry = pts[min(our_t, len(pts)) - 1]
            vs = self.eval_state(c, rx, ry, True)
            if depth >= 2 and kind != "clear":
                vs = max(vs, W["disc"] * self._receiver_best(c, rx, ry))
            lost = pts[min(opp_t, len(pts)) - 1]
            k.eu = k.p * vs + (1.0 - k.p) * self._lost_value(c, lost, False)
        elif kind in ("shot1", "shot3"):
            k.p, k.eu = self._shot_value(c, c.bx, c.by, k.ty, k.v0, k.delay)
        elif kind == "dribble":
            k.p, k.eu = self._dribble_value(c, k)
        elif self._in_our_box(c, c.bx, c.by):   # hold in our box: back-pass
            k.p, k.eu = 0.0, self._backpass_value(c)
            return k.eu
        else:                                   # hold
            k.p = self.success_prob(c.opp_reach_ball - 1.5)
            here = self.eval_state(c, c.bx, c.by, True) * W["hold_decay"]
            k.eu = k.p * here + (1.0 - k.p) * self.eval_state(
                c, c.bx, c.by, False)
        if kind in SLOW and c.opp_tackle > 0.0:
            # MIN's immediate reply: an opponent this close tackles before
            # a slow action (multi-touch kick, dribble, hold) gets away
            f = W["tight_w"] * c.opp_tackle
            k.p *= 1.0 - f
            k.eu = (1.0 - f) * k.eu + f * self.eval_state(c, c.bx, c.by,
                                                          False)
        return k.eu

    def _near_keeper(self, c, pts):
        """Would the ball sit in our box within our keeper's reach? He
        catches it, and from a teammate's kick that is a back-pass."""
        g = c.our_gk
        if g is None:
            return False
        for x, y in pts:
            if (x < -c.pbox_x and abs(y) < c.pbox_w
                    and math.hypot(x - g.x, y - g.y) < self.W["gk_avoid"]):
                return True
        return False

    @staticmethod
    def _in_our_box(c, x, y):
        """Replay VH5 t=654: a 'hold' touch 6m from our keeper rolled to
        him -> back-pass goal. In our box only kick the ball away."""
        return x < -c.pbox_x and abs(y) < c.pbox_w

    def _keeper_first(self, c, pts):
        """First cycle our keeper can catch the ball on pts (inside our box
        only), INF if never - he catches our kick = back-pass."""
        g = c.our_gk
        if g is None:
            return INF
        box = [(x, y) if (x < -c.pbox_x and abs(y) < c.pbox_w) else (1e3, 1e3)
               for x, y in pts]
        return _first_t(g, box, self.W["catch_r"], True)

    def _backpass_value(self, c):
        """Their indirect free kick on our goal line."""
        return -self._v_pos(c, c.L - 5.0, 0.0, 99.0)

    def _shot_value(self, c, x, y, gy, v0, delay):
        W = self.W
        d = math.hypot(c.L - x, gy - y)
        ux, uy = (c.L - x) / d, (gy - y) / d
        pts = [(x, y)] * delay
        v, crossed = v0, False
        while len(pts) < W["tmax"] and v > 0.15:
            x += ux * v
            y += uy * v
            v *= c.decay
            pts.append((x, y))
            if x >= c.L:
                crossed = True
                break
        if not crossed:
            return 0.0, self._lost_value(c, pts[-1], False)
        # outfield blockers: strict margin (v1.2e shot into them at -2).
        # Keeper: own model (W gk_*). out=True: the ball ends in the net,
        # there is no rest point to race to (v1.3 capped P near 0.6 so)
        T = len(pts)
        field_t = gk_t = INF
        for o in c.opps:
            if o.goalie:
                gk_t = _first_t(o, pts, W["r_opp"], True, INF, c.gk_shot)
            else:
                field_t = min(field_t, _first_t(o, pts, W["r_opp"], True,
                                                field_t))
        opp_t = min(field_t, gk_t)
        p_field = 1.0 if field_t >= INF else self.success_prob(
            field_t - T, W["k_shot"], W["shot_m0"]) / W["p_max"]
        p_beat = p_field * self.success_prob(gk_t - T, W["gk_k"], W["gk_m0"])
        sigma = W["shot_noise"] * d + W["shot_noise0"]
        z = sigma * math.sqrt(2.0)
        p_on = 0.5 * (math.erf((c.gh - gy) / z) + math.erf((c.gh + gy) / z))
        p = p_beat * p_on
        after = self._lost_value(c, pts[min(opp_t, len(pts)) - 1], False)
        return p, p * W["goal"] + (1.0 - p) * after

    def _dribble_value(self, c, k):
        W = self.W
        D = math.hypot(k.tx - c.bx, k.ty - c.by)
        ux, uy = (k.tx - c.bx) / D, (k.ty - c.by) / D
        T = int(math.ceil(D / W["drib_speed"]))
        if ux * c.me.bc + uy * c.me.bs < 0.7:
            T += 1                              # turn with the ball first
        step = D / T
        pts = [(c.bx + ux * step * t, c.by + uy * step * t)
               for t in range(1, T + 1)]
        if self._in_our_box(c, c.bx, c.by) or self._near_keeper(c, pts):
            return 0.0, self._backpass_value(c)    # dribble in our box
        opp_t = self.opp_response(c, pts, True, W["r_drib"])
        p = self.success_prob(opp_t - T, m0=W["drib_m0"])
        lost = pts[min(opp_t, T) - 1]
        eu = (p * self.eval_state(c, k.tx, k.ty, True)
              + (1.0 - p) * self.eval_state(c, lost[0], lost[1], False))
        return p, eu

    def _receiver_best(self, c, rx, ry):
        """Ply 2: the receiver's best follow-up from (rx, ry) - a shot, or
        a pass on to a teammate's current position (2 cycles to control)."""
        W = self.W
        best = -INF
        if math.hypot(c.L - rx, ry) < W["shot_range"]:
            for gy in (-c.gh + 1.0, 0.0, c.gh - 1.0):
                best = max(best, self._shot_value(c, rx, ry, gy, 2.6, 2)[1])
        for m in c.onside:
            d = math.hypot(m.fx - rx, m.fy - ry)
            if d < 4.0:
                continue
            ux, uy = (m.fx - rx) / d, (m.fy - ry) / d
            v0 = min(c.vmax, W["pass_end_speed"] + (1.0 - c.decay) * d)
            pts, out = self.ball_path(c, rx, ry, ux, uy, v0, 2)
            opp_t = self.opp_response(c, pts, out)
            our_t = _first_t(m, pts, W["r_our"], out)
            if our_t >= INF:
                continue
            p = self.success_prob(opp_t - our_t) * W["pass_calib"]
            px, py = pts[min(our_t, len(pts)) - 1]
            lx, ly = pts[min(opp_t, len(pts)) - 1]
            best = max(best, p * self.eval_state(c, px, py, True)
                       + (1.0 - p) * self.eval_state(c, lx, ly, False))
        return best

    def _upper_bound(self, c, k):
        """Optimistic EU at depth 1, for pruning (alpha-style cutoff)."""
        if k.kind in ("shot1", "shot3"):
            return self.W["goal"]
        if k.kind in ("pass", "pass1", "dribble"):
            return self._v_pos(c, k.tx, k.ty, 99.0) + 0.02
        return INF                              # hold/clear: always evaluate

    def search(self, c, cands, deadline):
        """Anytime: ply 1 for everything in best-first order (pruning what
        cannot beat the incumbent), then ply 2 on the top `beam` passes."""
        for k in cands:
            k.ub = self._upper_bound(c, k)
        order = sorted(cands, key=lambda k: (k.ub < INF, -k.ub))
        done, best = [], -INF
        for k in order:
            if k.ub < INF and time.perf_counter() > deadline and done:
                break
            if k.ub + k.bonus <= best:
                continue
            self.expectimax(c, k, 1)
            done.append(k)
            best = max(best, k.eu + k.bonus)
        deep = 0
        top = sorted(done, key=lambda k: -(k.eu + k.bonus))[:self.W["beam"]]
        for k in top:
            if time.perf_counter() > deadline:
                break
            if k.kind in ("pass", "pass1"):
                self.expectimax(c, k, 2)
                deep += 1
        done.sort(key=lambda k: (-(k.eu + k.bonus), k.kind, k.tx, k.ty))
        return done, deep

    def emit(self, agent, ranked):
        """Best first, then the best action that does not go through
        Action.kick (runs if the kick shields instead of kicking), then a
        clearance that cannot fail."""
        best = ranked[0]
        self._do(agent, best)
        if best.kind in KICKS:
            alt = next((k for k in ranked[1:] if k.kind not in KICKS), None)
            if alt is not None:
                self._do(agent, alt)
        Action.clear(agent)

    def _do(self, agent, k):
        target = Vector2D(k.tx, k.ty)
        if k.kind == "pass":
            Action.kick(agent, target, k.arrive, self.W["accept_late"])
        elif k.kind == "shot3":
            Action.kick(agent, target, 1, self.W["accept_late"])
        elif k.kind in ("pass1", "shot1"):
            Action.kick_one_step(agent, target)
        elif k.kind == "dribble":
            Action.dribble(agent, target)
        elif k.kind == "hold":
            Action.hold(agent)
        else:
            Action.clear(agent)

    def _apply_memory(self, c, cands):
        """Commitment to last cycle's multi-touch kick; drop blacklisted."""
        self._black = {key: t for key, t in self._black.items()
                       if t > c.cycle}
        keep = []
        prev = self._plan
        for k in cands:
            if (k.kind, round(k.tx), round(k.ty)) in self._black:
                continue
            if (prev and prev[0] == c.cycle - 1 and prev[1] == k.kind
                    and math.hypot(prev[2] - k.tx, prev[3] - k.ty) < 1.0):
                k.bonus = self.W["commit"]
            keep.append(k)
        cands[:] = keep

    def _remember(self, c, best):
        prev = self._plan
        n = 1
        if (prev and prev[0] == c.cycle - 1 and prev[1] == best.kind
                and math.hypot(prev[2] - best.tx, prev[3] - best.ty) < 1.0):
            n = prev[4] + 1
        if best.kind in KICKS and n >= self.W["max_repeat"]:
            self._black[(best.kind, round(best.tx), round(best.ty))] = (
                c.cycle + 10)
            n = 0
        if best.kind in KICKS:                 # smart kick, ball still here?
            chained = prev and prev[0] == c.cycle - 1 and prev[1] in KICKS
            self._stuck = self._stuck + 1 if chained else 1
        else:
            self._stuck = 0
        self._plan = (c.cycle, best.kind, best.tx, best.ty, n)

    def _allow_ms(self, agent, c, on_ball):
        W = self.W
        b = agent.budget
        cap = W["on_ms"] if on_ball else W["off_ms"]
        rem = b.remaining_ms
        if rem != float("inf"):
            left = max(60.0, 1.15 * (1500 - min(c.cycle, 1490)))
            cap = min(cap, rem / left * (W["on_mult"] if on_ball else 1.0))
        cap = min(cap, b.decision_remaining_ms - W["wall_margin"])
        return max(1.0, cap)

    # ------------------------------------------------------------------
    # 7. OFF BALL: ROLES (CSP) AND SPOTS
    # ------------------------------------------------------------------

    def assign_roles(self, c):
        """Same inputs in every process -> same answer. -> (phase,
        {unum: (role, spot)}, q) where q is where the ball will be won."""
        W = self.W
        ours = c.ours
        if c.kick_mate:
            carrier = min(ours, key=lambda p: (
                math.hypot(p.x - c.bx, p.y - c.by), p.unum))
            q = (c.bx, c.by)
            role = "intercept" if carrier is c.me else "carry"
            roles = {carrier.unum: (role, q)}
            rest = [p for p in ours if p is not carrier]
            roles.update(self._assign(rest, self._attack_spots(c, q)))
            return "attack", roles, q

        speed = math.hypot(c.bvx, c.bvy)
        if speed > 0.05:
            pts, out = self.ball_path(c, c.bx, c.by, c.bvx / speed,
                                      c.bvy / speed, speed)
        else:
            pts, out = [(c.bx, c.by)], False
        reach = {p.unum: _first_t(p, pts, W["r_our"], out) for p in ours}
        chaser = min(ours, key=lambda p: (reach[p.unum], p.unum))
        our_t = reach[chaser.unum]
        opp_t = 0 if c.kick_opp else self.opp_response(c, pts, out)

        if our_t < opp_t:
            q = pts[min(our_t, len(pts)) - 1]
            roles = {chaser.unum: ("intercept", q)}
            rest = [p for p in ours if p is not chaser]
            roles.update(self._assign(rest, self._attack_spots(c, q)))
            return "attack", roles, q

        q = (c.bx, c.by) if opp_t == 0 else pts[min(opp_t, len(pts)) - 1]
        if our_t < INF and our_t <= opp_t + W["contest"]:
            roles = {chaser.unum: ("intercept", q)}
            rest = [p for p in ours if p is not chaser]
            roles.update(self._assign(rest, self._defend_spots(c, q, rest)[1:]))
        else:
            roles = self._assign(ours, self._defend_spots(c, q, ours))
        return "defend", roles, q

    def _assign(self, players, spots):
        """Exhaustive search over the <= 4! ways to fill the roles. A spot
        is a point, or {unum: (point, steps)} when it depends on who goes."""
        if not players:
            return {}

        def where(p, s):
            if isinstance(s, dict):
                return s[p.unum]
            return s, reach_steps(p, s[0], s[1])

        cost = []
        for p in players:
            row = []
            for _r, s, w in spots:
                (sx, sy), steps = where(p, s)
                row.append(w * (steps + 0.01 * math.hypot(p.x - sx, p.y - sy)))
            cost.append(row)
        n = min(len(players), len(spots))
        best, best_cost = None, float("inf")
        for perm in permutations(range(len(spots)), n):
            total = sum(cost[i][perm[i]] for i in range(n))
            if total < best_cost - 1e-9:
                best, best_cost = perm, total
        return {players[i].unum: (spots[best[i]][0],
                                  where(players[i], spots[best[i]][1])[0])
                for i in range(n)}

    def _attack_spots(self, c, q):
        W = self.W
        qx, qy = q
        side = -1.0 if qy > 0 else 1.0
        if qx > 0:
            # their half: like FULL's (11-13m behind the ball, central),
            # the support man trails instead of standing level with the
            # ball among their defenders - a safe outlet, already goal-side
            wide = self._clip(c, qx - W["trail_dx"], qy + side * W["trail_dy"])
        else:
            wide = self._clip(c, qx + W["wide_dx"], qy + side * W["wide_dy"])
        return [("fwd", self._clip(c, qx + W["fwd_dx"], qy * 0.4), 1.0),
                ("wide", wide, 1.0),
                ("back", self._clip(c, min(qx - W["back_dx"], W["back_max_x"]),
                                    qy * 0.3), 1.0)] # rest defence

    def _threat_path(self, c, q):
        """MIN's most dangerous continuation: carry the ball straight at
        our goal at threat_speed, until shooting range."""
        W = self.W
        ux, uy = self._unit(-c.L - q[0], -q[1])
        x, y = q
        pts = []
        while len(pts) < 30 and math.hypot(x + c.L, y) > W["threat_stop"]:
            x += ux * W["threat_speed"]
            y += uy * W["threat_speed"]
            pts.append((x, y))
        return pts or [q]

    def _defend_spots(self, c, q, players):
        """press: for each player, the first point of the threat path he
        can reach press_lead cycles BEFORE the carrier, so he arrives set
        and goal-side instead of running alongside. Then 2 marks, a cover.
        Everywhere, also near our goal: v1.3's tight press there (1m
        goal-side of the ball inside 25m) let FULL shoot ~2.4 times a match
        against ~1.4 with this (v1.5 ablation, CONTEXT.md section 7)."""
        W = self.W
        path = self._threat_path(c, q)
        lead = W["press_lead"]
        press = {}
        for p in players:
            t = _first_t(p, path[lead:], 0.8, False)
            if t >= INF:                       # carrier already at range
                pt = path[-1]
                t = reach_steps(p, pt[0], pt[1])
            else:
                pt = path[min(t - 1 + lead, len(path) - 1)]
            press[p.unum] = (pt, min(t, 60))
        spots = [("press", press, W["w_press"])]
        danger = sorted(
            (o for o in c.opps if not o.goalie
             and math.hypot(o.x - q[0], o.y - q[1]) > W["mark_skip_r"]),
            key=lambda o: (o.x + 0.3 * abs(o.y), o.unum))[:2]
        for o in danger:
            spots.append(("mark", self.defend_spot(c, "mark", o, q),
                          W["w_mark"]))
        cover = self.defend_spot(c, "cover", None, q)
        spots.append(("cover", cover, W["w_cover"]))
        while len(spots) < 4:
            side = -1.0 if q[1] > 0 else 1.0
            spots.append(("cover", (cover[0], cover[1] + side * 8.0),
                          W["w_cover"]))
        return spots

    def defend_spot(self, c, role, o, q):
        W = self.W
        gx, gy = -c.L, 0.0
        if role == "mark":
            ax, ay = self._unit(gx - o.fx, gy - o.fy)
            bx, by = self._unit(q[0] - o.fx, q[1] - o.fy)
            dx, dy = self._unit(0.65 * ax + 0.35 * bx, 0.65 * ay + 0.35 * by)
            return (o.fx + dx * W["mark_gap"], o.fy + dy * W["mark_gap"])
        if role == "cover":
            x = q[0] + (gx - q[0]) * W["cover_frac"]
            y = q[1] + (gy - q[1]) * W["cover_frac"]
            d = math.hypot(x - gx, y - gy)
            if d < W["cover_min"]:             # don't stand on the keeper
                ux, uy = self._unit(q[0] - gx, q[1] - gy)
                x, y = gx + ux * W["cover_min"], gy + uy * W["cover_min"]
            return (max(-c.L + 4.0, x), y)
        ux, uy = self._unit(gx - q[0], gy - q[1])
        return (q[0] + ux * W["press_gap"], q[1] + uy * W["press_gap"])

    def support_spot(self, c, anchor, q):
        """Sample round the role's anchor; score each spot by the EU of the
        pass the carrier could play to it, minus crowding and travel."""
        W = self.W
        ax, ay = anchor
        pts = [anchor]
        for r, start in self.SUPPORT_RINGS:
            pts += [(v.x(), v.y()) for v in Tools.points_around(
                Vector2D(ax, ay), r, 8, start)]
        best, best_s = anchor, -INF
        for sx, sy in pts:
            sx, sy = self._clip(c, sx, sy)
            d = math.hypot(sx - q[0], sy - q[1])
            if d < 3.0:
                continue
            ux, uy = (sx - q[0]) / d, (sy - q[1]) / d
            v0 = min(c.vmax, W["pass_end_speed"] + (1.0 - c.decay) * d)
            n = self._arrive_in(c, d, v0)
            path, out = self.ball_path(c, q[0], q[1], ux, uy, v0, 1, n)
            opp_t = self.opp_response(c, path, out)
            p = self.success_prob(opp_t - len(path)) * W["pass_calib"]
            lx, ly = path[min(opp_t, len(path)) - 1]
            s = (p * self.eval_state(c, sx, sy, True)
                 + (1.0 - p) * self.eval_state(c, lx, ly, False))
            for m in c.mates:
                dm = math.hypot(m.x - sx, m.y - sy)
                if dm < W["crowd_r"]:
                    s -= W["crowd"] * (1.0 - dm / W["crowd_r"])
            s -= W["travel"] * reach_steps(c.me, sx, sy) / 10.0
            if self._spot and math.hypot(sx - self._spot[0],
                                         sy - self._spot[1]) < 2.0:
                s += W["spot_keep"]
            if s > best_s:
                best, best_s = (sx, sy), s
        self._spot = best
        return best

    def should_tackle(self, c, agent):
        """Tackle direction (deg, body-relative, front/sideways only) or
        None. Never foul=True, never with a teammate on the ball.

        Two cases, both decided by expectimax against NOT tackling:
          loose ball (nobody kickable, e.g. a dribbler just pushed it on)
              and they win the race to it -> clean tackle, no foul risk.
          they control it -> called a foul ~4 times in 5 (measured), so
              only as a last resort inside emerg_r of our goal, where not
              tackling means they shoot as if unopposed.
        Outcomes: p = tackle_probability we reach the ball; then foul (their
        free kick, nobody near) or the ball flies at power*(1-|dir|/180)
        and we race for it; 1-p = they keep it and I am frozen 10 cycles.
        """
        W = self.W
        if c.kick_mate:
            return None
        p = agent.wm.self.tackle_probability
        if p < W["tackle_p_min"]:
            return None
        others = c.onside
        free_kick = -self._v_pos(c, -c.bx, -c.by, 99.0)
        if c.kick_opp:
            if (math.hypot(c.bx + c.L, c.by) > W["emerg_r"]
                    or p < W["emerg_p"]):
                return None
            foul = W["foul_risk"]
            keep = frozen = free_kick          # they shoot regardless
        else:
            it = agent.wm.intercept_table
            if (min(it.self_reach_steps, it.first_teammate_reach_steps)
                    < it.first_opponent_reach_steps):
                return None                    # loose and ours: intercept
            foul = 0.0
            keep = self.eval_state(c, c.bx, c.by, False)
            frozen = -self._v_pos(c, -c.bx, -c.by,
                                  self._nearest(others, c.bx, c.by))
        best, best_eu = None, keep + W["tackle_margin"]
        for d in (-90, -60, -30, 0, 30, 60, 90):
            a = math.radians(c.body + d)
            acc = (1.0 - abs(d) / 180.0) * W["tackle_accel"]
            vx = c.bvx + acc * math.cos(a)     # adds to the ball's velocity
            vy = c.bvy + acc * math.sin(a)
            v0 = min(c.vmax, math.hypot(vx, vy))
            if v0 < 1e-6:
                continue
            pts, out = self.ball_path(c, c.bx, c.by, vx / math.hypot(vx, vy),
                                      vy / math.hypot(vx, vy), v0)
            our_t = min((_first_t(m, pts, W["r_our"], out) for m in others),
                        default=INF)
            opp_t = self.opp_response(c, pts, out)
            if (self._near_keeper(c, pts[:min(our_t, opp_t)])
                    or self._keeper_first(c, pts) <= min(our_t, opp_t)):
                continue                       # tackled to our keeper
            q = self.success_prob(opp_t - our_t) if our_t < INF else 0.0
            rx, ry = pts[min(our_t, len(pts)) - 1]
            lx, ly = pts[min(opp_t, len(pts)) - 1]
            won = (q * self.eval_state(c, rx, ry, True)
                   + (1.0 - q) * self._lost_value(c, (lx, ly), out
                                                  and opp_t >= INF))
            eu = (p * ((1.0 - foul) * won + foul * free_kick)
                  + (1.0 - p) * frozen)
            if eu > best_eu:
                best, best_eu = float(d), eu
        return best

    # ------------------------------------------------------------------
    # 8. SMALL HELPERS
    # ------------------------------------------------------------------

    def _clip(self, c, x, y):
        x = max(-c.L + 4.0, min(c.L - 4.0, x))
        if x > 0 and x > c.offside_x - 1.0:
            x = max(0.0, c.offside_x - 1.0)
        return (x, max(-c.Wd + 3.0, min(c.Wd - 3.0, y)))

    @staticmethod
    def _unit(x, y):
        r = math.hypot(x, y)
        return (x / r, y / r) if r > 1e-9 else (1.0, 0.0)

    def _dash(self, c, role, dist, urgent):
        """Sprint only when it matters. A forward dash costs its power in
        stamina and ~45/cycle comes back, so 'trot' is free. Below
        stam_low we trot unless urgent - librcsc refuses to dash below
        ~2446 and a player stuck there crawls for the rest of the half."""
        W = self.W
        if urgent:
            power = 100.0
        elif dist < 2.0:
            power = 40.0
        elif role in ("mark", "cover"):
            power = 80.0
        else:
            power = 100.0 if dist > 8.0 else 70.0
        if c.stamina < W["stam_low"]:
            power = min(power, 70.0 if urgent else W["trot"])
        elif c.stamina < W["stam_mid"]:
            power = min(power, 90.0 if urgent else 60.0)
        # hard floor, urgent or not: urgent runs at 70 below stam_low still
        # parked players on the 2446 floor (12f m3: #3 at 2446 t=690-740)
        if c.stamina < W["stam_floor"]:
            power = min(power, 42.0)
        elif c.stamina < W["stam_guard"]:
            power = min(power, 60.0 if urgent else 45.0)
        return power


class Agent2(StarterAgent):
    def on_ball(self, agent) -> None:
        return None

    def off_ball(self, agent) -> None:
        return None

# STARTER CODE ENDS HERE #
