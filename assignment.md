# Assignment III: Game Playing AI

# Overview

- This assignment concerns the problem of decision making when there are other agents in the domain. We consider a game setup where there are two teams playing each other. We will implement an AI agent for a team that you are leading that can play with another team (another AI agent).
- We consider the game of football with a small team of five players - in which there are four players that can be controlled and then there is a goal keeper that acts automatically. We will work in a simulated environment where players have a certain number of actions that they can perform and the simulation allows us to see their consequences.The simulated game has some realism with some actual rules implemented. The objective is to score your own goals and defend against goals attempted from the other side. Interestingly, football has has been a topic for study by AI researchers for a number of years. There have been competitions in AI conferences where AI agents (sometimes with real robots) for this game.
- The assignment is closely associated with the game playing AI topic covered in the course. The core learning objective is to learn how to deal with larger action spaces (there are four players in your team) and how to decide the next action to take considering the actions for your team as well as those of the opposing team. Note that the full game is rather complex and hence the simulation environment provides a reduced sandbox to learn the algorithmic aspects.
- **Please start the assignment on time.** The first stage is to get comfortable with the interface and learn to interact with the various aspects of the Actions API (essentially what all can the agents do). Please engage with the starter code and ask any relevant questions early on. Any relevant doubts/clarifications should be posted as a follow-up on the Piazza A3 thread.
- **We hope that the assignment is a good learning experience.** From previous years, students have often enjoyed seeing AI agents play intelligently and autonomously.

# **Getting Started**

