# AIMA Chapters 3 & 4: Heuristic and Real-Time Search (Reference Guide)

Source: *Artificial Intelligence: A Modern Approach (4th Edition)*, Chapters 3 & 4, pp. 81–163.  
Grounded in **COL333 Lectures L03, L05, L06: Search & Optimization**.

---

## 1. Budget-Aware Iterative Deepening (AIMA Section 3.3.4, p. 95)

In real-time games with wall-clock decision limits (such as our 1.0s maximum per decision and 75s CPU match limit):
- Search cannot run to arbitrary depth $d$.
- **Iterative Deepening Search (IDS)** systematically explores depths $1, 2, 3, \dots$, maintaining the best decision from the last fully completed depth.
- If remaining CPU time drops below a safety threshold (e.g. 50ms), the current search aborts immediately and returns the best answer found at depth $d-1$.

### Budget-Aware Pattern for Assignment 3
```python
def decide_action(agent, candidates):
    best_action = fallback_action(agent)
    depth = 1
    
    # Check remaining match CPU time and per-decision wall-clock time
    while depth <= MAX_DEPTH:
        if agent.budget.remaining_ms < 400 or agent.budget.decision_remaining_ms < 60:
            break
            
        action, score = search_depth(agent, depth, candidates)
        if action is not None:
            best_action = action
        depth += 1
        
    return best_action
```

---

## 2. Local Beam Search & Action Filtering (AIMA Section 4.1.4, p. 134)

In 5-a-side football, each player can kick, dribble, or pass in infinite continuous directions.

### Beam Search Over Candidate Actions:
1. **Sample**: Sample $K$ candidate spatial points (e.g., $N$ radial points around teammates using `Tools.points_around`, plus 3 dribble vectors).
2. **Prune (Rules Filter)**: Drop any candidate target that:
   - Exceeds max kick distance (`target.dist(ball) > 30.0`).
   - Is offside (`target.x() > wm.offside_line_x`).
   - Is obstructed by an opponent in the passing cone (`Tools.exist_opponent_in(agent, Sector2D)`).
3. **Select Beam**: Retain only the top $B$ highest-ranked candidate actions according to a quick spatial heuristic (e.g., forward advancement + distance from nearest defender).
4. **Deepen**: Feed only these $B$ candidate actions into the Minimax / $\alpha$-$\beta$ search tree.

---

## 3. Discretization of Continuous Action Spaces (AIMA Section 4.2, p. 137)

Continuous action spaces cannot be directly traversed by discrete tree search. Discretization bridges the gap:
- **Radial Grid**: Discretizing target zones using polar coordinates around key field entities:
  $$\text{target}_i = \text{center} + r \cdot [\cos(\theta_i), \sin(\theta_i)]$$
- **Velocity/Power Discretization**: Instead of searching continuous power from $0$ to $100$, discretize into 2–3 semantically distinct actions:
  - *Firm pass*: `Action.kick(agent, target, arrive_in=5)`
  - *Max power blast*: `Action.kick_one_step(agent, target)`
  - *Shield / hold*: `Action.hold(agent)`
