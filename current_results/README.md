# current_results/

Everything about the **current promoted model** (the `Agent1` we would
submit right now) and nothing about trial ideas.

| file | what | updated by |
|---|---|---|
| `STRATEGY.md` | how the model plays, in plain words | hand |
| `SUMMARY.md` | W/D/L, goals, averaged telemetry, per-match table, replay names | script |
| `match_stats.csv` | one row per match (from `runlogs/history.csv`) | script |
| `reports/*.txt` | full `match_report.py` output per match: goal stories, planned-vs-actual, per player | script |
| `model_agent.py` | the model's code (`agent.py` with experiment classes stripped) | script |
| `CONTEXT.md` | copy of the project context, including the full experiment log | script |

## Rule

Update this folder **only when a new version replaces Agent1**:

```
python3 scripts/batch.py --tag vX.Y --name VX -n 8 -j 3   # evaluate it
python3 scripts/publish_current.py --tag vX.Y            # promote it
```

then edit `STRATEGY.md` by hand. Trial or experiment runs (`--left :AgentBus`,
exploratory tags) are never published here. They only go in `CONTEXT.md` §7.

Current: **v1.3**.
