# CONTEXT.md — COL333 Assignment 3 (Football AI Agent)
> Ultra-dense reference for coding `Agent1` in `src/student/agent.py`. Zero-hallucination signatures & rules.

---

## 1. Environment, Rules & Hard Constraints
- **Submission**: Only `src/student/agent.py` is evaluated (`Agent1` class). Python 3 standard library + `numpy` + `pyrusgeom` only. **`scipy` is strictly FORBIDDEN**.
- **Process Isolation**: Each player runs in a separate process. No IPC, no network, no disk sharing, no `say`/`attentionto`. All coordination is computed from shared full-state perception (`agent.wm`).
- **Time Budgets**: 1500 cycles/match. CPU budget = 75.0s per PLAYER process per match (team counted as max across players). Only PlayOn cycles call us (~720–800 decisions/player measured) → ~90ms avg available; target ≤40ms avg for safety margin on slower grader CPUs. Starter uses ~0.03ms. Hard wall-clock limit = 1.0s/decision (5 violations = player sent off; >1.5s = match forfeit).
- **Pitch & Coordinates**: Pitch is `[-52.5, 52.5] x [-34.0, 34.0]`. Always attacking towards `+x` (opponent goal at `(52.5, 0)`), our goal at `(-52.5, 0)`. Angle `0°` = ahead (`+x`), `90°` = right (`+y`), `-90°` = left (`-y`), `180°` = behind (`-x`).
- **Simulator Quirks**:
  - `Action.tackle`: Power is `1.0` straight ahead (0°), `0.5` sideways (±90°), `0.0` backward (±180°). `tackle_back_dist` is 0. Tackler is frozen `tackle_cycles=10` after ANY tackle (hit or miss).
  - **Fouls without `foul=True` (measured, v1 vs FULL)**: tackling an opponent who has the ball under control (kickable, did not kick that cycle) was called `foul_charge` 4 of 5 times → their free kick (no yellow). Tackles at the moment they kicked: 0 of 5 fouled. So `should_tackle` prices `foul_risk=0.7`.
  - Stamina: librcsc refuses to dash below ~2446 (recover_dec_thr), and a player stuck there crawls. v1.1 spent ~4% of player-cycles there; v1.2 urgency-based dash: <1%.
  - **Back-pass traps**: our keeper catching ANY ball last touched by us (dribble next to him, a pass, or a TACKLE deflecting their shot) = indirect FK on our goal line. v1.2 values such paths as a back-pass (`_near_keeper` radius + `_keeper_first` reach race).
  - Tackle physics: tackle accel ADDS to the ball's current velocity (a tackled shot keeps flying at our goal).
  - Smart kick (`Action.kick`) under tight pressure (opponent < ~1.6m) often cannot find a safe sequence and just nudges the ball; 12 of 14 lost dribbles also had an opponent < 1.6m. v1.2 models this as MIN's immediate reply (`tight_w`, `SLOW` kinds) + `stuck_max` escalation to one-touch kicks.
  - `Action.kick`: Python wrapper returns `None` ALWAYS (no success flag; failure is decided later inside the proxy). If no ≤3-touch sequence meets `accept_late`, proxy registers a shield. **Sources conflict on what happens next**: `interface.py` says a fallback behind it never runs; Piazza (TA: "intended") says shield is registered but reports false, so the proxy runs the NEXT emitted action. Design so both are safe: pre-filter infeasible kicks, and emit the 2nd-best action after `kick` anyway.
  - Goalie: Controlled automatically. Backward dash clamped to 0 under `rcssserver 19.0.0`; easily stranded if pulled out. Back-pass to goalie concedes indirect free kick.
  - Offside: Evaluated only in opponent half (`target.x() > 0` and `target.x() > wm.offside_line_x - 0.5`).
  - Tie-breakers: Goal Difference -> Goals Scored -> Fewest Yellows (Red = 2.5 Yellows) -> Fewest Fouls.
- **Permitted Algorithms (COL333 L01-L12)**: Minimax, $\alpha$-$\beta$ pruning (iterative deepening, move ordering, transposition tables), Heuristic linear evaluation $Eval(s) = \sum w_i f_i(s)$, Quiescence search (for contested ball/tackle states), Expectimax (stochastic intercepts), MCTS/UCT, Beam search, CSP role assignment. **Deep RL, Neural Nets, Genetic Algos are FORBIDDEN.**

