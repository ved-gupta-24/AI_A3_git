# AIMA Chapter 6: Adversarial Search and Games (Reference Guide)

Source: *Artificial Intelligence: A Modern Approach (4th Edition)*, Chapter 6, pp. 192–225.  
Grounded in **COL333 Lecture 10: Adversarial Search**.

---

## 1. Minimax Algorithm (AIMA Section 6.2, p. 196)

### Mathematical Formulation
For a two-player zero-sum game with players $\text{MAX}$ and $\text{MIN}$:
$$\text{Minimax}(s) = \begin{cases} 
\text{Utility}(s, \text{MAX}) & \text{if } \text{Terminal}(s) \\
\max_{a \in Actions(s)} \text{Minimax}(\text{Result}(s, a)) & \text{if } \text{Player}(s) = \text{MAX} \\
\min_{a \in Actions(s)} \text{Minimax}(\text{Result}(s, a)) & \text{if } \text{Player}(s) = \text{MIN}
\end{cases}$$

### Pseudocode
```python
def minimax_decision(state):
    return max(actions(state), key=lambda a: min_value(result(state, a)))

def max_value(state):
    if is_cutoff(state):
        return eval(state)
    v = -infinity
    for a in actions(state):
        v = max(v, min_value(result(state, a)))
    return v

def min_value(state):
    if is_cutoff(state):
        return eval(state)
    v = +infinity
    for a in actions(state):
        v = min(v, max_value(result(state, a)))
    return v
```

---

## 2. Alpha-Beta Pruning (AIMA Section 6.2.3, p. 198)

Alpha-Beta pruning computes the exact same minimax decision while pruning branches that cannot possibly influence the final decision.

### Pruning Conditions:
- $\alpha$: Highest-value choice found so far along the path for $\text{MAX}$.
- $\beta$: Lowest-value choice found so far along the path for $\text{MIN}$.
- **Prune below MIN node** when $v \le \alpha$.
- **Prune below MAX node** when $v \ge \beta$.

### Pseudocode
```python
def alpha_beta_search(state, depth, alpha=-float('inf'), beta=float('inf')):
    best_action = None
    v = -float('inf')
    for a in ordered_actions(state):
        val = min_val(result(state, a), depth - 1, alpha, beta)
        if val > v:
            v = val
            best_action = a
        alpha = max(alpha, v)
    return best_action, v

def max_val(state, depth, alpha, beta):
    if depth <= 0 or is_terminal(state):
        return evaluate(state)
    v = -float('inf')
    for a in ordered_actions(state):
        v = max(v, min_val(result(state, a), depth - 1, alpha, beta))
        if v >= beta:
            return v  # Pruning by beta
        alpha = max(alpha, v)
    return v

def min_val(state, depth, alpha, beta):
    if depth <= 0 or is_terminal(state):
        return evaluate(state)
    v = float('inf')
    for a in ordered_actions(state):
        v = min(v, max_val(result(state, a), depth - 1, alpha, beta))
        if v <= alpha:
            return v  # Pruning by alpha
        beta = min(beta, v)
    return v
```

---

## 3. Heuristic Evaluation & Cutoff Strategies (AIMA Section 6.3, pp. 202–207)

### Linear Weighted Evaluation Function
$$Eval(s) = \sum_{i=1}^n w_i \cdot f_i(s)$$
Where:
- $f_i(s)$ are extracted numerical features of the game state.
- $w_i$ are positive or negative weights reflecting tactical value.

### Quiescence Search (p. 204)
- **Problem**: Fixed depth cutoffs suffer from the *horizon effect*, evaluating a state right in the middle of a tackle or pass interception where a large swing in utility is imminent.
- **Solution**: Do not apply the static evaluation function to non-quiescent states. If the ball is loose within reach of multiple players, expand the search further restricted only to "violent" actions (tackles, shots, clearances) until a stable state is reached.

---

## 4. Monte Carlo Tree Search (MCTS / UCT) (AIMA Section 6.4, pp. 207–210)

MCTS does not require an exhaustive game tree expansion; it directs search toward promising paths using random or heuristic simulation rollouts.

### The 4 Phases:
1. **Selection**: Starting at the root, choose child nodes according to the **UCB1** policy until reaching a node that has unexpanded children.
   $$\text{UCB1}(n) = \frac{U(n)}{N(n)} + C \sqrt{\frac{\ln N(\text{parent}(n))}{N(n)}}$$
   - $\frac{U(n)}{N(n)}$: Exploitation term (average observed utility / win rate).
   - $C \sqrt{\frac{\ln N(\text{parent})}{N(n)}}$: Exploration bonus (favors rarely visited nodes; typically $C = \sqrt{2} \approx 1.414$).
2. **Expansion**: Create one or more child nodes for unexplored actions from the selected leaf.
3. **Simulation (Rollout)**: Execute a fast rollout policy (random actions or simple greedy heuristic) from the new child until a fixed horizon or terminal state.
4. **Backpropagation**: Propagate the outcome utility back up the path, incrementing visit counts $N(n)$ and accumulating utility $U(n)$.

---

## 5. Expectimax Search (AIMA Section 6.5, pp. 210–213)

When the environment or opponent behavior is non-deterministic (e.g. chance of opponent intercepting a pass, tackle success probability):
$$\text{Expectimax}(s) = \begin{cases}
\text{Utility}(s) & \text{if Terminal}(s) \\
\max_a \text{Expectimax}(\text{Result}(s, a)) & \text{if MAX node} \\
\sum_{s'} P(s' \mid s, a) \cdot \text{Expectimax}(s') & \text{if CHANCE node}
\end{cases}$$
