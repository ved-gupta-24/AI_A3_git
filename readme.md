# COL333: Introduction to Artificial Intelligence — Assignment 3

## 1. Student Information
- **Name**: Vedant Gupta
- **Entry Number**: 2024CS10384

---

## 2. AIMA Textbook Reference & Zero-Token Knowledge System

The repository includes `AIMA.pdf` (*Artificial Intelligence: A Modern Approach*, 4th Edition) as a comprehensive theoretical reference for algorithmic extensions. In accordance with assignment regulations, student agents must strictly adhere to the concepts covered in the COL333 course syllabus (Lectures L01–L12) and their standard textbook extensions—such as Minimax, Alpha-Beta pruning, heuristic linear evaluation functions, quiescence search, MCTS (UCT), and budget-aware beam search—while strictly avoiding out-of-scope frameworks like Deep Reinforcement Learning, neural networks, genetic algorithms, or `scipy` optimizers.

To enable coding agents and developers to look up algorithms, pseudocode, and mathematical formulations without consuming large context windows or token budgets, a zero-token offline knowledge system is provided:
- **[docs/aima_index.md](docs/aima_index.md)**: A complete matrix mapping course lectures directly to exact AIMA chapters and page numbers with strict compliance boundaries.
- **[docs/aima_references/](docs/aima_references/)**: Pre-distilled algorithmic reference sheets:
  - [adversarial_search_and_games.md](docs/aima_references/adversarial_search_and_games.md): Minimax, Alpha-Beta, Quiescence, Cutoffs, MCTS/UCT, and Expectimax.
  - [heuristic_and_realtime_search.md](docs/aima_references/heuristic_and_realtime_search.md): Budget-aware Iterative Deepening Search, Beam Search, and Continuous Action Discretization.
- **[scripts/query_aima.py](scripts/query_aima.py)**: Fast, offline CLI search tool running locally on CPU. It indexes the book in `.cache/aima_index.json` and returns targeted snippets in <0.1s with zero API token cost.

### Example Usage Script

#### CLI Search
```bash
# 1. Search for allowed concepts within course syllabus (instant, 0 API tokens):
python3 scripts/query_aima.py "quiescence search"
python3 scripts/query_aima.py "monte carlo tree search"
python3 scripts/query_aima.py "evaluation function" --max-results 3

# 2. View full page content by page number:
python3 scripts/query_aima.py --page 209

# 3. Guardrail check (warns if a technique is outside the course syllabus):
python3 scripts/query_aima.py "deep q-network"
```

#### Programmatic Query Example
```python
import subprocess

def query_textbook(topic: str, max_results: int = 2) -> str:
    """Query AIMA.pdf offline without spending LLM tokens."""
    res = subprocess.run(
        ["python3", "scripts/query_aima.py", topic, "-n", str(max_results)],
        capture_output=True,
        text=True,
        check=True
    )
    return res.stdout

if __name__ == "__main__":
    print(query_textbook("alpha beta"))
```

---

## 3. Environment & Simulator Setup

For full instructions on simulator binaries, gRPC stub generation, and match diagnostics, refer to the original starter documentation: **[README_STARTER.md](README_STARTER.md)**.

Quick summary:
```bash
# Activate environment & check system readiness
source .venv/bin/activate
python3 a3.py doctor

# Run a match against the baseline
python3 a3.py match STARTER FULL --right full
```
