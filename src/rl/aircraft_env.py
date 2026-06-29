import os
import sys
import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces

# Add the simulation source folder to python's import path
# This allows us to load config, Aircraft, Missile, and Waypoint directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'simulation')))

import config
from aircraft import Aircraft
from missile import Missile
from waypoint import Waypoint
from reward import RewardFunction

class AircraftEnv(gym.Env):
    """
    Custom Gymnasium Environment wrapping our 2D Aircraft/Missile simulation.
    Designed to train a Reinforcement Learning agent (like PPO) to navigate
    to waypoints and evade incoming missile threats using a modular reward function.
    """
    # Define render metadata
    metadata = {"render_modes": ["ansi"]}

    def __init__(self):
        super(AircraftEnv, self).__init__()

        # Instantiate the modular Reward Function
        self.reward_fn = RewardFunction()

        # 1. Action Space: spaces.Discrete(3)
        # 0 -> Turn Left
        # 1 -> Go Straight (maintain current heading)
        # 2 -> Turn Right
        self.action_space = spaces.Discrete(3)

        # 2. Observation Space: spaces.Box (6 continuous values)
        # [Aircraft X, Aircraft Y, Aircraft Speed, Aircraft Heading, Dist to Waypoint, Dist to Missile]
        # We specify minimum (low) and maximum (high) limits for each value
        low_bounds = np.array([
            0.0,                         # X position min
            0.0,                         # Y position min
            config.AIRCRAFT_MIN_SPEED,   # Speed min
            -math.pi,                    # Heading angle min (-180 degrees in rad)
            0.0,                         # Dist to waypoint min
            0.0                          # Dist to missile min
        ], dtype=np.float32)

        high_bounds = np.array([
            float(config.SCREEN_WIDTH),  # X position max (800)
            float(config.SCREEN_HEIGHT), # Y position max (600)
            config.AIRCRAFT_MAX_SPEED,   # Speed max (6.0)
            math.pi,                     # Heading angle max (+180 degrees in rad)
            2000.0,                      # Dist to waypoint max (safe upper limit)
            2000.0                       # Dist to missile max (safe upper limit)
        ], dtype=np.float32)

        self.observation_space = spaces.Box(low=low_bounds, high=high_bounds, dtype=np.float32)

        # Object references (initialized in reset)
        self.aircraft = None
        self.missile = None
        self.waypoint = None

        # Episode tracking variables
        self.missile_spawn_timer = 0
        self.steps_count = 0
        self.previous_distance_to_waypoint = 0.0
        self.previous_distance_to_missile = 9999.0
        self.missile_active_steps = 0  # Frame steps the current missile has been chasing

    def _get_obs(self):
        """
        Helper method to compile the environment state into a NumPy array.
        """
        return np.array([
            float(self.aircraft.x),
            float(self.aircraft.y),
            float(self.aircraft.speed),
            float(self.aircraft.angle),
            float(self.aircraft.distance_to_waypoint),
            float(self.aircraft.distance_to_missile)
        ], dtype=np.float32)

    def _get_distance(self, x1, y1, x2, y2):
        """
        Calculates straight-line Euclidean distance between two points.
        """
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def reset(self, seed=None, options=None):
        """
        Resets the environment state at the start of a new episode.
        """
        # Call super to handle random seeds in Gymnasium
        super().reset(seed=seed)

        # 1. Recreate Aircraft in the center of the screen
        self.aircraft = Aircraft(
            config.SCREEN_WIDTH // 2,
            config.SCREEN_HEIGHT // 2,
            speed=config.AIRCRAFT_START_SPEED,
            angle=0.0
        )

        # 2. Recreate Waypoint randomly
        self.waypoint = Waypoint()

        # 3. Recreate Missile (starts inactive)
        self.missile = Missile()

        # 4. Reset counter and timers
        self.missile_spawn_timer = 0
        self.steps_count = 0
        self.missile_active_steps = 0

        # 5. Initialize distances
        initial_waypoint_dist = self._get_distance(self.aircraft.x, self.aircraft.y, self.waypoint.x, self.waypoint.y)
        self.aircraft.distance_to_waypoint = initial_waypoint_dist
        self.aircraft.distance_to_missile = 9999.0  # Set to a safe default since missile is not active

        self.previous_distance_to_waypoint = initial_waypoint_dist
        self.previous_distance_to_missile = 9999.0

        # Compile observation
        obs = self._get_obs()
        info = {}

        return obs, info

    def step(self, action):
        """
        Executes one timestep of simulation physics based on the selected action.
        """
        # Increment frame steps counter
        self.steps_count += 1

        # Track position prior to movement to detect coordinate wrapping (boundary crossing)
        prev_x, prev_y = self.aircraft.x, self.aircraft.y

        # 1. Apply action to turn/steer the aircraft
        if action == 0:    # Turn Left
            self.aircraft.turn_left()
        elif action == 2:  # Turn Right
            self.aircraft.turn_right()
        # Action == 1: Do nothing (Go Straight)

        # 2. Advance aircraft physics position (can wrap around coordinates inside self.aircraft.update())
        self.aircraft.update()

        # Check if wrapping occurred (if distance jumped is greater than aircraft's speed)
        wrapped_x = abs(self.aircraft.x - prev_x) > (self.aircraft.speed * 2)
        wrapped_y = abs(self.aircraft.y - prev_y) > (self.aircraft.speed * 2)
        wrapped = wrapped_x or wrapped_y

        # 3. Manage missile spawn, tracking, and evasion lifetime
        missile_evaded = False
        if not self.missile.active and not self.missile.exploding:
            self.missile_spawn_timer += 1
            frames_to_spawn = int(config.MISSILE_SPAWN_DELAY_SEC * 60)
            if self.missile_spawn_timer >= frames_to_spawn:
                self.missile.spawn()
                self.missile_spawn_timer = 0
                self.missile_active_steps = 0
        else:
            self.missile.update(self.aircraft.x, self.aircraft.y)
            if self.missile.active:
                self.missile_active_steps += 1
                # If active for more than 5 seconds (300 frames), the missile is successfully evaded
                if self.missile_active_steps >= 300:
                    self.missile.explode()  # Triggers inert explosion state
                    missile_evaded = True
                    self.missile_active_steps = 0

        # 4. Calculate updated distances
        curr_dist_to_waypoint = self._get_distance(self.aircraft.x, self.aircraft.y, self.waypoint.x, self.waypoint.y)
        self.aircraft.distance_to_waypoint = curr_dist_to_waypoint

        if self.missile.active:
            curr_dist_to_missile = self._get_distance(self.aircraft.x, self.aircraft.y, self.missile.x, self.missile.y)
        else:
            curr_dist_to_missile = 9999.0
        self.aircraft.distance_to_missile = curr_dist_to_missile

        # Determine events for reward calculation
        waypoint_reached = curr_dist_to_waypoint < (config.WAYPOINT_RADIUS + 12.0)
        missile_hit = self.missile.active and (curr_dist_to_missile < config.MISSILE_COLLISION_RADIUS)
        collision_detected = False  # Placeholder for obstacles, none present in current version

        # 5. Compute modular reward function
        reward, reward_breakdown = self.reward_fn.calculate_total_reward(
            action=action,
            curr_dist_to_waypoint=curr_dist_to_waypoint,
            prev_dist_to_waypoint=self.previous_distance_to_waypoint,
            waypoint_reached=waypoint_reached,
            curr_dist_to_missile=curr_dist_to_missile,
            prev_dist_to_missile=self.previous_distance_to_missile,
            missile_active=self.missile.active,
            missile_evaded=missile_evaded,
            collision_detected=collision_detected,
            wrapped=wrapped,
            missile_hit=missile_hit
        )

        # Set up terminal states
        terminated = False
        truncated = False
        
        if waypoint_reached or missile_hit:
            terminated = True

        # Step limit truncation (ends episode after 1000 frames)
        if self.steps_count >= 1000:
            truncated = True

        # Store distance states for comparison in the next step
        self.previous_distance_to_waypoint = curr_dist_to_waypoint
        self.previous_distance_to_missile = curr_dist_to_missile

        # Compile detailed info dictionary
        info = {
            "waypoint_reached": waypoint_reached,
            "missile_hit": missile_hit,
            "missile_evaded": missile_evaded,
            "boundary_wrapped": wrapped,
            "reward_breakdown": reward_breakdown
        }

        # Compile observation
        obs = self._get_obs()

        return obs, reward, terminated, truncated, info

    def render(self):
        """
        Console-based rendering. Prints simulation values.
        """
        angle_deg = math.degrees(self.aircraft.angle)
        print(f"Step: {self.steps_count:04d} | "
              f"Plane Pos: ({self.aircraft.x:.1f}, {self.aircraft.y:.1f}) | "
              f"Heading: {angle_deg:.1f}° | "
              f"Speed: {self.aircraft.speed:.1f} | "
              f"Dist Waypoint: {self.aircraft.distance_to_waypoint:.1f} px | "
              f"Dist Missile: {self.aircraft.distance_to_missile:.1f} px")

    def close(self):
        """
        Clean up resources.
        """
        pass

