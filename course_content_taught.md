# Course Content Taught Reference Document
(course_content_taught.md)
# Comprehensive Grounded Technical Reference for AI Assignment
# Implementation
Course: Introduction to Artificial Intelligence (COL333 / COL7333 / COL671 / AIL7025)
Instructor: Prof. Rohan Paul, Department of Computer Science and Engineering, IIT Delhi


## 1. Purpose and Scope
This document serves as the single authoritative, evidence-based technical reference
manual for student assignments, AI coding assistants, and automated evaluation scripts in
the course COL333 / COL7333 / COL671 / AIL7025: Introduction to Artificial Intelligence
taught by Prof. Rohan Paul at IIT Delhi.


The scope encompasses all theoretical foundations, mathematical formulations, algorithmic
pseudocode, heuristic design principles, and implementation constraints presented across
the official course lecture materials (Lectures L01 through L12). It provides exact boundaries
regarding permitted techniques, computational complexity, operational software
environments (Ubuntu / Python 3), and anti-plagiarism compliance rules.


## 2. Source-Material Inventory
The course content synthesized within this document is derived strictly from the official
primary lecture slide decks:


   ● L01-Course-Overview.pdf ([source: 1]): Course logistics, evaluation scheme,
       programming environment (Python 3 / Ubuntu), honor code, academic integrity
       guidelines, primary and secondary textbooks.
   ● L02-Introduction.pdf ([source: 5]): Historical perspectives of AI, Turing Test,
       rational agent framework, PEAS categorization, environment dimensions,
       problem-solving modeling paradigm.
   ● L03-Problem-Solving-As-Search-Uninformed.pdf ([source: 6]): State-space
       graphs vs. search trees, frontiers, loop handling, BFS, DFS, Depth-Limited Search
       (DLS), Iterative Deepening Search (IDS), Uniform Cost Search (UCS), Beam Search,
       Bi-directional Search.


---

   ● L04-Constraint-Satisfaction.pdf ([source: 2]): CSP formalization, constraint
       types, Backtracking search, variable ordering heuristics (MRV, Degree), value ordering
       (LCV), constraint propagation (Forward Checking, Arc Consistency / AC-3,
       K-Consistency).
   ● L05-Local-Search-Algorithms.pdf ([source: 4]): Discrete optimization
       formulation, Hill-Climbing, local optima/plateaus, Local Beam Search, Stochastic
       Beam Search, Random Restarts, Random Walks.
   ● L06-Goal-Informed-Search.pdf ([source: 3]): Best-First Search, Greedy Best-First
       Search, A* Search, heuristic admissibility and consistency, heuristic dominance,
       composite heuristics, effective branching factor ($b^$), IDA.
   ● L07-Modeling-Uncertainty.pdf ([source: 9]): Probability spaces, joint probability
       distributions, marginalization, conditioning, inference by enumeration, chain rule,
       Bayes' rule, conditional independence, sampling mechanisms.
   ● L08-Markov-Decision-Processes.pdf ([source: 12]): Sequential decision making
       under uncertainty, MDP tuples, discount factor, state and Q-value functions, Bellman
       Optimality Equations, Value Iteration, Policy Iteration.
   ● L09-Reinforcement-Learning-II.pdf ([source: 8]): Model-Based RL, Model-Free
       RL, First-Visit Monte Carlo policy evaluation, Temporal Difference (TD) learning,
       Tabular Q-learning, exploration vs. exploitation ($\epsilon$-greedy, exploration
       functions).
   ● L10-Adversarial-Search.pdf ([source: 10]): Game theory basics, Minimax
       algorithm, Alpha-Beta pruning, node ordering effects, depth-limited search with
       evaluation functions, Expectimax, Monte Carlo Tree Search (MCTS / UCT).
   ● L11-Bayesian-Networks.pdf ([source: 11]): Directed Graphical Models, joint
       distribution factorization, Inference by Enumeration, Variable Elimination (VE), factor
       operations (Join, Eliminate), elimination ordering heuristics (Min-fill, Min-neighbors),
       D-separation, active/inactive triples.
   ● L12-Probabilistic-Learning.pdf ([source: 7]): Maximum Likelihood Estimation
       (MLE), Maximum A Posteriori (MAP) estimation, Naïve Bayes classification, Laplace
       smoothing ($k$-smoothing), Expectation-Maximization (EM) algorithm, BN structure
       learning score penalties.


## 3. Course Topic Map
Artificial Intelligence Core Curriculum


├── 1. Classical Problem Solving & Search


│ ├── Uninformed Search Strategies (BFS, DFS, DLS, IDS, UCS, Beam, Bi-directional)


│ ├── Goal-Informed / Heuristic Search (Greedy, A*, IDA*)


---

│ ├── Constraint Satisfaction Problems (Backtracking, MRV, Degree, LCV, FC, AC-3)


│ └── Discrete Optimization & Local Search (Hill-Climbing, Local Beam, Stochastic Search)


├── 2. Adversarial Decision Making & Games


│ ├── Deterministic Zero-Sum Games (Minimax, Alpha-Beta Pruning)


│ ├── Evaluation Functions & Cutoff Strategies


│ ├── Stochastic Games (Expectimax Search)


│ └── Sample-Based Search (Monte Carlo Tree Search / MCTS / UCT)


├── 3. Probabilistic Reasoning & Graphical Models


│ ├── Probability Foundations (Joints, Marginals, Conditionals, Bayes Rule)


│ ├── Bayesian Networks Semantics & Factorization