---

## 2. World Model API (`agent.wm`)
> **CRITICAL**: In `pyrusgeom.geom_2d.Vector2D`, `.x()` and `.y()` are **METHODS**, NOT properties!
- `wm.ball`: `.position`, `.velocity` (`Vector2D`), `.dist_from_self`, `.angle_from_self` (`float`). (seen_/heard_/*_count fields exist but are meaningless under fullstate.)
- `wm.self`: `.position`, `.velocity` (`Vector2D`), `.body_direction` (**`float` degrees**, wrap with `AngleDeg(...)` for geometry), `.stamina` (`[0, 8000]`), `.stamina_capacity`, `.effort`, `.recovery`, `.is_kickable`, `.kick_rate` (feed to `Tools.calc_max_velocity`), `.uniform_number`, `.tackle_probability`, `.foul_probability`, `.dist_from_ball`, `.angle_from_ball`, `.ball_reach_steps`, `.is_tackling`, `.card`, `.type_id`, `.get_safety_dash_power`.
- `wm.teammates` / `wm.opponents`: `list[Player]` (teammates exclude self; include goalie → filter `is_goalie`; filter `uniform_number > 0`).
  - `Player`: `.uniform_number`, `.id` (proxy id, ≠ unum), `.position`, `.velocity`, `.body_direction` (float), `.dist_from_self`, `.angle_from_self`, `.dist_from_ball`, `.angle_from_ball`, `.is_goalie`, `.ball_reach_steps`, `.is_kicking`, `.is_tackling`, `.type_id`, `.inertia_final_point` (`Vector2D`, where it coasts to if it stops dashing). **No stamina for other players.**
- `wm.intercept_table` (precomputed by proxy each cycle): `.self_reach_steps`, `.first_teammate_reach_steps`, `.second_teammate_reach_steps`, `.first_opponent_reach_steps`, `.second_opponent_reach_steps` (`int`); `.first_teammate_id` / `.second_teammate_id` / `.first_opponent_id` / `.second_opponent_id` (proxy `id`, match against `Player.id`, 0 = none); `.self_intercept_info`: `list[InterceptInfo]` with `.turn_steps .turn_angle .dash_steps .dash_power .dash_dir .final_self_position .final_ball_dist .final_stamina .value .action_type`.
- Other `wm`: `.cycle`, `.game_mode_type` (int), `.our_team_score`/`.their_team_score`, `.last_kicker_uniform_number`, `.last_kick_side`, `.kickable_teammate_id`/`.kickable_opponent_id`, `.our_defense_line_x`/`.their_defense_line_x` (incl. ball), `.our_defense_player_line_x`/`.their_defense_player_line_x` (players only).
- **Map fields are broken by the wrapper**: `wm.our_players_dict`, `wm.their_players_dict`, `wm.helios_home_positions` arrive as a plain list of KEYS only. Don't use them.
- `wm.offside_line_x`: `float` (opponent's second-to-last defender x).
- `wm.kickable_teammate_existance` / `wm.kickable_opponent_existance`: `bool`.
- `agent.server_params`: `.pitch_half_length` (52.5), `.pitch_half_width` (34.0), `.goal_width` (14.02), `.ball_decay` (0.94), `.ball_speed_max` (3.0), `.stamina_max` (8000.0).
- `agent.budget`: `.remaining_ms` (match CPU ms left), `.decision_remaining_ms` (decision wall ms left, <=1000). Always guard searches: `while budget.remaining_ms > 400 and budget.decision_remaining_ms > 50: deepen()`.

---

## 3. Action API (`from src.student.interface import Action, Tools, note`)
> Only first emitted body action per cycle executes; always end with an infallible fallback (`hold`/`clear` on ball, `go_to_point` off ball).

### On-Ball Actions:
- `Action.kick(agent, target: Vector2D, arrive_in: int, accept_late: int = 3)`: Smart multi-touch kick (1-3 cycles).
- `Action.kick_one_step(agent, target: Vector2D)`: Maximum pace shot in 1 cycle. Infallible. Best for shooting.
- `Action.dribble(agent, target: Vector2D)`: Advances keeping ball at feet, dodges opponents.
- `Action.hold(agent)`: Shields ball against close defenders.
- `Action.clear(agent)`: Powerful clearance toward opponent touchline. Infallible last line of `on_ball`.
- `Action.advance_ball(agent)`: Puts ball 30m up clearest forward lane.
- `Action.stop_ball(agent)`: Traps fast ball to dead stop.

### Off-Ball Actions:
- `Action.go_to_point(agent, target: Vector2D, max_dash_power=100.0, distance_threshold=None, dodge=False)`: Navigates to target point.
- `Action.intercept(agent)`: Moves to intercept predicted ball trajectory in minimum cycles.
- `Action.tackle(agent, direction: float = 0.0, foul: bool = False)`: Direction is relative to body (0=front, ±90=side).

### Angle & Body Actions:
- `Action.turn_to_point(agent, target: Vector2D)`, `Action.turn_to_angle(agent, deg: float)`, `Action.turn_to_ball(agent)`.

### Helpers (`Tools`):
- `Tools.home_position(agent) -> Vector2D`: Target formation position for this cycle.
- `Tools.points_around(center: Vector2D, radius: float, n: int, start_deg: float = 0.0) -> list[Vector2D]`.
- `Tools.nearest_to(players: list[Player], point: Vector2D) -> Player`: Closest player from any list.
- `Tools.get_opponent_nearest_to(agent, point: Vector2D) -> Player`.
- `Tools.get_opponent_nearest_to_self(agent) -> Player`.
- `Tools.get_opponent_goalie(agent) -> Player`.
- `Tools.exist_opponent_in(agent, region: Sector2D) -> bool`: Checks passing/dribbling corridor.
- `Tools.get_teammates_from_ball(agent) -> list[Player]`, `Tools.get_opponents_from_ball(agent) -> list[Player]`.
- `Tools.first_ball_speed(dist, steps, decay) -> float`, `Tools.ball_move_step(speed, dist, decay) -> int`.
- `Tools.calc_max_velocity(AngleDeg(dir), wm.self.kick_rate, wm.ball.velocity, agent.server_params) -> Vector2D`: max ball velocity reachable in ONE kick toward `dir` (`.r()` = speed). Use to pre-check kick feasibility.
- `Tools.predict_opponent_reach_step(agent, opp, first_ball_pos, first_ball_vel, AngleDeg(move_angle), receive_point, max_cycle, description)` → `(cycles, point)`. Real signature has 8 args; interface.py docstring shows only 5. Pure Python, relatively slow: call per candidate × nearby opponents only.
- `Sector2D(origin: Vector2D, min_r, max_r, start_angle_deg, end_angle_deg)`.
- `note(agent, label: str, **kwargs)`: Traces decision for `a3.py why` analysis.

---

## 4. CLI Commands (`a3.py`)
```bash
python3 a3.py doctor                                        # Verify environment setup
python3 a3.py match MINE FULL --right full                  # vs reference bot (positional args = team NAMES only)
python3 a3.py match MINE AGENT2 --right :Agent2 -t 20       # vs passive opponent, short match
python3 a3.py match A B --right path/to/old_agent.py:Agent1 # vs a frozen older version (self-play / regression)
python3 a3.py match A B --no-trace -p 6100                  # second match in parallel needs a different port
python3 a3.py why                                           # label breakdown for latest traced match
python3 a3.py why -t MINE --match SUBSTR --list             # pick team / match; list traced matches
python3 a3.py why 200 260                                   # dump cycles 200..260
python3 a3.py why -g pass | --slow 30 | --chase | --stack LABEL | --possession   # (-n/--limit N rows, default 20)
python3 a3.py validate logs/<stamp>.rcg --json              # hidden: rcg sanity / stats
python3 a3.py watch [--follow]                              # browser replays (127.0.0.1:8080)
```
- Spec: `--left/--right` = `full` | `path/agent.py[:Class]` | `:Class` (default `src/student/agent.py:Agent1`).
- `-t/--half N` = half length in SERVER SECONDS (×10 cycles), default 75 → 750 cycles/half. `-n` team size (default 5 from base.conf).
- `-o K=V` overrides any server/a3 conf key (e.g. `-o server::half_time=30`). `--policy off|warn|strip|raise`, `--no-sandbox`, `--stamp NAME`, `--dry-run`.
- Matches are always headless and `synch_mode=true` (runs as fast as agents answer); there is no separate "fast" flag. Viewing is offline via `watch`.
- Telemetry: per-player CPU/wall per decision → `runlogs/timing/<stamp>/<TEAM>_<unum>.json` (`cpu_ms`, `wall_ms`, `spent_ms`, `killed`); trace rows → `runlogs/trace/<stamp>/<TEAM>/<unum>.jsonl` (`c, pos, ball, reach[self,mate,opp], nearest_opp, actions, ms, left_ms, notes`); score → `runlogs/<stamp>_server.log`. `why` prints nothing useful unless the agent calls `note()`.

---

## 5. `Agent1` Architecture (v1.6 = v1.3 + shot model fixes + trailing support + threat-path press everywhere + stamina floor guard; frozen copies in `src/student/` (gitignored): `agent_v16.py` = v1.6 (promoted), `agent_i1/i2/i3/i31/i3s/i3sc.py` = 2026-10-29 v1.6 ablation steps, `agent_v15.py` = someone's v1.5 (not promoted, -1.64 over 11), `agent_v1.py` = v1.1, `agent_v12.py` = v1.2, `agent_v12b/d/e/f.py` = variants, `agent_v13.py` = v1.3, `agent_v14.py` = v1.4 (promoted), `agent_tA/tB/tC/tD1/tD2.py` = 2026-10-29 ablation steps, `agent_v14c.py` = v1.4c trial (not promoted), `agent_exp14.py` = its A/B subclasses `OffOnly/DefOnly/Brake/Tackle/Cone/Strip/BrakeCone`)
- `on_ball`: `snapshot` → `gen_shots/gen_passes/gen_dribbles/gen_safe` → `search` (ply-1 `expectimax` best-first with upper-bound pruning, then ply-2 `_receiver_best` on top `beam` passes, deadline-checked) → `emit` ([best, best non-`Action.kick` alt, clear]) → `_remember` (commit bonus / blacklist after `max_repeat`).
- `expectimax`: EU = P·Eval(ours at receive pt) + (1−P)·Eval(theirs at loss pt); P = `p_max·sigmoid(k·(opp_t − our_t − m0))`; reach times from `reach_steps`/`_first_t` (dash table + turn penalty; their keeper gets catch radius + back-dash penalty).
- `eval_state`: `_v_pos` (progress² + xG-like term × space factor), mirrored & negated for opponent possession. Units = goals.
- `off_ball`: `should_tackle` (EU vs not tackling, incl. foul/frozen) → `assign_roles` (identical in all processes; 4!/3! permutation search over attack anchors fwd/wide/back or defend press/mark/mark/cover) → `support_spot` (sample 17 pts, score by pass EU) / `defend_spot`.
- All tunables in class dict `Agent1.W`. Notes: `on:<kind>` (to, t, eu, p, n, d2, ms), `off:<role>` (ph, s).
- v1.2/v1.3 additions: pass_calib 0.9; MIN immediate reply (`tight_w`, `SLOW`) + `stuck_max`; onside-only receivers; back-pass guards (`_near_keeper`, `_keeper_first`, `_in_our_box`: no hold/dribble in our box); tackle = loose-ball race or last resort <20m (`foul_risk`); threat-path press, tight press `close_gap` within `close_r`=25m; rest defence (`back_max_x`), recovery-run urgency; stamina tiers `stam_low/mid`; no space passes from own third (`space_min_x`).
- agent.py has NO experiment classes (AgentBus/AgentMix removed 2026-10-28). Put trials in a gitignored `src/student/agent_*.py` and run `--left src/student/agent_x.py:Class`.

## 6. Telemetry: `python3 scripts/match_report.py [rcg...] [--team T] [--tag v] [--json] [--no-history]`
- Default = latest `logs/*.rcg`. Touches are exact (rcg kick/tackle/catch counters + KICK/TACKLE_FAULT flags). Trace decision at cycle `c` ↔ rcg touch at `c+1`. Right-side teams are flipped to our frame.
- Prints: score, possession %, passes ok/att, turnovers (intercepted / dispossessed / out / offside) + by zone, shots (on target), tackles won/failed, fouls/cards, territory, per-player table, CPU (avg/p95/max/wall/total), **planned note → actual outcome** matrix, **pass P calibration** (predicted vs actual), double-chase count, **goal stories** (who lost it where, planned action, cycles/touches to goal, restart incl. `foul->free_kick`).
- Appends one row per match to `runlogs/history.csv` (compare versions by `--tag`).

- `python3 scripts/batch.py --tag T --name N -n 8 -j 4 [--left spec] [--right spec] [--port P]`: N matches in parallel (own ports), each fed to match_report with `--tag`, prints W/D/L + goals. Two batches at once need different `--port` bases (6000 / 7000).
- **Startup race**: `a3.py` waits only 30s for the brains. 4+ matches launched in the same second (batch rounds, or two batches at once) often miss it → server killed at 0 cycles, recorded as a 0-0 "result" (batch.py doesn't notice). Check `grep -c '^(show' rcg` > 1000, or stagger launches ~8s apart.

## 6b. `current_results/` = the promoted model ONLY
- After a version replaces Agent1: `python3 scripts/batch.py --tag vX.Y ...` then `python3 scripts/publish_current.py --tag vX.Y`, and hand-edit `current_results/STRATEGY.md`. Never publish trial/experiment runs there (they go only in §7).

## 7. Experiment log vs FULL (pooled from runlogs/history.csv; GD/match, SE ~0.3-0.4 at n=8 → only differences > ~0.8 are real)
| version | n | GD/m | W-D-L | note |
|---|---|---|---|---|
| starter | 1 | -3.0 | 0-0-1 | |
| v1.1 | 3 | -2.3 | 0-0-3 | fouls from tackles, stamina floor |
| v1.2b | 11 | -1.45 | 0-2-9 | + tight-pressure, stuck, keeper radius |
| v1.2c | 8 | -2.1 | 0-1-7 | REVERTED: press 2 cycles ahead / never chase controlled ball → stood off, 21% of time in our box |
| v1.2d | 16 | -1.13 | 2-4-10 | + tackle physics fix |
| v1.2e | 8 | -1.6 | 0-1-7 | REVERTED: shot_m0=-2 (calibrated on SELECTED shots → shot from bad spots); block role (player was 11-18m from spot) |
| v1.2f | 20 | -0.95 | 1-9-10 | + rest defence (back ≤ x=-5), recovery runs |
| v1.2g = v1.2 | 8 | -0.9 | 0-3-5 | + xg 0.9 / scale 12: shots 1.1/m vs 0.5 |
| exp AgentBus (9m / 16m) | 3 / 4 | -8 / -4 | 0-0-7 | REJECTED: FULL shoots from outside the wall (13 shots/match at 9m); clears give it back |
| exp AgentSwarm | 8 | -2.1 | 0-1-7 | REJECTED: safe passes but ball in their half 12%, 0.1 shots/match |
| exp static bus (wall 5m, fixed) | 8 | -5.1 | 0-0-8 | REJECTED: FULL gets the box (ball in our box 33%), 13 shots/match |
| exp mix: bus defend + tight box attack | 8 | -3.25 | 0-2-6 | REJECTED: box keeps the ball (38/45 passes) but their half 8%, 0 shots; nobody back on loss. Two 0-0s (MIX0, MIX1) |
| **v1.3** | 8 | -0.9 | 1-3-4 | + no hold/dribble in own box (back-passes 2→0), close press <25m, no space passes from own third |
| v1.3-control (same day) | 8 | -1.25 | 1-1-6 | rerun of agent_v13.py; v1.3 pooled n=16: -1.06 (9-26) |
| v1.4a | 8 | -2.38 | 0-0-8 | REJECTED (all v1.4 ideas): keeper fitted on the wrong keeper (p 0.35-0.5 at 22-27m → FULL's keeper caught 9/11 shots); ply-2 keep-race + drib_m0 -0.7 → ~400 holds/8 matches |
| v1.4-defonly | 8 | -3.0 | 0-0-8 | REJECTED: v1.3 offence + close_r 35, close_gap 0.35 w/ 0.3m arrival, strip <2.8m, cover 4.25m behind ball, box tackles. FULL shots 3.8/m |
| v1.4-offonly / b-off / c | 8/8/8 | -1.9/-1.4/-1.6 | 1-2-21 | not better: v1.4 offence + v1.3 defence (beam 32, ply 2 on dribble+hold, refit keeper, pass1 always, half-space balls, pocket role, stamina floor). Only 12 on-ball decisions/match within 30m (v1.3: 31) |
| v1.4c + brake / cone / tackle | 8 each | -1.0 / -1.1 / -2.25 | 0-4-20 | brake = 0.35m arrival goal-side; cone = cover 4.25m behind ball (their shots 1.5/m, our box 3.7%); tackle = emerg_r 26 / p 0.72 / foul 0.55 (their shots 3.4/m: REJECTED) |
| v1.4d = c + brake + cone | 8 | -2.25 | 0-1-7 | not better → v1.4c NOT promoted |
| **Ablation 2026-10-29, each from clean v1.3, 16 matches, staggered launcher** | | | | |
| A = v1.3 + shot fixes | 14 | -1.07 | 2-2-10 | fitted FULL keeper, out=True rest-point fix, shot3 at measured 2.4 m/s, shot1_min 2.2. Neutral; shots 1.1/m. (The suspected `shot3 arrive_in=1` bug is NOT a bug: arrive_in=1 → max-power branch, accept_late unused) |
| B = A + shot-cone cover + stamina floor | 16 | -1.19 | 2-1-13 | not better. Shots 1.9 vs 2.0, floor hits 9/63 (A 36/56), but dispossessed 8.1/m |
| C = A + runner to far side of their box | 16 | -1.06 | 1-1-14 | not better; our shots 0.4/m |
| D1 = A + trailing support (FULL-like: wide trails 9m behind, 7m central, in their half) | 16 + 16 | -0.56 / -0.94 | 2-12-18 | **pooled -0.75 → PROMOTED as v1.4** (~1 SE better than v1.3; FULL shots 1.6 / 1.9 per m) |
| D2 = A + goal-side block (press 3m goal-side, 0.5m arrival, like Bhv_Block) | 16 | -1.00 | 2-3-11 | not better |
| v1.4 pooled (2 batches + same-day control VCT) | 44 | -0.95 | 3-13-28 | control 2026-10-29: -1.50 (3-21, FULL 2.6 shots/m) - the -0.75 from 32 matches was partly luck |
| v1.5 (agent_v15.py, not ours) | 11 | -1.64 | 0-2-9 | bundle: shot_m0 -2, no space passes, pass P veto, dodge, reach model changes |
| **v1.6 ablation 2026-10-29, gates of 12, staggered** | | | | |
| i1 = v1.4 + mark/cover arrive within 0.7m (ignore.md P3) | 12 | -1.00 | 1-2-9 | REJECTED (and again on i3: -1.25, FULL shots 1.8 vs 1.4) |
| i2 = v1.4 + shot-cone cover + stamina guard | 12 | -1.50 | 0-2-10 | = control; split up below |
| i3 = v1.4 + threat-path press everywhere (close_r 0, v1.2f's) | 12 | -0.67 | 0-5-7 | KEPT: FULL shots 1.4, our box 3.7% |
| i3 + stamina floor guard (ignore.md P9) | 12 | -0.50 | 3-4-5 | KEPT: FULL shots 1.2 |
| i3 + stamina + shot-cone cover | 12 | -1.83 | 0-1-11 | REJECTED: FULL shots 2.5, 8 goals after dispossession (nobody deep) |
| **v1.6 = i3 + stamina** (gate 12 + validation 24) | 36 | **-0.81** | 4-11-21 | PROMOTED. FULL 1.7 shots/m, floor hits 44% (v1.4 ~70%), cpu 1.06ms avg / 26ms max, 0 cut-offs, 3 fouls / 0 cards. Validation alone: -0.96 |
| exp v1.5 | 8 | -1.75 | 0-1-7 | REJECTED: solved passing/clustering bugs (96% ok in tight games), but over-pushed forward & premature shots (shot_m0=-2) conceded counter-attacks (-1.75 GD/m vs v1.3 -0.90) → agent.py remains v1.3 |
- **Press family, pooled**: threat-path press everywhere (v1.2f + i3 + v1.6, 67 matches) -0.73 GD/m, FULL ~1.6 shots/m; close press <25m (v1.3 + v1.4, 63 matches) -1.06, FULL ~2.1. ~1.4 SE.
- **Noise rule**: per-match GD SD ~1.3, so 12 matches = SE 0.38. Single gates swing ±0.5 (v1.4: -0.56, -0.94, -1.50; v1.6: -0.50 then -0.96). Judge on pooled GD + FULL shots, and always run a same-day control.
- **Possession value (measured over ~150 matches, E[GD in next 200 cycles])**: ours -0.20 (own goal line) .. -0.07 (x=-15) .. -0.03 (x=+15) .. +0.01 (their box); FULL's +0.14 .. +0.51 everywhere. Losing the ball costs ~0.2-0.3 goals, 20m of progress gains ~0.02: our Eval already values progress MORE than this (ratio 0.17 vs 0.10). Do NOT raise prog_lin.
- **Carry pace**: all players are type 0 (identical bodies). FULL carries +0.31 m/cycle toward goal (0.57 m/cycle overall, a touch every 3.8 cycles); we +0.10 (0.47, every 2.6) - our dribbles go sideways to stay away from opponents.
- **go_to_point default tolerance** is max(1, ball_dist/10) = 1.8-2.9m in defence: 16% of mark and 14% of cover decisions are 'parked' 0.7m+ from their spot. Fixing it (i1) did not help.
- **Keeper restarts** (framework, not Agent1): after a catch our keeper always smart-kicks to (-10, +-25) across our box; 11 of 106 recent goals conceded came straight from it.
- **shot3 arrive_in=1 is NOT a bug**: 67 of 68 shot3 from >11m fired (62 single touch, median 2.42 m/s). Probe vs Agent2 (src/student/agent_probe.py): current shot3 2.74 m/s 7/10 goals; arrive_in=_arrive_in(d)+1 2.18 m/s 2/9; shot1 2.57 m/s 1/6.
- What decides matches: FULL converts ~90% of its shots (14-20m, our defenders: 0.4 in the shot cone, nearest 4.2m median); ~1 of our 4 field players is goal-side when FULL attacks our half. Our attack: only ~5% of on-ball decisions within 30m of goal; shot P there ≈ 0 by our model, so we dribble at 25-30m.
- **Their keeper (fit 2026-10-28, 98 unblocked shots at FULL's keeper)**: he saves everything he can reach - full sprint after a 1-cycle reaction, 1.2m catch, P(goal) = 0.97·sig(1.2·(gk_t − T − 2)), log-loss 0.13 (v1.3's model 0.56 on the same set, but its shape is close). Calibrated by distance: 16-22m pred 0.69 / act 0.68, 22-35m 0.43 / 0.44. So an unblocked 18-22m shot at a SET keeper really is ~0: the fix is reaching angles he can't cover, not lowering shot margins. Both keepers are the same `HeliosGoalie` (src/decision_makers/goalie_decision_maker.py); FULL's ~85% conversion is SHOT SELECTION (its proxy preprocess + `HeliosShoot` only shoot when the keeper can't reach), so never fit on FULL's shots.
- **FULL = the HELIOS base team** (`USE_STARTER=0`, source in src/): on ball `HeliosShoot` then `HeliosOffensivePlanner` (C++ action-chain search: pass/through/lead/dribble/cross, opponent-distance penalty); proxy preprocess auto-shoots (we get `ignore_shootInPreprocess`). Off ball (`move_decision_maker.py`): `HeliosBasicTackle(min_prob=0.8)` every cycle → intercept if self_min<=3 or first-ish → `Bhv_Block` (go to the first point on the opponent's predicted dribble path to its target that we reach in time, threshold 0.5) → formation spot (`src/formations/4-3-3-5aside`). helios_* actions are FORBIDDEN for us (policy.py: "the reference planner"); the ideas can be reimplemented with the allowed API.
- **Bug in v1.3 `_shot_value`**: `opp_response(c, pts, False)` races blockers to the ball's rest point BEHIND the goal line → finite margin even when nobody can reach → shot P capped ~0.6. Fixed in v1.4 (`out=True`).
- Dribble model at drib_m0 -2 is calibrated (3.6% of touches dispossessed vs mean predicted p 0.955); tightening it only makes hold win. Ply-2 backup must be max(Eval, follow-up) applied to ALL kinds incl. hold; an extra opponent race at the endpoint double-counts the path race.
- Collisions (rcg flag 0x800): 4.7% of mark cycles, <1% for press/cover → `go_to_point(dodge=True)` would only steer marks/pressers off their man; not used. `advance_ball`/`stop_ball` targets are chosen inside the proxy, so expectimax can't score them; space passes / 3-touch smart kick already cover them.
