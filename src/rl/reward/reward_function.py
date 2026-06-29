import math

class RewardFunction:
    """
    RewardFunction defines and computes the reinforcement learning reward system 
    for the Aircraft Control simulation. It evaluates the agent's behavior after 
    each step, combining sparse event-driven rewards and dense shaping rewards.
    
    Why separate the reward system from the environment?
    1. Separation of Concerns: Keeps the physical/state updates separate from reward metrics.
    2. Modularity: Allows weights and reward formulas to be tweaked independently 
       without changing env mechanics.
    3. Readability & Maintainability: Provides structured, isolated methods for 
       each distinct behavior.
    """
    def __init__(self):
        # Base event rewards/penalties
        self.r_survival = 1.0            # +1 for surviving one step
        self.r_stable_flight = 5.0        # +5 for stable flight (no turning)
        self.r_reach_waypoint = 15.0     # +15 for reaching the waypoint
        self.r_evade_missile = 30.0      # +30 for successfully evading the missile
        
        self.p_leave_boundary = -20.0    # -20 for leaving environment boundaries
        self.p_collision = -50.0         # -50 for collision with obstacles
        self.p_missile_hit = -100.0      # -100 for being hit by a missile

        # Shaping rewards/penalties
        self.s_closer_waypoint = 1.0     # Small reward for moving closer to waypoint
        self.s_farther_waypoint = -1.0   # Small penalty for moving farther from waypoint
        self.s_away_missile = 1.5        # Small reward for increasing distance from missile
        self.s_closer_missile = -1.5     # Small penalty for decreasing distance to missile
        self.p_turn = -0.5               # Small penalty for turning action to prevent instability

    def survival_reward(self) -> float:
        """
        Computes the survival reward for staying alive during the step.
        """
        return self.r_survival

    def flight_stability_reward(self, action: int) -> float:
        """
        Computes the stability reward and turning penalties.
        Stable flight is encouraged when the aircraft does not steer/turn (action == 1).
        Turning (action == 0 or action == 2) incurs a small penalty to prevent oscillations.
        """
        if action == 1:  # 1 -> Go Straight (stable flight)
            return self.r_stable_flight
        else:  # 0 -> Turn Left, 2 -> Turn Right
            return self.p_turn

    def waypoint_navigation_reward(self, curr_dist: float, prev_dist: float, reached: bool) -> float:
        """
        Computes rewards for navigating towards the waypoint.
        Provides a large positive reward if reached, and shaping rewards based on relative progress.
        """
        if reached:
            return self.r_reach_waypoint
        
        # Shaping reward based on distance change
        if curr_dist < prev_dist:
            return self.s_closer_waypoint
        else:
            return self.s_farther_waypoint

    def missile_avoidance_reward(self, curr_dist: float, prev_dist: float, missile_active: bool, evaded: bool) -> float:
        """
        Computes rewards for avoiding incoming missile threats.
        Provides a large positive reward if evaded, and shaping rewards based on whether distance is increasing/decreasing.
        """
        if evaded:
            return self.r_evade_missile
        
        if not missile_active:
            return 0.0
            
        # Shaping reward based on distance change to active missile
        if curr_dist > prev_dist:
            return self.s_away_missile
        else:
            return self.s_closer_missile

    def collision_penalty(self, collision_detected: bool) -> float:
        """
        Computes penalty for colliding with a flight obstacle.
        """
        return self.p_collision if collision_detected else 0.0

    def boundary_penalty(self, wrapped: bool) -> float:
        """
        Computes penalty for leaving screen boundary (coordinates wrap).
        """
        return self.p_leave_boundary if wrapped else 0.0

    def missile_hit_penalty(self, hit_detected: bool) -> float:
        """
        Computes penalty for getting hit by a missile.
        """
        return self.p_missile_hit if hit_detected else 0.0

    def calculate_total_reward(self, 
                               action: int,
                               curr_dist_to_waypoint: float,
                               prev_dist_to_waypoint: float,
                               waypoint_reached: bool,
                               curr_dist_to_missile: float,
                               prev_dist_to_missile: float,
                               missile_active: bool,
                               missile_evaded: bool,
                               collision_detected: bool,
                               wrapped: bool,
                               missile_hit: bool) -> tuple:
        """
        Calculates the final aggregated reward as the sum of all components.
        
        Returns:
            total_reward (float): The final reward value.
            reward_components (dict): Individual reward components for analysis/logging.
        """
        # Calculate each component
        r_surv = self.survival_reward()
        r_stab = self.flight_stability_reward(action)
        r_wayp = self.waypoint_navigation_reward(curr_dist_to_waypoint, prev_dist_to_waypoint, waypoint_reached)
        r_miss = self.missile_avoidance_reward(curr_dist_to_missile, prev_dist_to_missile, missile_active, missile_evaded)
        r_coll = self.collision_penalty(collision_detected)
        r_bound = self.boundary_penalty(wrapped)
        r_mhit = self.missile_hit_penalty(missile_hit)

        # Sum all components
        total_reward = r_surv + r_stab + r_wayp + r_miss + r_coll + r_bound + r_mhit

        # Compile component breakdown for environment logging and info dict
        reward_components = {
            "survival": r_surv,
            "stability": r_stab,
            "waypoint": r_wayp,
            "missile_avoidance": r_miss,
            "collision": r_coll,
            "boundary": r_bound,
            "missile_hit": r_mhit
        }

        return total_reward, reward_components