│ ├── Exact Inference (Inference by Enumeration, Variable Elimination)


│ └── Independence Analysis (D-Separation, Active/Inactive Triples)


├── 4. Sequential Decision Making Under Uncertainty


│ ├── Markov Decision Processes (MDPs: S, A, T, R, gamma)


│ ├── Dynamic Programming Algorithms (Value Iteration, Policy Iteration)


│ └── Reinforcement Learning (Model-Based, First-Visit MC, TD Learning, Q-Learning)


└── 5. Probabilistic Learning & Parameter Estimation


  ├── Parameter Estimation Frameworks (MLE vs. MAP)


  ├── Generative Classifiers (Naïve Bayes, Laplace Smoothing)


  ├── Latent Variable Models (Expectation-Maximization / EM)


  └── Structural Learning Principles (Bayes Net Structure Search)


---

## 4. Detailed Topic-by-Topic Coverage

### 4.1 Foundations of AI & Rational Agents
  ● AI Definitions: Categorized along two dimensions—Thinking vs. Acting, and
     Human-like vs. Rational performance. Rational agents select actions that maximize
     expected utility given current percept sequences and internal knowledge.
  ● Turing Test: Operational test for acting humanly involving Natural Language
     Processing, Knowledge Representation, Automated Reasoning, Machine Learning,
     Computer Vision, and Robotics.
  ● PEAS Framework: Specifies Performance Measure, Environment, Actuators, and
     Sensors.
  ● Environment Properties: Fully vs. Partially Observable, Single vs. Multi-Agent,
     Deterministic vs. Stochastic, Episodic vs. Sequential, Static vs. Dynamic, Discrete vs.
     Continuous.


