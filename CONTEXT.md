# CONTEXT.md — COL333 Assignment 3 (Football AI Agent)
> Ultra-dense reference for coding `Agent1` in `src/student/agent.py`. Zero-hallucination signatures & rules.

---

## 1. Environment, Rules & Hard Constraints
- **Submission**: Only `src/student/agent.py` is evaluated (`Agent1` class). Python 3 standard library + `numpy` + `pyrusgeom` only. **`scipy` is strictly FORBIDDEN**.
- **Process Isolation**: Each player runs in a separate process. No IPC, no network, no disk sharing, no `say`/`attentionto`. All coordination is computed from shared full-state perception (`agent.wm`).
- **Time Budgets**: 1500 cycles/match. Total CPU budget = 75.0s per agent per match (~50ms/step). Hard wall-clock limit = 1.0s/decision (5 violations = player sent off; >1.5s = match forfeit).
- **Pitch & Coordinates**: Pitch is `[-52.5, 52.5] x [-34.0, 34.0]`. Always attacking towards `+x` (opponent goal at `(52.5, 0)`), our goal at `(-52.5, 0)`. Angle `0°` = ahead (`+x`), `90°` = right (`+y`), `-90°` = left (`-y`), `180°` = behind (`-x`).
- **Simulator Quirks**:
  - `Action.tackle`: Power is `1.0` straight ahead (0°), `0.5` sideways (±90°), `0.0` backward (±180°). `tackle_back_dist` is 0.
  - `Action.kick`: If cannot satisfy `accept_late`, shields ball, returns `False`, and proxy executes the next emitted fallback action.
  - Goalie: Controlled automatically. Backward dash clamped to 0 under `rcssserver 19.0.0`; easily stranded if pulled out. Back-pass to goalie concedes indirect free kick.
  - Offside: Evaluated only in opponent half (`target.x() > 0` and `target.x() > wm.offside_line_x - 0.5`).
  - Tie-breakers: Goal Difference -> Goals Scored -> Fewest Yellows (Red = 2.5 Yellows) -> Fewest Fouls.
- **Permitted Algorithms (COL333 L01-L12)**: Minimax, $\alpha$-$\beta$ pruning (iterative deepening, move ordering, transposition tables), Heuristic linear evaluation $Eval(s) = \sum w_i f_i(s)$, Quiescence search (for contested ball/tackle states), Expectimax (stochastic intercepts), MCTS/UCT, Beam search, CSP role assignment. **Deep RL, Neural Nets, Genetic Algos are FORBIDDEN.**

---

## 2. World Model API (`agent.wm`)
> **CRITICAL**: In `pyrusgeom.geom_2d.Vector2D`, `.x()` and `.y()` are **METHODS**, NOT properties!
- `wm.ball`: `.position` (`Vector2D`), `.velocity` (`Vector2D`), `.dist_from_self` (`float`).
- `wm.self`: `.position` (`Vector2D`), `.velocity` (`Vector2D`), `.body_direction` (`AngleDeg`), `.stamina` (`float` in `[0, 8000]`), `.effort`, `.recovery`, `.is_kickable` (`bool`), `.uniform_number` (`int`), `.tackle_probability` (`float`).
- `wm.teammates` / `wm.opponents`: `list[Player]` (excludes self).
  - `Player`: `.uniform_number` (`int`), `.position` (`Vector2D`), `.velocity` (`Vector2D`), `.body_direction`, `.dist_from_self`, `.dist_from_ball`, `.is_goalie` (`bool`), `.ball_reach_steps` (`int`), `.inertia_final_point` (`Vector2D`).
- `wm.intercept_table`: `.self_reach_steps`, `.first_teammate_reach_steps`, `.first_opponent_reach_steps` (`int`).
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
- `Sector2D(origin: Vector2D, min_r, max_r, start_angle_deg, end_angle_deg)`.
- `note(agent, label: str, **kwargs)`: Traces decision for `a3.py why` analysis.

---

## 4. CLI Commands (`a3.py`)
```bash
python3 a3.py doctor                                        # Verify environment setup
python3 a3.py match STARTER FULL --right full -t 50         # Test vs TA reference baseline (50 cycles)
python3 a3.py match STARTER AGENT2 --right :Agent2 -t 50    # Test vs passive opponent
python3 a3.py match MINE1 MINE2 --left :Agent1 --right :Agent1 # Self-play testing
python3 a3.py why -t STARTER --limit 30                     # Decision trace diagnostics
python3 a3.py why --slow 50.0                               # Find decisions exceeding 50ms CPU
python3 a3.py watch                                         # Browser match visualizer (port 8080)
```

---

## 5. Modular `Agent1` Skeleton Contract
```python
class Agent1(StarterAgent):
    def on_ball(self, agent) -> None:
        """Priority: Shoot -> Pass (Alpha-Beta/Beam) -> Dribble -> Hold -> Clear."""
    def off_ball(self, agent) -> None:
        """Priority: Intercept/Tackle -> Mark/Block Opponent -> Return to Home Formation."""
    def can_shoot(self, agent) -> bool: ...
    def search_pass(self, agent) -> Vector2D | None: ...
    def search_dribble(self, agent) -> Vector2D | None: ...
    def evaluate_state(self, agent, ball_pos: Vector2D) -> float: ...
    def should_intercept(self, agent) -> bool: ...
    def block_lane(self, agent) -> Vector2D | None: ...
```
