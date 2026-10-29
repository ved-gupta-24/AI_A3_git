# Strategy of the current model (v1.6)

The submitted `Agent1` in plain words. Exact weights and code: `model_agent.py`
(all tunables are in the `W` dict). Every experiment and why it was kept or
rejected: `CONTEXT.md` §7.

## The model

Each cycle a player either has the ball (`on_ball`) or not (`off_ball`).
Every player runs in its own process with no communication, but sees the
exact same state, so teammates coordinate by computing the same answer.

Values are in **goals**: `Eval(ball at p)` ≈ how likely possession there
ends in a goal for us, minus for them. It grows with progress up the pitch
and sharply near the opponent's goal (shot threat), is reduced when an
opponent is close, and is mirrored and negated when they have the ball.

## With the ball - depth-limited expectiminimax

1. **Generate moves (MAX)**:
   - shots at 9 points across the goal;
   - passes around each onside teammate (rings at 0 / 3 / 6 m, through-balls 10 m ahead), plus passes into space;
   - dribbles in 11 directions × 3 distances;
   - hold and clear.
2. **Opponent reply (MIN)**: the ball's path is simulated with the real decay.
   For every opponent we compute the first cycle he can be on it. The keeper
   gets a catch radius and a penalty for having to move backwards.
   - **Shots (v1.4)**: outfield blockers and the keeper are modelled
     separately. The keeper model was fitted on 98 real unblocked shots at
     FULL's keeper: he sprints after a 1-cycle reaction, catches within 1.2 m,
     and saves essentially everything he can reach (predicted vs actual goal
     rate 0.69 / 0.68 at 16-22 m). Multi-touch shots are modelled at their
     measured release speed (2.4 m/s, not the 3.0 maximum), and a shot nobody
     can reach is no longer capped at P ≈ 0.6 (v1.3 raced blockers to a "rest
     point" behind the goal line).
3. **Chance node**: P(we keep it) = sigmoid of how many cycles our receiver
   beats the first opponent by. Passes are calibrated ×0.9 from measured
   completion rates. An opponent within ~1.6 m can tackle before a slow
   action (multi-touch kick, dribble, hold) gets away.
4. **Expected utility** = P·Eval(where we receive it) + (1−P)·Eval(where they win it).
   The best few passes are searched one ply deeper (what the receiver can do
   next: shoot or pass on).
5. **Anytime and budget-aware**: candidates are searched best-first, with
   pruning of those that cannot beat the current best. Search stops at a time
   slice of the remaining CPU budget (~1 ms average, 21 ms worst, of 75 s).
6. **Safe emission**: we send the best action, then the best non-kick
   alternative, then a clear. A refused multi-touch kick therefore never leaves
   the player doing nothing.

Hard rules (value −∞):
- never pass to an offside teammate;
- never let our own keeper be first to a ball we played, and never hold or
  dribble inside our own box (back-pass → indirect free kick);
- no passes into space from our own third.

## Without the ball - same CSP in every process

- **Phase**: whoever reaches the ball first decides attack vs defence.
- **Attack**: carrier + 3 roles, assigned by trying every permutation
  (≤ 3! / 4!) and minimising total time to the spots:
  - **forward** (on the offside line);
  - **wide** - in our half out on the flank; **in their half (v1.4) it trails
    ~9 m behind the ball and ~7 m toward the centre**, copied in spirit from
    FULL (its supporters sit 11-13 m behind the ball, ours used to stand level
    with it among their defenders). It is a safe outlet and already goal-side
    when we lose the ball;
  - **back** - rest defence, never past x = −5.

  Each supporter then samples 17 nearby spots and takes the one the carrier
  could pass to with the best EU, while avoiding crowding.
- **Defence**: **press** + 2 **marks** (goal-side of the most dangerous
  opponents) + **cover** (between ball and goal).
  - The presser is whoever can get in front of the carrier's most dangerous
    line (straight at our goal) first, at the first point of it he reaches
    before the carrier - **everywhere, including near our goal (v1.6)**.
    v1.3/v1.4 switched to a tight press 1 m goal-side of the ball inside
    25 m; FULL then shot ~2.0-2.4 times a match against ~1.4-1.7 with the
    threat-path press (it is also how FULL's own `Bhv_Block` defends).
  - Players upfield of the ball sprint back.
- **Tackles**: only after an EU comparison with not tackling.
  - Clean tackles on a loose ball we would otherwise lose.
  - On a controlled ball only as a last resort inside 20 m, because
    tackling a player in control was called a foul 4 times in 5.
  - Never `foul=True`.
- **Stamina**: sprint only when urgent. Below 4500 stamina players cap at
  jogging, below 3000 they trot. **v1.6 adds a hard floor that applies even
  to urgent runs**: below 3400 at most 60 (45 if not urgent), below 2800 at
  most 42 - under the ~45/cycle a player recovers. The simulator stops
  dashing at ~2446, where a player crawls; players reaching it fell from
  ~70% to ~44% of player-matches (`Action.intercept` and dribbles still pick
  their own power, so it is not zero).

## What still decides matches vs FULL (see SUMMARY.md)

v1.6: −0.81 GD/match over 36 matches, W4 D11 L21 (v1.4: −0.95 over 44,
v1.3: −1.06). On GD alone the gain over v1.4 is within noise; the
threat-path press is supported more broadly - every version with it
(v1.2f, v1.6, 67 matches) averages −0.73 against −1.06 for every version
with the close press (v1.3, v1.4, 63 matches) - and FULL shoots less.

- **Their possession is worth far more than ours.** Measured over ~150
  matches: FULL's possession is worth +0.14 to +0.51 goals in the next 200
  cycles wherever it is; ours −0.07 to +0.01, even in their box. Losing the
  ball costs ~0.2-0.3 goals and 20 m of progress gains ~0.02, so the search
  is right to keep the ball rather than force it forward; that is why our
  carries look sideways (+0.10 m/cycle toward goal; FULL +0.31).
- **Their shooting**: FULL converts ~90% of its shots, from 11-20 m - its
  proxy only shoots when our keeper cannot reach. Both keepers are the same.
- **Our keeper's restarts**: the framework keeper always clears to
  (−10, ±25) across our box; ~10% of goals conceded come straight from that
  ball being intercepted. It is not Agent1's code.
- **Tried and rejected in the v1.6 ablation**: tighter arrival for marks
  (they stop 2-3 m short of the spot - a real effect, but fixing it did not
  help), the cover standing in the shot cone 4.25 m behind the ball (FULL's
  shots doubled: nobody left deep), and the `shot3 arrive_in` change (made
  power shots slower: 2.18 vs 2.74 m/s, 2/9 vs 7/10 goals in a probe).
- **Passive defence fails**: parking the bus or swarming the ball was tried
  and conceded far more (CONTEXT.md §7).