### 4.2 Problem Solving as Uninformed Search
  ● Search Formulation: Requires State Space $S$, Initial State $s_0$, Actions $A(s)$,
     Transition Model $Result(s,a)$, Goal Test $Goal(s)$, and Step Cost $c(s,a,s')$.
  ● State-Space Graph vs. Search Tree: Graphs implicitly characterize the problem (each
     state appears once). Trees explicitly represent expanded paths from the root $s_0$
     (nodes correspond to entire paths).
  ● Frontier Data Structures: Priority Queue (UCS, Best-First), FIFO Queue (BFS), LIFO
     Stack (DFS).
  ● Graph Search Rule: Explored set maintains visited states to prevent redundant loop
     expansions.
  ● Uninformed Algorithms:
         ○ BFS: Expands shallowest nodes. Complete and optimal for unit step costs.
             Time: $O(b^d)$, Space: $O(b^d)$.
         ○ DFS: Expands deepest nodes. Incomplete in infinite spaces, non-optimal.
             Time: $O(b^m)$, Space: $O(bm)$.
         ○ DLS: DFS constrained to depth limit $l$. Time: $O(b^l)$, Space: $O(bl)$.
         ○ IDS: Iteratively calls DLS with $l = 0, 1, 2, \dots$. Combines DFS space
             complexity $O(bd)$ with BFS completeness/optimality.
         ○ UCS: Expands node with lowest path cost $g(n)$. Complete and optimal if
             step costs $\ge \epsilon > 0$. Time/Space: $O(b^{1 + \lfloor C^* / \epsilon
             \rfloor})$.
         ○ Bi-directional Search: Simultaneous forward and backward search.
             Time/Space: $O(b^{d/2})$.


---

### 4.3 Goal-Informed / Heuristic Search
  ● Heuristic Function $h(n)$: Problem-specific estimate of cheapest path cost from
     node $n$ to a goal. $h(n) = 0$ if $n$ is a goal.
  ● Greedy Best-First Search: Node expansion prioritized by $f(n) = h(n)$. Fast but
     incomplete and non-optimal.
  ● A* Search: Combines backward cost $g(n)$ and forward cost $h(n)$ using $f(n) =
     g(n) + h(n)$.
  ● Admissibility: $h(n) \le h^(n)$ for all $n$, where $h^$ is true cost to goal. Guarantees
     optimality for A* Tree Search.
  ● Consistency (Monotonicity): $h(s) \le c(s, a, s') + h(s')$. Satisfies triangle inequality;
     guarantees $f(n)$ is non-decreasing along any path. Guarantees optimality for A*
     Graph Search.
  ● Dominance: $h_2$ dominates $h_1$ if $h_2(n) \ge h_1(n)$ for all $n$. A* with $h_2$
     expands fewer or equal nodes than with $h_1$.
  ● Composite Heuristics: $h(n) = \max(h_1(n), h_2(n), \dots, h_m(n))$ is admissible and
     dominates all individual admissible heuristics.
  ● Effective Branching Factor ($b^*$): Defined via $N + 1 = 1 + b^* + (b^)^2 + \dots +
     (b^)^d$, where $N$ is total nodes generated at depth $d$.
  ● IDA*: Iterative Deepening A* uses $f$-value limits rather than depth limits to achieve
     linear space complexity $O(bd)$.


### 4.4 Constraint Satisfaction Problems (CSPs)
  ● CSP Definition: Tuple $(X, D, C)$ with variables $X = {X_1, \dots, X_n}$, domains $D =
     {D_1, \dots, D_n}$, and constraints $C$.
  ● Constraint Types: Unary (single variable), Binary (pairs), Higher-order ($k \ge 3$
     variables), Soft constraints/Preferences.
  ● Backtracking Search: Depth-first search picking single variable assignments
     incrementally.
  ● Ordering Heuristics:
         ○ MRV (Minimum Remaining Values): Choose unassigned variable with fewest
             legal domain values ("Fail-Fast").
         ○ Degree Heuristic: Break MRV ties by choosing variable involved in highest
             number of constraints on unassigned variables.
         ○ LCV (Least Constraining Value): Choose value ruling out fewest choices for
             neighboring unassigned variables ("Fail-Last").
  ● Constraint Propagation / Inference:
         ○ Forward Checking: When variable $X$ is assigned, prune inconsistent values
             from domains of unassigned neighbors $Y$ connected to $X$.


---

         ○ Arc Consistency (AC-3): Arc $X \to Y$ is consistent if for every $x \in D_X$,
             there exists $y \in D_Y$ satisfying binary constraints. Time complexity:
             $O(n^2 d^3)$ for $n$ variables with domain size $d$.
         ○ K-Consistency: $k=1$ (Node), $k=2$ (Arc), $k=3$ (Path consistency).


### 4.5 Local Search & Discrete Optimization
  ● Optimization Formulation: Search state space $X$ to maximize evaluation function
     $Eval(X)$ or minimize cost $Cost(X)$ where path to solution is irrelevant.
  ● Hill-Climbing Search: Iterative local move to highest-valued neighbor. Stops at local
     maxima, ridges, or plateaus.
  ● Escaping Local Optima:
         ○ Stochastic Hill-Climbing: Selects randomly among uphill moves weighted by
             steepness.
         ○ Random Restarts: Conducts series of independent hill-climbing searches from
             randomly sampled initial states.
         ○ Local Beam Search: Keeps $k$ parallel states. Generates all successors,
             retains top $k$ overall.
         ○ Stochastic Beam Search: Samples $k$ successors with probability
             proportional to state evaluation scores.


### 4.6 Adversarial Search & Game Playing
  ● Game Formalism: Two-player zero-sum deterministic games defined by initial state
     $s_0$, actions $A(s)$, transition function $Result(s,a)$, terminal test $Terminal(s)$,
     and utility function $Utility(s, p)$.
  ● Minimax Algorithm: Recursively evaluates game tree assuming MAX maximizes
     payoff and MIN minimizes payoff. Complete, optimal against optimal opponents.
     Time: $O(b^m)$, Space: $O(bm)$.
  ● Alpha-Beta Pruning: Maintains bounds $\alpha$ (MAX's best alternative along path
     to root) and $\beta$ (MIN's best alternative).
         ○ Prune subtree below MIN node if $v \le \alpha$.
         ○ Prune subtree below MAX node if $v \ge \beta$.
         ○ Best-case time complexity with optimal move ordering: $O(b^{m/2})$.
  ● Evaluation Functions & Cutoffs: Replaces terminal tests with depth-limit cutoffs and
     utility functions with heuristic evaluation functions $Eval(s)$ (weighted sum of state
     features).
  ● Expectimax Search: Models non-deterministic game outcomes or stochastic
     opponents by taking expectation over chance nodes.
  ● Monte Carlo Tree Search (MCTS): Evaluates states via rollouts/simulations. Four
     phases:
         a. Selection: Traverses tree using UCT policy.


---

         b. Expansion: Adds new child state node.
         c. Simulation: Executes playout using default/random policy until terminal state.
         d. Backpropagation: Updates node visit counts $N(n)$ and win scores $W(n)$
             along path.


### 4.7 Probabilistic Reasoning & Bayesian Networks
  ● Probabilistic Foundations: Joint distributions $P(X_1, \dots, X_n)$ over discrete
     random variables.
  ● Marginalization: $P(Y) = \sum_{z} P(Y, Z = z)$.
  ● Conditioning: $P(Y | Z = z) = \frac{P(Y, Z = z)}{P(Z = z)}$.
  ● Bayesian Network Semantics: Directed Acyclic Graph (DAG) where nodes represent
     random variables and directed edges represent direct conditional dependencies.
  ● Joint Factorization:
     $$P(X_1, X_2, \dots, X_n) = \prod_{i=1}^{n} P(X_i \mid Parents(X_i))$$
  ● Inference by Enumeration: Computes posterior queries $P(Q | e) = \alpha \sum_h
     P(Q, e, h)$ by summing joint entries. Exponential complexity $O(d^n)$.
  ● Variable Elimination (VE): Exact inference algorithm using factor operations:
         ○ Factor: Table mapping assignments to positive real numbers.
         ○ Join Product: Combines factors sharing variables via pointwise multiplication.
         ○ Eliminate (Marginalize): Sums out hidden variable from factor.
         ○ Complexity: $O(d^k)$ where $k$ is size of largest factor generated
             (dependent on variable elimination ordering).
  ● D-Separation (Independence): Determines if $X \perp Y \mid Z$. Checks all
     undirected paths between $X$ and $Y$.
         ○ Causal Chain ($A \to B \to C$): Active iff $B$ is unobserved.
         ○ Common Cause ($A \leftarrow B \to C$): Active iff $B$ is unobserved.
         ○ Common Effect / V-Structure ($A \to B \leftarrow C$): Active iff $B$ or any
             descendant of $B$ is observed ("Explaining Away").


### 4.8 Sequential Decision Making: MDPs & Reinforcement
Learning
  ● MDP Tuple: $(S, A, T, R, \gamma)$ with states $S$, actions $A$, transition
     probabilities $T(s,a,s') = P(s'|s,a)$, reward function $R(s,a,s')$, and discount factor
     $\gamma \in [0,1)$.
  ● Utilities & Discounting: Utility of reward sequence $[r_0, r_1, r_2, \dots] =
     \sum_{t=0}^{\infty} \gamma^t r_t \le \frac{R_{\max}}{1 - \gamma}$.
  ● Value Iteration: Dynamic programming algorithm updating state values iteratively
     until convergence ($\max_{s} |V_{k+1}(s) - V_k(s)| < \epsilon$):
     |---|\sum_{s'} T(s,a,s') \left[ R(s,a,s') + \gamma V_k(s') \right]$$


---

  ● Policy Iteration: Alternates two steps until policy stabilizes:
         a. Policy Evaluation: Solve linear system $V^{\pi}(s) = \sum_{s'} T(s, \pi(s), s')
             [R(s, \pi(s), s') + \gamma V^{\pi}(s')]$.
         b. Policy Improvement: $\pi_{new}(s) = \arg\max_{a \in A} \sum_{s'} T(s,a,s')
             [R(s,a,s') + \gamma V^{\pi}(s')]$.
  ● Model-Based RL: Estimates empirical transition model $T(s,a,s') =
     \frac{N(s,a,s')}{N(s,a)}$ and reward model $R(s,a,s')$, then solves estimated MDP via
     Value Iteration.
  ● Model-Free RL:
         ○ First-Visit Monte Carlo: Averages total empirical returns following first visit to
             state $s$ across sampled episodes.
         ○ Temporal Difference (TD) Learning: On-policy update following transition $(s, a,
             s', r)$:
             $$V(s) \leftarrow V(s) + \alpha \left[ r + \gamma V(s') - V(s) \right]$$
         ○ Tabular Q-Learning: Off-policy TD update for state-action values $Q(s,a)$:
             $$Q(s,a) \leftarrow Q(s,a) + \alpha \left[ r + \gamma \max_{a'} Q(s', a') - Q(s,a)
             \right]$$
  ● Exploration vs. Exploitation:
         ○ $\epsilon$-Greedy: Selects random action with probability $\epsilon$, greedy
             action $\arg\max_a Q(s,a)$ with probability $1 - \epsilon$.
         ○ Exploration Function: Replaces $Q(s',a')$ with $f(u, n) = u + \frac{k}{n}$ inside
             Q-update equation, favoring under-explored state-action pairs.


### 4.9 Probabilistic Learning
  ● Maximum Likelihood Estimation (MLE): Choose parameters $\theta$ maximizing
     log-likelihood of observed data $D$:
     $$\theta_{MLE} = \arg\max_{\theta} \log P(D \mid \theta)$$
     For coin toss with $\alpha_H$ heads and $\alpha_T$ tails: $\theta_{MLE} =
     \frac{\alpha_H}{\alpha_H + \alpha_T}$.
  ● Maximum A Posteriori (MAP): Incorporates prior distribution $P(\theta)$:
     $$\theta_{MAP} = \arg\max_{\theta} \left[ \log P(D \mid \theta) + \log P(\theta)
     \right]$$
  ● Naïve Bayes Classifier: Assumes features $F_1, \dots, F_n$ are conditionally
     independent given class label $Y$:
     $$P(Y \mid F_1, \dots, F_n) \propto P(Y) \prod_{i=1}^{n} P(F_i \mid Y)$$
  ● Laplace Smoothing: Prevents zero probabilities for unseen features by adding
     pseudo-counts $k$:
     $$P(F_i = f \mid Y = c) = \frac{c(f, c) + k}{c(c) + k \cdot |D_{F_i}|}$$
  ● Expectation-Maximization (EM): Iterative optimization for latent variable models:
         ○ E-Step: Compute expected soft counts / probabilities of unobserved latent
             variables $Z$ given current parameters $\theta^{(t)}$.


---

         ○ M-Step: Update parameters $\theta^{(t+1)}$ via MLE on expected soft counts.
  ● BN Structure Learning: Optimizes DAG topology by maximizing penalised likelihood
     score $Score(G) = \log P(D \mid G, \theta_{MLE}) - Penalty(G)$ to penalize model
     complexity.


## 5. Mathematical Foundations and Depth

### 5.1 Search Metrics & Heuristic Conditions
  ● A* Evaluation Function:
     $$f(n) = g(n) + h(n)$$
  ● Admissibility Condition:
     $$\forall n, \quad 0 \le h(n) \le h^*(n)$$
  ● Consistency Condition:
     $$\forall s, a, s', \quad h(s) \le c(s, a, s') + h(s')$$
  ● Monotonicity Property:
     $$f(s') = g(s') + h(s') = g(s) + c(s,a,s') + h(s') \ge g(s) + h(s) = f(s)$$
  ● Effective Branching Factor Equation:
     $$N + 1 = \sum_{i=0}^{d} (b^)^i = \frac{(b^)^{d+1} - 1}{b^* - 1}$$


### 5.2 Constraint Satisfaction Equations
  ● Arc Consistency Condition ($X \to Y$):
     $$\forall x \in D_X, \quad \exists y \in D_Y \quad \text{such that} \quad (x, y) \in
     C_{XY}$$


### 5.3 Adversarial Decision Equations
  ● Minimax Recursion:
     $$V(s) = \begin{cases} Utility(s) & \text{if } Terminal(s) \ \max_{a \in A(s)}
     V(Result(s,a)) & \text{if } Player(s) = MAX \ \min_{a \in A(s)} V(Result(s,a)) & \text{if }
     Player(s) = MIN \end{cases}$$
  ● Expectimax Value:
     $$V_{exp}(s) = \sum_{s'} P(s' \mid s, a) V(s')$$
  ● UCT Selection Formula (MCTS):
     $$UCT(n) = \frac{W(n)}{N(n)} + C \cdot \sqrt{\frac{\ln N(Parent(n))}{N(n)}}$$


---

### 5.4 Probability & Bayesian Network Equations
  ● Bayes' Rule:
     $$P(A \mid B) = \frac{P(B \mid A) P(A)}{P(B)} = \frac{P(B \mid A) P(A)}{\sum_{a} P(B
     \mid A = a) P(A = a)}$$
  ● Bayesian Network Factorization:
     $$P(X_1, \dots, X_n) = \prod_{i=1}^{n} P(X_i \mid Parents(X_i))$$
  ● Factor Pointwise Product (Joining $f_1(A,B)$ and $f_2(B,C)$):
     $$f_3(A, B, C) = f_1(A, B) \cdot f_2(B, C)$$
  ● Factor Marginalization (Eliminating variable $B$):
     $$f_4(A, C) = \sum_{b \in D_B} f_3(A, B = b, C)$$


### 5.5 MDP & Reinforcement Learning Equations
  ● Bellman Optimality Equation for $V^*(s)$:
     $$V^(s) = \max_{a \in A} \sum_{s'} T(s,a,s') \left[ R(s,a,s') + \gamma V^(s') \right]$$
  ● Bellman Optimality Equation for $Q^*(s,a)$:
     $$Q^(s,a) = \sum_{s'} T(s,a,s') \left[ R(s,a,s') + \gamma \max_{a'} Q^(s',a') \right]$$
  ● Relation Between $V^(s)$ and $Q^(s,a)$:
     $$V^(s) = \max_{a \in A} Q^(s,a)$$
  ● Policy Extraction Formula:
     $$\pi^(s) = \arg\max_{a \in A} \sum_{s'} T(s,a,s') \left[ R(s,a,s') + \gamma V^(s')
     \right]$$
  ● TD(0) State Update:
     $$V(s) \leftarrow (1 - \alpha) V(s) + \alpha \left[ r + \gamma V(s') \right]$$
  ● Tabular Q-Learning Sample Update:
     $$Q(s,a) \leftarrow (1 - \alpha) Q(s,a) + \alpha \left[ r + \gamma \max_{a'} Q(s',a')
     \right]$$


### 5.6 Probabilistic Learning Derivations
  ● Coin Flip Log-Likelihood Function:
     $$\mathcal{L}(\theta) = \log P(D \mid \theta) = \alpha_H \log \theta + \alpha_T \log
     (1 - \theta)$$
  ● MLE Derivative and Root:
     $$\frac{\partial \mathcal{L}}{\partial \theta} = \frac{\alpha_H}{\theta} -
     \frac{\alpha_T}{1 - \theta} = 0 \implies \theta_{MLE} = \frac{\alpha_H}{\alpha_H +
     \alpha_T}$$
  ● Naïve Bayes Posteriors Ratio:
     $$\frac{P(Y = c_1 \mid F)}{P(Y = c_2 \mid F)} = \frac{P(Y = c_1)}{P(Y = c_2)}
     \prod_{i=1}^{n} \frac{P(F_i \mid Y = c_1)}{P(F_i \mid Y = c_2)}$$


---

## 6. Algorithms and Implementation Methods

### 6.1 Uninformed Graph Search
def general_graph_search(problem, frontier_data_structure):


  # frontier_data_structure defines expansion order (FIFO, LIFO, PriorityQueue)


  start_node = Node(state=problem.initial_state, path_cost=0)


  frontier = frontier_data_structure


  frontier.push(start_node)


  explored = set()


  while not frontier.is_empty():


    node = frontier.pop()


    if problem.is_goal(node.state):


      return node.path()


    if node.state not in explored:


      explored.add(node.state)


      for action in problem.actions(node.state):


         child_state = problem.result(node.state, action)


         cost = node.path_cost + problem.step_cost(node.state, action, child_state)


         child_node = Node(state=child_state, parent=node, action=action, path_cost=cost)


         frontier.push(child_node)


  return Failure


---

### 6.2 A* Graph Search
n
def a_star_graph_search(problem, heuristic):
start_node = Node(state=problem.initial_state, path_cost=0)
frontier = PriorityQueue(key=lambda node: node.path_cost + heuristic(node.state))
frontier.push(start_node)
explored = set()while not frontier.is_empty():


     node = frontier.pop()


     if problem.is_goal(node.state):


       return node.path()


     if node.state not in explored:


       explored.add(node.state)


       for action in problem.actions(node.state):


         child_state = problem.result(node.state, action)


         g_cost = node.path_cost + problem.step_cost(node.state, action, child_state)


         child_node = Node(state=child_state, parent=node, action=action, path_cost=g_cost)


         frontier.push(child_node)


return Failur
e


## 6.3 CSP Backtracking with AC-3 Inference


```python


def ac3(csp, queue=None):


     if queue is None:


       queue = [(X_i, X_j) for X_i in csp.variables for X_j in csp.neighbors[X_i]]


---

  while queue:


    (X_i, X_j) = queue.pop(0)


    if revise(csp, X_i, X_j):


       if len(csp.domains[X_i]) == 0:


         return False


       for X_k in csp.neighbors[X_i] - {X_j}:


         queue.append((X_k, X_i))


  return True


def revise(csp, X_i, X_j):


  revised = False


  for x in set(csp.domains[X_i]):


    if not any(csp.satisfies_constraint(x, y) for y in csp.domains[X_j]):


       csp.domains[X_i].remove(x)


       revised = True


  return revised


def backtracking_search(csp):


  return backtrack({}, csp)


def backtrack(assignment, csp):


  if len(assignment) == len(csp.variables):


    return assignment


  var = select_unassigned_variable(assignment, csp) # MRV + Degree Heuristic


---

  for value in order_domain_values(var, assignment, csp): # LCV Heuristic


    if csp.is_consistent(var, value, assignment):


       assignment[var] = value


       inferences = forward_checking_or_ac3(csp, var, value)


       if inferences != Failure:


         result = backtrack(assignment, csp)


         if result != Failure:


            return result


       del assignment[var]


       restore_domains(csp, inferences)


  return Failure


### 6.4 Alpha-Beta Pruning
def alpha_beta_decision(state):


  v, best_action = -inf, None


  alpha, beta = -inf, inf


  for action in state.actions():


    v_child = min_value(state.result(action), alpha, beta)


    if v_child > v:


       v = v_child


       best_action = action


    alpha = max(alpha, v)


---

  return best_action


def max_value(state, alpha, beta):


  if state.is_terminal():


    return state.utility()


  v = -inf


  for action in state.actions():


    v = max(v, min_value(state.result(action), alpha, beta))


    if v >= beta:


       return v # Beta cutoff


    alpha = max(alpha, v)


  return v


def min_value(state, alpha, beta):


  if state.is_terminal():


    return state.utility()


  v = inf


  for action in state.actions():


    v = min(v, max_value(state.result(action), alpha, beta))


    if v <= alpha:


       return v # Alpha cutoff


    beta = min(beta, v)


  return v


---

### 6.5 Variable Elimination (Bayesian Networks)
def variable_elimination(query_var, evidence, bn, elimination_order):


  factors = [make_factor(var, evidence) for var in bn.variables]


  hidden_vars = [v for v in elimination_order if v != query_var and v not in evidence]


  for var in hidden_vars:


    mentioning_factors = [f for f in factors if var in f.vars]


    if mentioning_factors:


      joined_factor = join_all(mentioning_factors)


      eliminated_factor = joined_factor.sum_out(var)


      factors = [f for f in factors if f not in mentioning_factors] + [eliminated_factor]


  final_factor = join_all(factors)


  return final_factor.normalize()


### 6.6 Value Iteration and Tabular Q-Learning
def value_iteration(mdp, gamma, epsilon):


  V = {s: 0.0 for s in mdp.states}


  while True:


    delta = 0


    V_new = V.copy()


    for s in mdp.states:


      if mdp.is_terminal(s):


         continue


---

      max_q = max(


          sum(T * (R + gamma * V[s_prime])


             for s_prime, T, R in mdp.transitions(s, a))


          for a in mdp.actions(s)


      )


      V_new[s] = max_q


      delta = max(delta, abs(V_new[s] - V[s]))


    V = V_new


    if delta < epsilon:


      break


  return V


def q_learning(env, num_episodes, alpha, gamma, epsilon):


  Q = defaultdict(float)


  for episode in range(num_episodes):


    s = env.reset()


    while not env.is_terminal(s):


      if random.random() < epsilon:


          a = random.choice(env.actions(s))


      else:


          a = max(env.actions(s), key=lambda act: Q[(s, act)])


      s_prime, r = env.step(a)


---

                                                       max_next_q = max([Q[(s_prime, a_p)] for a_p in env.actions(s_prime)], default=0.0)


                                                       Q[(s, a)] = Q[(s, a)] + alpha * (r + gamma * max_next_q - Q[(s, a)])


                                                       s = s_prime


                                                  return Q


                                                7. Permitted Methods, Reasonable
                                                Variations, and Scope Boundaries
                                                     ● Target Execution Environment: Linux Ubuntu systems running standard Python 3
                                                        interpreter. Automated grading scripts execute strictly on Ubuntu machines.
                                                     ● Data Structure Standard Variations:
                                                             ○ Graph Search vs. Tree Search: In graph search, closed sets (hash tables) track
                                                                visited states. Node tie-breaking in priority queues must remain deterministic
                                                                to ensure reproducibility across script runs.
                                                             ○ In-Place Dynamic Programming: Value Iteration can be executed using two
                                                                tables ($V_k$ and $V_{k+1}$) or via asynchronous in-place updates. In-place
                                                                updates converge faster and are explicitly permitted.
                                                     ● Constraint Satisfaction Methods: Forward Checking and AC-3 constraint propagation
                                                        can be interleaved with backtracking search. Dynamic variable ordering (MRV +
                                                        Degree) is preferred over static ordering.
                                                     ● Adversarial Search Variations: Standard Alpha-Beta Pruning relies on exact depth
                                                        cutoffs. Transposition tables (hash tables storing evaluated subtrees) and iterative
                                                        deepening ordering are valid efficiency enhancements.
                                                     ● Reinforcement Learning Variants:
                                                             ○ Tabular Q-learning uses either an explicit $\epsilon$-greedy schedule or an
                                                                exploration function bonus $f(u, n) = u + k/n$.
                                                             ○ Both First-Visit and Every-Visit Monte Carlo implementations fall within
                                                                standard model-free evaluation paradigms.


## 8. Algorithm and Concept Reference Table
Algorithm / Concept   Problem Domain      Time Complexity                      Space Complexity                      Optimality Conditions       Completeness                   Key Parameters / Heuristics

BFS                   Uninformed Search   $O(b^d)$                             $O(b^d)$                              Unit step costs             Yes (if $b$ finite)            FIFO Queue

DFS                   Uninformed Search   $O(b^m)$                             $O(bm)$                               Non-optimal                 No (in infinite state space)   LIFO Stack


---

Algorithm / Concept    Problem Domain          Time Complexity                    Space Complexity                    Optimality Conditions             Completeness   Key Parameters / Heuristics

IDS                    Uninformed Search       $O(b^d)$                           $O(bd)$                             Unit step costs                   Yes            Depth limit iteration $l$

UCS                    Uninformed Search       $O(b^{1 + \lfloor C^* / \epsil…    $O(b^{1 + \lfloor C^* / \epsilon    Step costs $c \ge \epsilon > 0$   Yes            Priority Queue on $g(n)$
                                                                                  \rfloor})$

A* Search              Informed Search         Exponential in $d$                 Exponential in $d$                  Tree: Admissible $h$; Graph:      Yes            Priority Queue on $f(n) = g(n) +
                                                                                                                      Consistent $h$                                   h(n)$

IDA*                   Informed Search         Exponential in $d$                 $O(bd)$                             Tree: Admissible $h$              Yes            $f$-value threshold limit

Backtracking + AC-3    CSP                     $O(d^n)$                           $O(n \cdot d)$                      Complete assignment satisfying    Yes            MRV, Degree, LCV heuristics,
                                                                                                                      $C$                                              AC-3 ($O(n^2 d^3)$)

Hill-Climbing          Discrete Optimization   Depends on landscape               $O(1)$                              Non-optimal (Local Optima)        No             Next-step neighbor evaluation

Minimax                Zero-Sum Games          $O(b^m)$                           $O(bm)$                             Against optimal opponent          Yes            Terminal utilities

Alpha-Beta Pruning     Zero-Sum Games          Best: $O(b^{m/2})$; Worst: …       $O(bm)$                             Identical to Minimax              Yes            $\alpha, \beta$ bounds, move
                                                                                                                                                                       ordering

Expectimax             Stochastic Games        $O(b^m)$                           $O(bm)$                             Max expected utility              Yes            Chance node probability
                                                                                                                                                                       weighting

MCTS (UCT)             Large Games / Go        Dependent on budget                $O(\text{Nodes in tree})$           Asymptotically optimal            Yes            UCT constant $C$, Playout policy

Variable Elimination   Bayes Net Inference     $O(d^k)$ ($k$ = max factor …       $O(d^k)$                            Exact posterior probability       Yes            Min-fill, Min-neighbors ordering

Value Iteration        MDP                     $O(                                S                                   ^2                                A              )$ per iteration

Q-Learning             Model-Free RL           Dependent on sampling              $O(                                 S                                                A

Naïve Bayes            Classification          $O(N \cdot                         F                                   )$                                $O(            Y


## 9. Techniques Not Established as In Scope
                                                     To maintain absolute academic integrity and focus strictly on covered content, the following
                                                     advanced topics are out of scope:


                                                          ● Deep Reinforcement Learning: Deep Q-Networks (DQN), Policy Gradient methods
                                                             (PPO, TRPO, A3C) beyond high-level mention of neural evaluation functions in
                                                             AlphaGo.


---

   ● Continuous State MDPs & Control: Continuous state/action spaces, Kalman Filters,
       Particle Filters, LQR controllers.
   ● Partially Observable MDPs (POMDPs): Belief state tracking spaces, POMDP value
       iteration trees.
   ● First-Order Logic & Theorem Proving: Unification, Resolution Refutation, First-Order
       Inference, Prolog engines.
   ● Deep Neural Architectures: Backpropagation algorithms, Convolutional Networks
       (CNNs), Recurrent Networks (RNNs), Transformers, Attention Mechanisms.
   ● Complex CSP Algorithms: General $k$-consistency solvers ($k > 3$), Tree-structured
       CSP reduction via directional arc consistency.


## 10. Ambiguities and Missing Evidence
The following implementation nuances are left discretionary by the lecture slides and must
be resolved cleanly by code developers:


   ● Tie-Breaking Mechanisms: Slide materials do not specify exact tie-breaking rules for
       equal $f(n)$ values in A*, equal $Q(s,a)$ values in Q-learning, or equal variable/value
       heuristic scores in CSPs. Standard practice mandates deterministic tie-breaking (e.g.,
       lexicographical order on state/variable labels) to preserve reproducible autograder
       behavior.
   ● Convergence Thresholds in Value Iteration: The stopping condition parameter
       $\epsilon$ for Value Iteration ($\max_s |V_{k+1}(s) - V_k(s)| < \epsilon$) is left
       task-dependent.
   ● MCTS Playout Depth Limits: Rollout termination rules in MCTS simulations are left
       open (either full random playout to terminal states or bounded rollout with evaluation
       function substitution).
   ● Structure Learning Penalty Scaling: The exact mathematical weight of the model
       complexity penalty function $Penalty(G)$ in Bayesian Network structure learning is
       not fixed.


## 11. Instructions for AI Assistants Solving
Assignments
When an AI coding assistant (e.g., Gemini, Copilot, ChatGPT) is tasked with writing,
debugging, or optimizing code for assignments in this course, it must adhere strictly to the
following directives:


## 1. Target Operating System & Runtime: All Python scripts must be strictly compatible
       with Python 3 on Ubuntu Linux environments. Do not use OS-specific Windows calls
       or non-standard external software libraries unless explicitly requested.


---

## 2. Interface Format Compliance: Standardized automated scripts evaluate submissions
    on Ubuntu machines. Even minor violations in input/output command-line
    arguments, API parameters, or returned tuple signatures will fail automated
    evaluation scripts, leading to score deductions.
## 3. Plagiarism & Academic Integrity:
        ○ Assignments must represent original code constructed from scratch.
        ○ "Cognitive offloading" of entire assignment logic to GenAI without
             understanding violates the institute honor code.
        ○ Plagiarism or code sharing results in zero marks for the assignment and an
             absolute scale penalty (at least -10 absolute marks) along with institute
             disciplinary proceedings (DISCO / F-grade).
## 4. Deterministic Implementation Practices: Always incorporate explicit tie-breaking
    rules for priority queues, set iterations, and search frontiers to ensure deterministic
    program execution during autograding test suite runs.
## 5. Memory Constraints: Strictly maintain closed lists (hash sets) in graph search to
    avoid memory explosions. Use linear-space variants (e.g., IDA*, DFS) when memory
    bounds are tight.


## 12. Source Index with Lecture and Page
References
 ● [source: 1] (L01-Course-Overview.pdf): Course structure, credits, evaluation
    criteria (Theory ~55%, Practical ~35%, Quiz ~10%), Pass/Audit criteria, Python 3 /
    Ubuntu assignment rules, Moodle guidelines, Honor code violations & DISCO penalty
    scale.
 ● [source: 5] (L02-Introduction.pdf): Definitions of AI, Turing Test, Rational Agents,
    PEAS breakdown, Environment characteristics (Discrete/Continuous, Static/Dynamic,
    Deterministic/Stochastic), Modeling-Inference-Learning paradigm.
 ● [source: 6] (L03-Problem-Solving-As-Search-Uninformed.pdf): Search
    formulation components, State Space Graphs vs. Search Trees, Frontier operations,
    Loop handling & explored sets, BFS, DFS, DLS, IDS, UCS (Dijkstra), Beam Search,
    Bi-directional search, Time/Space summary table.
 ● [source: 2] (L04-Constraint-Satisfaction.pdf): CSP definition $(X,D,C)$,
    Constraint Graph, Map Coloring / Sudoku modeling, Backtracking algorithm, MRV
    Heuristic, Degree Heuristic, LCV Heuristic, Forward Checking, Arc Consistency (AC-3,
    $O(n^2 d^3)$ complexity), K-Consistency.
 ● [source: 4] (L05-Local-Search-Algorithms.pdf): Discrete optimization framing,
    Cost vs. Evaluation functions, Hill-Climbing algorithm, 4-Queens local moves, Local
    minima/plateaus, Local Beam Search ($k$ states), Stochastic Beam Search, Random
    Restarts, Random Walks.


---

● [source: 3] (L06-Goal-Informed-Search.pdf): Best-First Search, Greedy Best-First
   Search, A* Search formulation ($f = g + h$), Admissibility ($h \le h^$), Consistency
   ($h(s) \le c(s,a,s') + h(s')$), Heuristic Dominance, Combining heuristics via Max,
   Effective Branching Factor ($b^$), IDA* algorithm.
● [source: 9] (L07-Modeling-Uncertainty.pdf): Random variables, Joint Probability
   Distributions, Marginalization, Conditioning, Inference by Enumeration, Chain Rule,
   Bayes' Rule, Conditional Independence, Sampling methods.
● [source: 12] (L08-Markov-Decision-Processes.pdf): Sequential decision making
   under uncertainty, MDP tuple $(S,A,T,R,\gamma)$, Policy $\pi(s)$, Discounting,
   Bellman Optimality Equations for $V^$ and $Q^$, Value Iteration algorithm, Policy
   Iteration (Evaluation & Improvement).
● [source: 8] (L09-Reinforcement-Learning-II.pdf): Active/Passive RL,
   Model-Based RL, Model-Free RL, First-Visit Monte Carlo evaluation, Temporal
   Difference TD(0) learning, Tabular Q-learning algorithm, Exploration vs. Exploitation
   ($\epsilon$-greedy, Exploration Function $f(u,n)$).
● [source: 10] (L10-Adversarial-Search.pdf): Game theory definitions, Minimax
   algorithm, Alpha-Beta Pruning ($\alpha, \beta$ bounds, best-case $O(b^{m/2})$
   complexity), Depth-limited search with evaluation functions, Expectimax search,
   Monte Carlo Tree Search (Selection, Expansion, Simulation, Backpropagation, UCT
   formula).
● [source: 11] (L11-Bayesian-Networks.pdf): Directed Graphical Models
   semantics, Factorization equation, Inference by Enumeration, Variable Elimination
   (VE) algorithm, Factor operations (Join, Marginalize), Elimination ordering heuristics
   (Min-fill, Min-neighbors), D-separation rules (Causal chain, Common cause, Common
   effect / Explaining away).
● [source: 7] (L12-Probabilistic-Learning.pdf): Parameter estimation, Maximum
   Likelihood Estimation (MLE), Maximum A Posteriori (MAP), Naïve Bayes model,
   Laplace smoothing ($k$-smoothing), Expectation-Maximization (EM) algorithm,
   Bayes Net structure search with complexity penalties.


---