- **The starter code is available [here](https://github.com/TheAbry/COL333-Assignment-3-py2d-fork).** Please refer to the repository for the instructions to get the starter code up and running. Please try the following commands.

| `python3 [a3.py](http://a3.py) match`  | to see a match between two starter implementations. |
| --- | --- |
| `python3 [a3.py](http://a3.py) match --right full`  | to see a match between a starter implementation and one of the sample bots that will be used for grading. |

[examplevid.mp4](Assignment%20III%20Game%20Playing%20AI/examplevid.mp4)

*The video above shows the simulation environment where you can run your agent to control a team of players playing with another team.*

- The file you have to edit is `src/student/agent.py`. Please review this file carefully. Please ****also read `src/student/interface.py` in order to understand the provided API and what actions are allowed. Anything outside of the exposed API will be rejected (either at runtime or by manually reading your file). *If you have any doubts or believe you need something else, please ask on Piazza.*
- Please carefully review the available commands in `a3.py`: it is a runner for matches, and can also diagnose issues with environment setup, allow you to analyze your agent’s execution and let you watch the match replays.
- Please only use **standard Python** for this assignment. Please <u>do no</u>t use additional libraries beyond the ones specified in the starter environment (note that despite being in the starter environment, <u>**scipy is not permitted**</u>). Our focus is on algorithmic aspects and less on real time optimisation. In case of a doubt please ask as non-standard implementations stall evaluation.

# **Problem Description**

This assignment considers the game of football between two teams. Each team will have 5 players. Our task is to write an AI agent to control 4 players in your team. One player is designated as the goalkeeper and is automatically (not by your code) controlled. The same is true for the second team which will be controlled by another AI agent. 

## Domain Representation

- The state space is essentially the positions of the players on the ground and the position of the ball. The action space consists of the following basic actions listed below. These actions can be considered as a behaviour that is executed for a certain time. **Please refer to the API in the starter code for further details on these actions.**

|   1.  | Kick the ball  | This action is parameterised by the direction and power. Note that direction is useful and power is less useful.  |
| --- | --- | --- |
| 2.  | Dribble with the ball | This action is parameterised by the direction. |
| 3.  | Hold the ball | This action has no parameters. |
| 4.  | Clear the ball away quickly | This action has no parameters. |
| 5.  | Go to a point | This action is parameterised by the terminal position. |
| 6.  | Intercept the ball | This action has no parameters. |
| 7.  | Tackle | This action is parameterised by the direction. |
- Some of the actions (hold, clear, intercept) do not have any parameters while some require an input such as position or direction. You will control the actions of your team by developing an AI agent in the `Agent` class. It has two functions-
    - `on_ball`: What action to take when you have the ball
    - `off_ball`: What action to take when you don’t have the ball
- Since a player’s position is a point in 2D-space, it is *continuous*. Hence, you might wonder how a search over actions can be feasible? However, semantically there are a limited number of positions to actually consider at a particular moment in time. For this reason, two helper functions are provided:
    - `home_position` → returns the location that the formation says a player should be at
    - `points_around` → samples $n$ points around a central point at a distance of $r$ from it.
- The vast majority of the ground is not helpful to utilise if your teammates are not there (hence, in practice only a few options may be considered in reasoning). We recommend utilising the first function when you do not have the ball to guide a player when no other action like tackling or intercepting is a better choice, and the second function to sample points around various teammates to use as choices for passing locations. Please do analyse the tradeoff of increasing granularity of the sampling versus increase in branching factor, to find the best tradeoff between action quality and latency.

## Other Information

- **A simple opponent team.** The provided `Agent2` in the starter code has players that stand at their positions but do not actively interact. Hence, this agent serves as a very simple  opposing team for you to try your code with. By playing matches with this opposing team, see your agent can **progress the ball and/or score goals past the goalkeeper**. Only after this should you start working on improvements to intercepting / defending and using opponent positions in your strategy.
- **Goalkeeper.** The goalkeeper is controlled automatically, so you do not have to think about it. You may want to try different attacking scenarios to understand the goalkeeper’s positioning so you can understand how to best score against it or help it defend the goal.
- **Other rules.** The underlying simulator is a realistic football simulator. Hence, it has other aspects of the game that are included to make it realistic. Hence, when you take an action and it is simulated then there may be other events that can occur. These include occurrences of: an offside, corner kicks, free kicks, indirect free kicks, kick-offs, throw-ins, goal kicks, fouls, yellow cards and back-passes occur in this game largely as in real football. We explain them briefly below. <u>*The goal is not to get too much into the rules of football but view these events as factors in the environment that affect our reward.*</u>
    - An offside occurs when you pass the ball to a player who is past the last defender. However, it is not an offside if your player is still in your half of the pitch. When an offside occurs, the other team gets a free kick.
    - An indirect free-kick conceded from a back-pass from your defender to the goalkeeper can be hard to defend against, so watch out.
    - Two yellow cards can lead to a player being sent off and hence you having to play a 4 player vs. 5 player game which is disadvantageous for your.
    - There are no penalties in this setup. A foul inside the box concedes an indirect free-kick (which can be hard to defend with 4 players) and may also lead to a card. There will also be no extra time or penalty shootouts to resolve draws; a best-of-3 is played and the criteria specified below are used to tiebreak.
    - You only need to control players during open play; that is, during situations like kick-offs, free kicks or corners, your agent is not even called. These situations are handled automatically.

## Hints for Implementation

- First, formalise a model for the problem by analysing the state and action spaces. Play the game yourself to get an intuition. Then develop a basic implementation that can play against the simple agent provided. Think in the direction of search based approach where your agents considers the various possible actions for the other team.
- Once you have a basic implementation working, work towards efficiency and take into considerations the time limits. The time aspect is described in the next section. Explore ways to find good actions quickly.  Refer to the discussion in class.
- You are encouraged to explore different modeling choices and search methods as well as trade-off that exists in terms of accuracy and efficiency. Please build on the material presented in class. Relaying on algorithms/methods that have a fundamentally different mathematical underpinning is not intended in this assignment and likely to be excluded from evaluation. Further, follow the AI thinking approach of developing a formal model and then solving it efficiently. Hence, approaches that try to hard code solutions often do not work well in practice when they are exposed to varied tests.

## What to Submit?

- Please <u>only</u> submit a single Python file **- agent.py.** Within [**agent.py**](http://agent.py), the `Agent1`  ****class must contain your best implementation which will be evaluated. All other classes you define in the file may be used by you for testing and experimentation, but ensure that the `Agent1` class contains your final submission.
- Please succinctly describe the core ideas of your algorithms in the text file called report.txt
(upto 2 pages in standard 11 point Arial font). The first line of the report should list the
name and entry number of student(s) who submit the assignment.

# **Evaluation Guidelines**

## Time available for taking an action

- Your agent will be called every simulator step for its decision. A match lasts for 1500 steps (so each of your agents needs to take up to 1500 decisions per match).
- The time budget for a match is 75 seconds of CPU time per agent, and a maximum cap of 1 second of wall-clock per decision. If you break this 1 second cap 5 times for a player, that player gets sent off for the rest of the match. If any agent is in a blocking call (a long C-level call) that causes it to take more than 1.5 seconds for a decision (and it does not get stopped by the 1 second cap), it gets disconnected from the match. We provide the time remaining for you in the code (refer to the starter code).
- Each agent runs in a separate process and there is no communication between them.

## Environment

- The Python environment we run your code in will be the exact same as the environment created by the repo. Do not expect any additional packages to be installed.
- Since the machine we run your code on may be different from your local setup, please ensure your algorithm is budget-aware and do not rely on hardcoded constants to adhere to time limits.

## Evaluation Components

Evaluation will include two components - a **Fixed** component and a T**ournament** component as described below. The fixed component aims to assess the agent w.r.t. TA implementations. The second part aims to expose the agent to a rich variety of agents from the class. Note that the tournament is intended more as a way to expose the agents to the diversity of implementations from the class which is less captured in the fixed agent evaluation.  

1. **Fixed Component.** The fixed component will account for **$\approx 70\%$** of the assignment grade. The fixed component will involve playing $k$ head-to-head matches against a number of TA agents (so there will be `num_agents` $\times k$ matches). One of these agents is provided to you. 
2. **Tournament Component.** The tournament part will constitute   **$\approx 30\%$**  of the evaluation. The tournament part will involve a group stage from which 32 agents will progress onto the knockout stage. Every head-to-head / knockout match between agents (two student agents or student agent versus TA agent) is going to be via a best-of-3. In case of a tie, the tiebreaker will be as follows:
    - Higher Goal Difference (Goals Scored - Goals Against)
    - Higher Goals Scored
    - Fewest number of yellow cards received (a direct red card counts as 2.5 yellow cards)
    - Fewest number of fouls committed
    - If it is still tied, we will have to resort to random chance
    
    Every group-stage match will be a one-off round-robin among all agents within a group (the group size will be declared once we ascertain how many submissions are received for the competitive part). A leaderboard will be created for each group, wherein there are 3 points for a win, 1 point for a draw and 0 points for a loss. The top teams from each group will enter the knockout stage. If two teams have the same number of points, the above tie-breaking criteria will again be used.
    

## Two Phase Submission Process

The submission and evaluation for this assignment will be in two phases. 

- The first phase will be evaluated for the fixed part of the evaluation. The submission for phase one is due at **5:00 pm on Thursday, 29th October, 2026.** The submissions received will be evaluated for the fixed evaluation and the agent performance will be available to students.
- The students can then improve their agent in a short time window based on experience and submit the improved agent for the second phase evaluation which will be in the tournament mode. the submission date for phase two will be notified and is likely to be in early November.
- We request a bulk of the work to be done in first phase itself, <u>leaving only refinements and some small improvements</u> for phase 2. Note that other evaluations may overlap with the phase two submission. This format has been adopted this year to allow students to fix some basic errors and the improve the submission with the initial experience.

## Logistics

- **This assignment is to be done individually or in pairs. The choice is entirely yours.** The assignment is intended for all class groups (COL333, COL7333 and AIL7025) enrolled in the course. ****If the assignment is being done in pairs then the partner is to be selected within your class only (not across the class group).
- Late submission for phase I will be accepted till two days after the due date, with a deduction of (10% per day) to be fair to other students who submit on time. Late days are not available for phase II submissions hence please submit on time.
- A **silent period** will be observed starting one day before the due date (from Wednesday, 28th October) till the due date. Here, basic queries (such as starter code, basic assumptions etc.) will not be clarified. This is intended to encourage a regular pacing of the work and avoiding last minute queries to the teaching team (on basic aspects of the assignment). The period close to the due date may only be used to refine your implementation.
- **This assignment will carry ~  $9\%$ weightage overall.** As mentioned, the instructor will provide the final weightage after closure of all assignments.
- **The assignment is to be submitted on Gradescope**. See the “What To Submit” section for the description of the submission package and other guidelines to upload.

## Other Notes

- Please follow the assignment guidelines. Failure to do so would cause exclusion from assessment and award of a reduction. Please strictly **adhere** to the input/output syntax specified in the assignment as the submissions are processed using scripts. Please do not modify files beyond the files you are supposed to modify. Failure to do so would cause exclusion from assessment/reduction.
- Queries (if any) should be raised on **Piazza**. Please keep track of Piazza posts. Any updates to the assignment statement will be discussed over Piazza. Please do not use email or message on Teams for assignment queries.
- **Please only submit work from your own efforts.** Do not look at or refer to code written by anyone else. You may discuss the problem, however the code implementation must be original. Discussion will not be grounds to justify software plagiarism. Please do not copy existing assignment solutions from the internet or take them from past submissions / submissions from other students; your submission will be compared against them using plagiarism detection software. Violations to the honour code will result in deductions as per course and institute policies.
- The solution to this exercise can be developed from your own thinking and analysis based on the material covered in class. Please refrain from cognitive offloading to GenAI tools as they take away the opportunity to fundamentally learn and may give a false impression of learning; which is likely to be detrimental in the long run. **The learning expected via this assignment may be included in other evaluation components within the course.**
- Solutions based on **fundamentally different mathematical principles that are beyond the scope of this course are not expected and will not be graded.** You may use algorithms covered in the course, as well as variations of those algorithms.

---