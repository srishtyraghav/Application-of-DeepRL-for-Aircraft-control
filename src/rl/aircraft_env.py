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

class AircraftEnv(gym.Env):
    """
    Custom Gymnasium Environment wrapping our 2D Aircraft/Missile simulation.
    Designed to train a Reinforcement Learning agent (like PPO) to navigate
    to waypoints and evade incoming missile threats.
    """
    # Define render metadata
    metadata = {"render_modes": ["ansi"]}

    def __init__(self):
        super(AircraftEnv, self).__init__()

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

        # 5. Initialize distances
        initial_waypoint_dist = self._get_distance(self.aircraft.x, self.aircraft.y, self.waypoint.x, self.waypoint.y)
        self.aircraft.distance_to_waypoint = initial_waypoint_dist
        self.aircraft.distance_to_missile = 9999.0  # Set to a safe default since missile is not active

        self.previous_distance_to_waypoint = initial_waypoint_dist

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

        # 1. Apply action to turn/steer the aircraft
        if action == 0:    # Turn Left
            self.aircraft.turn_left()
        elif action == 2:  # Turn Right
            self.aircraft.turn_right()
        # Action == 1: Do nothing (Go Straight)

        # 2. Advance aircraft physics position
        self.aircraft.update()

        # 3. Manage missile spawn and homing physics
        if not self.missile.active and not self.missile.exploding:
            self.missile_spawn_timer += 1
            frames_to_spawn = int(config.MISSILE_SPAWN_DELAY_SEC * 60)
            if self.missile_spawn_timer >= frames_to_spawn:
                self.missile.spawn()
                self.missile_spawn_timer = 0
        else:
            self.missile.update(self.aircraft.x, self.aircraft.y)

        # 4. Calculate updated distances
        curr_dist_to_waypoint = self._get_distance(self.aircraft.x, self.aircraft.y, self.waypoint.x, self.waypoint.y)
        self.aircraft.distance_to_waypoint = curr_dist_to_waypoint

        if self.missile.active:
            curr_dist_to_missile = self._get_distance(self.aircraft.x, self.aircraft.y, self.missile.x, self.missile.y)
        else:
            curr_dist_to_missile = 9999.0
        self.aircraft.distance_to_missile = curr_dist_to_missile

        # 5. Compute Reward function
        reward = -0.01  # Base step time penalty

        # Rule A: +1 if the aircraft moves closer to the waypoint
        if curr_dist_to_waypoint < self.previous_distance_to_waypoint:
            reward += 1.0

        # Rule B: Check if waypoint is reached
        terminated = False
        truncated = False
        info = {
            "waypoint_reached": False,
            "missile_hit": False
        }

        # Threshold to reach waypoint (radius + boundary margin)
        if curr_dist_to_waypoint < (config.WAYPOINT_RADIUS + 12.0):
            reward += 100.0
            terminated = True
            info["waypoint_reached"] = True

        # Rule C: Check if missile hits the aircraft
        if self.missile.active and curr_dist_to_missile < config.MISSILE_COLLISION_RADIUS:
            reward -= 100.0
            terminated = True
            info["missile_hit"] = True

        # Rule D: Step limit truncation (ends episode after 1000 frames)
        if self.steps_count >= 1000:
            truncated = True

        # Save distance for comparison in the next step
        self.previous_distance_to_waypoint = curr_dist_to_waypoint

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
