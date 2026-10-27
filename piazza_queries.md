# Piazza Queries — COL333 Assignment 3

> **Source:** Screenshots of the Piazza post **“A3 Discussion Thread”** (note #32), captured on 27 October 2026.
>
> **Coverage note:** This document records only the questions, replies, and updates legible in the supplied screenshots. The thread shows **23 follow-up discussions**, but the screenshots do not capture all 23 in full. Treat this as a partial compilation, not a complete export of the thread.

## 1. Official assignment-thread instructions and updates

The post author asks students to keep Assignment 3 queries in follow-ups to this thread, check existing follow-ups before posting to avoid duplicates, and mark doubts unresolved until a TA responds. After a TA response, the follow-up should be marked resolved; if the answer is insufficient or further doubts remain, reply in that follow-up and mark it unresolved again.

### Update — 15 October, 12:00 PM
- Starter code is available on GitHub.
- Students who downloaded the Linux scripts earlier are advised to redo setup because a silent file-copying error may have changed agent behaviour.

### Update — 25 October, 1:00 PM
- The tackle docstring was corrected.
- Sideways tackles are **half the strength of a straight-ahead tackle**.
- Tackle power is zero for a backward tackle and increases linearly with the angle, reaching its maximum when tackling straight ahead.

## 2. Questions and clarifications visible in the screenshots

### Query 1 — Evaluation opponents and intermediate baselines
**Status shown:** Resolved  
**Question:** A student notes that the Starter opponent is easy to beat while FULL is much stronger than a student agent can reasonably build, making FULL-only testing less informative. They ask whether one or two intermediate opponents could be provided and what opponent strength Phase 1 evaluation would use.

**TA response — Arunabh Roy:**
- Starter is starter code, not a reference opponent.
- Students should iteratively improve their own bots and analyse metrics beyond the final scoreline, such as chance creation, possession, passes, and self-play.

**Practical takeaway:** Use multiple diagnostics and self-play while developing; do not rely only on wins/losses against Starter or FULL.

### Query 2 — Meaning of a second tie-breaker
**Status shown:** Unresolved in the screenshot  
**Question:** “Can you please describe a situation where 2nd tie breaker is used to break the tie?”

**Clarification:** No answer to this question is visible in the supplied screenshots. It should remain marked as **unanswered in the available evidence**, rather than assumed resolved.

### Query 3 — How bot evaluation and scoring work
**Status shown:** Resolved  
**Question:** How will the bot be judged against the TA baseline bot? How many matches will be played to reduce variance, and how will scores be calculated?

**TA response — Arunabh Roy:**
- `k` best-of-3 matches will be used.
- Each best-of-3 outcome will receive a weight based on the bot.
- Exact weighting details will be disclosed when grades are released.
- Students can assume that marks are weighted reasonably by opponent difficulty and wins.

**Practical takeaway:** Expect multiple best-of-3 series per bot and difficulty-dependent weighting. The exact number of series and score formula are not specified in the visible replies.

### Query 4 — Variance from best-of-3 matches
**Status shown:** Resolved  
**Question/follow-up:** A student worries that best-of-3 series may be too few and produce high variance. They give a hypothetical sequence of series scores and ask whether the overall match outcomes are being considered.

**TA response — Arunabh Roy:**
- Multiple best-of-3 series will be played per bot.
- The intent is to keep the number of matches reasonable while reducing variance and returning results promptly after the first deadline.
- There are no guarantees.
- The TA notes that if bots are genuinely evenly matched, an outcome near 50% may be appropriate.

**Practical takeaway:** The evaluation is not just one best-of-3 series per opponent; multiple series are planned.

### Query 5 — Is FULL one of the TA grading bots, and how are weights assigned?
**Status shown:** Resolved  
**Question:** How is the final score computed across TA bots? Is FULL one of the baseline bots? How many bots are used, how are their weights set, do easier bots count less than harder ones, and do close losses earn points?

**TA response — Arunabh Roy:**
- Exact bot weights will be disclosed when grades are released.
- A reasonable weighting by difficulty and wins can be assumed.

**Unspecified in the visible answer:**
- Whether FULL is one of the actual grading bots.
- The exact number of grading bots.
- Exact weights or points for wins, draws, close losses, or individual best-of-3 game scores.

**Practical takeaway:** Do not treat these unanswered specifics as confirmed. The TA has only confirmed that weighting will account reasonably for difficulty and wins.

### Query 6 — Environment behaviour and tackle implementation
**Status shown:** The screenshot shows a resolved follow-up near the visible end of this discussion; confirm the precise status of each individual issue in Piazza if needed.

A student reports several apparent environment/API behaviours:
- The provided goalie seems unable to move backwards under `rcssserver 19.0.0`; the server clamps backward dash power to zero.
- The keeper appears to catch back-passes, although the student believes catching should be restricted to cases where the kicker is not a teammate.
- Kick-off appears idle for 45 cycles because `teammatesFromSelf` remains below 9.
- A fallback after `kick()` appears to run: when `kick()` cannot meet `accept_late`, it registers a shield kick but returns false, so the proxy runs the next action in the list.
- The `tackle` description in `interface.py` appears inconsistent with observed behaviour.
- Random passes or long-gap shots may cause the keeper to move far forward and allow a later easy goal.
- The student says a ball directly behind a player cannot be tackled because `tackle_back_dist` is zero, and contrasts the documentation's description of tackle force.

**TA response — Arunabh Roy:**
- Most listed behaviours are consequences of the environment and should be treated uniformly for everyone.
- The keeper-backward-movement issue should be considered a uniform environment consequence.
- The TA says the kick-off delay was compensated for by keeping the half length longer than intended.
- The kick fallback described by the student is intended.
- The TA asks for more detail about the `tackle()` issue.
- After the student explains the tackle-force discrepancy, the TA clarifies that “sideways” was intended to mean half the strength of a full straight-ahead tackle, not a backward tackle.
- The TA says the keeper may still move backwards slowly and suggests clearing the ball or sending it out of play to reset the goalkeeper position if the agent could be punished by the behaviour.
- The TA may investigate the keeper-position exploit for the second phase if it is too easily exploited, but does not want to change behaviour close to the fixed component deadline.

**Practical takeaways:**
- Treat environment quirks as shared constraints unless an official update says otherwise.
- Do not assume a keeper-position behaviour will be changed before the deadline.
- Use the corrected tackle semantics from the 25 October update: backward tackle power is zero; sideways is half of straight-ahead strength.

## 3. Confirmed updates to keep in mind

- **Starter setup:** Redo the Linux-script setup if you downloaded it before the 15 October update.
- **Tackling:** Sideways = half straight-ahead strength; backward = zero; power increases linearly with angle up to straight ahead.
- **Evaluation:** Multiple best-of-3 series per bot are planned, with weights based on bot difficulty and wins; exact scoring details are not yet available in the visible replies.
- **Development metrics:** Track chance creation, possession, passing, and self-play, not just the final scoreline.
- **Environment behaviours:** The TA says most reported behaviours are shared environment consequences; the kick fallback is intentional.

## 4. Items not conclusively answered by the screenshots

1. A concrete example of when the second tie-breaker is used.
2. Whether FULL is included among the TA's actual grading bots.
3. The exact number and identities of grading bots.
4. The exact scoring weights and points for wins, draws, close losses, and series outcomes.
5. Whether any reported environment behaviours beyond the tackle docstring will be changed before the deadline.

Check the live Piazza thread for later replies or status changes before relying on these as final.

## 5. Submission/development checklist

- [ ] Redo setup if using an older copy of the Linux scripts.
- [ ] Use the corrected tackle semantics.
- [ ] Evaluate the bot with more than the final scoreline: inspect possession, passes, chance creation, and self-play.
- [ ] Run multiple tests against available opponents; do not infer too much from a single series.
- [ ] Treat unspecified grading details as unknown until an official clarification is posted.
- [ ] Recheck unresolved follow-ups and any new replies before submission.

---
*Prepared from the supplied screenshots; wording has been condensed in places for readability. This is not a verbatim or exhaustive export of all 23 follow-up discussions.*
