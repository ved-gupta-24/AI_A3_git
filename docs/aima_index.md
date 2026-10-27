# AIMA (4th Edition) Curriculum-Grounded Index & Reference Guide

This document maps concepts from the textbook **Artificial Intelligence: A Modern Approach (4th Edition)** (`AIMA.pdf`) to the course curriculum of **COL333 / COL7333 / COL671 / AIL7025** (Prof. Rohan Paul, IIT Delhi) and the specific requirements of **Assignment 3 (Game Playing AI)**.

> [!IMPORTANT]
> **Strict Course Compliance Rule**:
> Per [assignment.md](file:///Users/vedantgupta/Documents/AI_A3/assignment.md#L64-L67) and [course_content_taught.md](file:///Users/vedantgupta/Documents/AI_A3/course_content_taught.md#L926-L928), student agents **must rely solely on algorithms covered in the course syllabus (Lectures L01–L12) and their recognized textbook extensions**. Solutions based on fundamentally different mathematical principles (e.g. Deep Reinforcement Learning, Neural Networks, Genetic Algorithms, or external scientific solvers like `scipy.optimize`) are strictly out-of-scope and not permitted.

---

## 1. Compliance Boundaries: Permitted vs. Prohibited Ideas

| Category | Permitted Course Core & Textbook Extensions | Strictly Prohibited / Out of Scope |
| :--- | :--- | :--- |
| **Game Playing / Adversarial Search** | Minimax, $\alpha$-$\beta$ pruning, Move Ordering heuristics, Quiescence search, Iterative Deepening with CPU budgets, Transposition Tables, Expectimax, Monte Carlo Tree Search (MCTS) with UCT / UCB1. | Deep Q-Networks (DQN), AlphaZero deep policy/value networks, PPO/A3C, end-to-end policy gradient methods. |
| **State Evaluation & Heuristics** | Multi-feature linear & non-linear evaluation functions (e.g. goal distance, passing lanes, open space, opponent pressure, shot angles, ball control). | Black-box neural network evaluators, pre-trained embeddings. |
| **Search Space Management** | Beam search over sampled continuous actions (`points_around`), forward pruning, state abstraction, discretization of continuous coordinates. | Genetic algorithms, evolutionary strategies, particle swarm optimization. |
| **Multi-Agent Coordination** | Role-based allocation, centralized reasoning with decentralized execution (computing identical target allocations without communication). | Decentralized communication protocols (disallowed by assignment rules; agents run in isolated processes). |
| **Numerical Libraries** | Python standard library, `numpy`, `pyrusgeom` (provided in environment). | `scipy` (explicitly forbidden in `assignment.md`), PyTorch, TensorFlow, JAX. |

---

## 2. Course-to-AIMA Alignment Matrix

Use this matrix to instantly locate relevant theoretical grounding, pseudocode, and mathematical definitions in `AIMA.pdf` without wasting LLM tokens.

| Lecture / Topic (from `course_content_taught.md`) | AIMA 4th Ed. Chapter & Section | PDF Page | Permitted Algorithmic Extensions & Formulas |
| :--- | :--- | :--- | :--- |
| **L10: Adversarial Search (Deterministic)** | **Chapter 6.1 – 6.2** (Optimal Decisions in Games) | pp. 192–201 | • **Minimax Algorithm**: `MINIMAX-DECISION` (p. 196)<br>• **Alpha-Beta Pruning**: `ALPHA-BETA-SEARCH` with $\alpha, \beta$ bounds (p. 198)<br>• **Move Ordering**: Hash tables, shallow searches, killer moves (p. 200) |
| **L10: Evaluation Functions & Cutoffs** | **Chapter 6.3** (Heuristic Alpha-Beta Search) | pp. 202–207 | • **Heuristic Evaluation**: Linear weighted sum $Eval(s) = \sum w_i f_i(s)$ (p. 202)<br>• **Cutoff Test**: Budget-aware depth limit (p. 203)<br>• **Quiescence Search**: Resolving volatile states (kickable / tackling) before evaluating (p. 204)<br>• **Transposition Tables**: State hashing (Zobrist-style) for repeated ball/player states (p. 206) |
| **L10: Monte Carlo Tree Search (MCTS)** | **Chapter 6.4** (Monte Carlo Tree Search) | pp. 207–210 | • **MCTS Algorithm**: Selection $\to$ Expansion $\to$ Simulation $\to$ Backpropagation (p. 209)<br>• **UCT / UCB1 Selection**: $UCB1(n) = \frac{U(n)}{N(n)} + C \sqrt{\frac{\ln N(parent)}{N(n)}}$ (p. 209)<br>• **Playout Policies**: Fast heuristic rollouts for football situations |
| **L10: Stochastic Games & Uncertainty** | **Chapter 6.5** (Stochastic Games) | pp. 210–213 | • **Expectimax Search**: Chance nodes for opponent ball-intercept probabilities (p. 211)<br>• Evaluation with probability distributions over ball trajectories |
| **L03 & L06: Informed Search & Budgeting** | **Chapter 3.3, 3.5, 3.6** (Search Algorithms & Heuristics) | pp. 89–120 | • **Iterative Deepening Search (IDS)**: Depth-increment search with wall-clock cutoff (p. 95)<br>• **A\* Search & Heuristic Design**: $f(n) = g(n) + h(n)$, admissibility and consistency (p. 104) |
| **L05: Local Search & Action Space** | **Chapter 4.1 – 4.2** (Complex Environments & Continuous Spaces) | pp. 128–139 | • **Local Beam Search**: Tracking $k$ best candidate passing/dribbling points (p. 134)<br>• **Continuous Space Discretization**: Action sampling around teammates (`points_around`) (p. 137) |
| **L08: Sequential Decision Making (MDPs)** | **Chapter 16.1 – 16.2** (Making Complex Decisions) | pp. 544–560 | • **Value Iteration & Bellman Optimality**: $V^*(s) = \max_a \sum P(s' \mid s, a)[R(s, a, s') + \gamma V^*(s')]$ (p. 553)<br>• In-place dynamic programming updates |
| **L17: Multi-Agent Coordination** | **Chapter 17.1 – 17.3** (Multiagent Decision Making) | pp. 589–620 | • **Role Assignment**: Dynamic task allocation (passer, support, marker, interceptor)<br>• Coordination without communication under full-state perception |
| **L09: Reinforcement Learning** | **Chapter 23.2 – 23.3** (Reinforcement Learning) | pp. 842–854 | • **Temporal Difference (TD) Learning**: $V(s) \leftarrow V(s) + \alpha [r + \gamma V(s') - V(s)]$ (p. 844)<br>• **Tabular Q-Learning**: $Q(s, a) \leftarrow Q(s, a) + \alpha [r + \gamma \max_{a'} Q(s', a') - Q(s, a)]$ (p. 849) |

---

## 3. Applying These Ideas to 5-a-Side Football (Assignment 3)

### A. State Space & Discretization (AIMA Ch 4.2)
- **Challenge**: The football pitch is continuous (105m $\times$ 68m) with continuous velocities.
- **Solution**:
  - Sample candidate passing targets using `Tools.points_around(teammate.position, radius, n)`.
  - Discretize candidate dribble angles (e.g. 3–5 directional vectors toward the goal).
  - Use `Tools.home_position(agent)` as the default defensive anchor when no immediate tactical action is urgent.

### B. Heuristic Evaluation Function Design (AIMA Ch 6.3, p. 202)
Design a weighted linear evaluation function $Eval(s)$ for non-terminal game states:
$$Eval(s) = w_1 \cdot \text{GoalProximity} + w_2 \cdot \text{OpenPassingLanes} - w_3 \cdot \text{OpponentPressure} + w_4 \cdot \text{ShotQuality} + w_5 \cdot \text{PossessionControl}$$
- **Goal Proximity**: Distance of ball and attacking players from opponent goal (`Vector2D(52.5, 0.0)`).
- **Open Passing Lanes**: Free line-of-sight between ball and teammate (checked via `Sector2D` and `Tools.exist_opponent_in`).
- **Opponent Pressure**: Inverse distance to the nearest opponent (`Tools.get_opponent_nearest_to_self`).
- **Shot Quality**: Angle and distance to open portions of the opponent goal away from their goalie (`Tools.get_opponent_goalie`).

### C. Budget-Aware Iterative Deepening (AIMA Ch 3.3 & Ch 6.3)
- **Rules**: 75 seconds total CPU time per agent for 1500 cycles ($\approx 50$ms average per decision), with a hard 1.0s wall-clock cap.
- **Search Loop**:
  ```python
  best_action = fallback_action
  for depth in range(1, max_depth):
      if agent.budget.remaining_ms < 400 or agent.budget.decision_remaining_ms < 50:
          break  # Stop search safely before budget cutoff
      action, val = alpha_beta_search(agent, depth)
      if action is not None:
          best_action = action
  return best_action
  ```

### D. Quiescence Search for Critical Ball States (AIMA Ch 6.3, p. 204)
- When the ball is in a contested state (e.g. `wm.self.is_kickable` or opponent within tackle range), a static cutoff evaluation may be wildly inaccurate (the "horizon effect").
- Quiescence search continues 1–2 steps deeper only for critical actions (immediate shots, tackles, clearances) before applying $Eval(s)$.

---

## 4. Using the Offline Zero-Token Query CLI

To search or inspect specific textbook sections with zero LLM API cost:

```bash
# 1. Search keywords in course-approved chapters (default):
python3 scripts/query_aima.py "quiescence search"
python3 scripts/query_aima.py "monte carlo tree search"
python3 scripts/query_aima.py "evaluation function" --max-results 5

# 2. View full page content directly:
python3 scripts/query_aima.py --page 204

# 3. Search the entire book (if explicitly needed):
python3 scripts/query_aima.py "markov decision" --all-pages
```
