# Your agent goes here. The Agent1 class must hold your final submission.

from pyrusgeom.geom_2d import Sector2D, Vector2D
from src.student.interface import StarterAgent, Action, Tools, note


class Agent1(StarterAgent):
    """
    Modular, budget-aware football AI agent for COL333.
    Subclasses StarterAgent with clean, isolated sub-handlers.
    """
    def __init__(self):
        super().__init__()

    # =========================================================================
    # 1. PRIMARY DISPATCHERS
    # =========================================================================

    def on_ball(self, agent) -> None:
        """
        Called once per cycle when wm.self.is_kickable is True.
        Action Priority: Shoot -> Pass -> Dribble -> Hold -> Clear.
        """
        if self.try_shoot(agent):
            return
        if self.try_pass(agent):
            return
        if self.try_dribble(agent):
            return
        
        # Fallback: shield or clear under pressure
        opps = [o for o in agent.wm.opponents if o.uniform_number > 0]
        nearest_opp_dist = min((o.dist_from_self for o in opps), default=1000.0)
        if nearest_opp_dist > self.COMFORT:
            Action.hold(agent)
            return
        Action.clear(agent)

    def off_ball(self, agent) -> None:
        """
        Called once per cycle when wm.self.is_kickable is False (~95% of cycles).
        Action Priority: Tackle/Intercept -> Block passing/shooting lane -> Return to formation.
        """
        if self.try_intercept_or_tackle(agent):
            return
        if self.try_defensive_block(agent):
            return
        
        # Formation anchor: navigate to tactical slot with stamina-conserving dash power
        Action.go_to_point(agent, Tools.home_position(agent), max_dash_power=self.dash_power(agent))

    # =========================================================================
    # 2. ON-BALL SUB-HANDLERS
    # =========================================================================

    def try_shoot(self, agent) -> bool:
        """
        Shooting sub-handler. Evaluates goalie positioning and distance.
        Contract: Emits Action.kick_one_step(agent, target) and returns True, or returns False.
        """
        return super().shoot(agent)

    def try_pass(self, agent) -> bool:
        """
        Passing sub-handler using candidate sampling and heuristic/adversarial search.
        Contract: Emits Action.kick(agent, target, arrive_in) and returns True, or returns False.
        """
        return super().pass_(agent)

    def try_dribble(self, agent) -> bool:
        """
        Dribbling sub-handler to advance ball into open forward space.
        Contract: Emits Action.dribble(agent, target) and returns True, or returns False.
        """
        return super().dribble(agent)

    # =========================================================================
    # 3. OFF-BALL SUB-HANDLERS
    # =========================================================================

    def try_intercept_or_tackle(self, agent) -> bool:
        """
        Ball recovery sub-handler. Emits Action.tackle or Action.intercept.
        Contract: Emits an off-ball action and returns True, or returns False if teammate is closer.
        """
        wm = agent.wm
        # Close-range tackle opportunity
        if wm.self.dist_from_ball < 2.0 and wm.self.tackle_probability > 0.6:
            Action.tackle(agent, direction=0.0)
            note(agent, "tackle")
            return True

        it = wm.intercept_table
        my_steps = it.self_reach_steps
        mate_steps = it.first_teammate_reach_steps
        opp_steps = it.first_opponent_reach_steps

        # Intercept if no teammate has the ball and we are the best responder
        if not wm.kickable_teammate_existance and (my_steps <= 3 or (my_steps <= mate_steps and my_steps < opp_steps + 3)):
            Action.intercept(agent)
            note(agent, "intercept")
            return True
        return False

    def try_defensive_block(self, agent) -> bool:
        """
        Defensive positioning sub-handler to block opponent attack lane toward our goal.
        Contract: Emits Action.go_to_point(agent, block_pos) and returns True, or returns False.
        """
        wm = agent.wm
        it = wm.intercept_table
        if it.first_opponent_reach_steps < min(it.self_reach_steps, it.first_teammate_reach_steps):
            block = self.block_point(agent)
            if block is not None:
                Action.go_to_point(agent, block, max_dash_power=100.0)
                note(agent, "block")
                return True
        return False

    # =========================================================================
    # 4. EVALUATION & UTILITY HELPERS
    # =========================================================================

    def evaluate_state(self, agent, ball_pos: Vector2D) -> float:
        """
        Linear weighted state evaluation function Eval(s) for Minimax / Alpha-Beta.
        Contract: Computes scalar score where higher is better for our team.
        """
        goal_pos = Vector2D(agent.server_params.pitch_half_length, 0.0)
        dist_to_goal = ball_pos.dist(goal_pos)
        return -dist_to_goal


class Agent2(StarterAgent):
    def on_ball(self, agent) -> None:
        return None

    def off_ball(self, agent) -> None:
        return None

# STARTER CODE ENDS HERE #
