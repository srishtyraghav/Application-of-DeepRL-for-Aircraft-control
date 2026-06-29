import os
import sys
import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces

# Add the project root directory to Python's search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import src.simulation.config as config
from src.simulation.aircraft import Aircraft
from src.simulation.missile import Missile
from src.simulation.waypoint import Waypoint
from src.rl.reward import RewardFunction

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

        # 1. Action Space: spaces.Discrete(7)
        # 0 -> Turn Left
        # 1 -> Turn Right
        # 2 -> Accelerate
        # 3 -> Decelerate
        # 4 -> Climb
        # 5 -> Dive
        # 6 -> Maintain Flight
        self.action_space = spaces.Discrete(7)

        # 2. Observation Space: spaces.Box (12 continuous values)
        # All values normalized to be in [-1.0, 1.0] or [0.0, 1.0]
        # [Norm X, Norm Y, Norm Alt, Norm Heading, Norm Speed, Rel WP X, Rel WP Y, Norm WP Dist, Rel MS X, Rel MS Y, Norm MS Dist, MS Active]
        low_bounds = np.array([
            0.0,   # X position
            0.0,   # Y position
            0.0,   # Altitude
            -1.0,  # Heading (angle / pi)
            0.0,   # Speed
            -1.0,  # Rel Waypoint X
            -1.0,  # Rel Waypoint Y
            0.0,   # Waypoint Dist
            -1.0,  # Rel Missile X
            -1.0,  # Rel Missile Y
            0.0,   # Missile Dist
            0.0    # Missile Active Flag
        ], dtype=np.float32)

        high_bounds = np.array([
            1.0,   # X position
            1.0,   # Y position
            1.0,   # Altitude
            1.0,   # Heading (angle / pi)
            1.0,   # Speed
            1.0,   # Rel Waypoint X
            1.0,   # Rel Waypoint Y
            1.5,   # Waypoint Dist
            1.5,   # Rel Missile X
            1.5,   # Rel Missile Y
            1.5,   # Missile Dist
            1.0    # Missile Active Flag
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
        Helper method to compile the normalized environment state into a NumPy array.
        """
        # Normalize aircraft state
        norm_x = self.aircraft.x / float(config.SCREEN_WIDTH)
        norm_y = self.aircraft.y / float(config.SCREEN_HEIGHT)
        norm_alt = self.aircraft.altitude / 5000.0  # Max altitude 5000.0m
        norm_heading = self.aircraft.angle / math.pi
        norm_speed = self.aircraft.speed / config.AIRCRAFT_MAX_SPEED

        # Waypoint relative positions and distance
        rel_waypoint_x = (self.waypoint.x - self.aircraft.x) / float(config.SCREEN_WIDTH)
        rel_waypoint_y = (self.waypoint.y - self.aircraft.y) / float(config.SCREEN_HEIGHT)
        norm_waypoint_dist = self.aircraft.distance_to_waypoint / 1000.0  # Diagonal is ~1000 pixels

        # Missile relative positions, distance, and status
        if self.missile.active:
            rel_missile_x = (self.missile.x - self.aircraft.x) / float(config.SCREEN_WIDTH)
            rel_missile_y = (self.missile.y - self.aircraft.y) / float(config.SCREEN_HEIGHT)
            norm_missile_dist = self.aircraft.distance_to_missile / 1000.0
            missile_active = 1.0
        else:
            rel_missile_x = 0.0
            rel_missile_y = 0.0
            norm_missile_dist = 1.0
            missile_active = 0.0

        return np.array([
            norm_x,
            norm_y,
            norm_alt,
            norm_heading,
            norm_speed,
            rel_waypoint_x,
            rel_waypoint_y,
            norm_waypoint_dist,
            rel_missile_x,
            rel_missile_y,
            norm_missile_dist,
            missile_active
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
        self.aircraft.altitude = 2500.0  # Start at mid-altitude (50% of 5000.0m)

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

        # 1. Apply action to turn/steer/accelerate/climb the aircraft
        # Actions are:
        # 0 -> Turn Left
        # 1 -> Turn Right
        # 2 -> Accelerate
        # 3 -> Decelerate
        # 4 -> Climb
        # 5 -> Dive
        # 6 -> Maintain Flight
        #
        # For the reward function, we map these to the 3 legacy actions:
        # 0 -> Turn Left, 1 -> Go Straight, 2 -> Turn Right
        if action == 0:    # Turn Left
            self.aircraft.turn_left()
            translated_action = 0
        elif action == 1:  # Turn Right
            self.aircraft.turn_right()
            translated_action = 2
        elif action == 2:  # Accelerate
            self.aircraft.accelerate()
            translated_action = 1
        elif action == 3:  # Decelerate
            self.aircraft.decelerate()
            translated_action = 1
        elif action == 4:  # Climb
            self.aircraft.altitude = min(self.aircraft.altitude + 50.0, 5000.0)
            translated_action = 1
        elif action == 5:  # Dive
            self.aircraft.altitude = max(self.aircraft.altitude - 50.0, 0.0)
            translated_action = 1
        elif action == 6:  # Maintain Flight
            translated_action = 1
        else:
            translated_action = 1

        # 2. Advance aircraft physics position
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
            action=translated_action,
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

