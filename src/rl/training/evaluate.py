import os
import argparse
import sys
import math
import numpy as np
import pygame

# Ensure project root and simulation directories are in the Python search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "simulation")))

import gymnasium as gym
from stable_baselines3 import PPO

# Import custom environment, simulator classes, and configs
from src.rl.aircraft_env import AircraftEnv
import src.simulation.config as config
from src.simulation.aircraft import Aircraft
from src.simulation.missile import Missile
from src.simulation.waypoint import Waypoint
from src.simulation.hud import HUD
from src.rl.reward.reward_function import RewardFunction

"""
================================================================================
EVALUATION CONCEPTS & EXPLANATIONS
================================================================================

1. WHAT IS DETERMINISTIC EVALUATION?
   During training, the agent samples actions from a probability distribution 
   to explore the state space. During evaluation, we set `deterministic=True`. 
   This forces the agent to always pick the highest-probability action (the optimal choice), 
   providing stable and consistent test behaviors.

2. WHY SEPARATE EVALUATION FROM TRAINING?
   Running evaluation scripts independently allows us to benchmark saved policy 
   networks under strict conditions without altering their learned weights. It helps 
   us assess how well the policy generalizes to new starting coordinates or threats.
================================================================================
"""

def get_normalized_observation(aircraft, missile, waypoint):
    """
    Helper function to compile the 12 normalized observations in Pygame GUI mode.
    Matches the observation space of AircraftEnv.
    """
    if not hasattr(aircraft, "altitude"):
        aircraft.altitude = 2500.0

    norm_x = aircraft.x / float(config.SCREEN_WIDTH)
    norm_y = aircraft.y / float(config.SCREEN_HEIGHT)
    norm_alt = aircraft.altitude / 5000.0
    norm_heading = aircraft.angle / math.pi
    norm_speed = aircraft.speed / config.AIRCRAFT_MAX_SPEED

    # Waypoint Rel
    rel_waypoint_x = (waypoint.x - aircraft.x) / float(config.SCREEN_WIDTH)
    rel_waypoint_y = (waypoint.y - aircraft.y) / float(config.SCREEN_HEIGHT)
    norm_waypoint_dist = aircraft.distance_to_waypoint / 1000.0

    # Missile Rel
    if missile.active:
        rel_missile_x = (missile.x - aircraft.x) / float(config.SCREEN_WIDTH)
        rel_missile_y = (missile.y - aircraft.y) / float(config.SCREEN_HEIGHT)
        norm_missile_dist = aircraft.distance_to_missile / 1000.0
        missile_active = 1.0
    else:
        rel_missile_x = 0.0
        rel_missile_y = 0.0
        norm_missile_dist = 1.0
        missile_active = 0.0

    return np.array([
        norm_x, norm_y, norm_alt, norm_heading, norm_speed,
        rel_waypoint_x, rel_waypoint_y, norm_waypoint_dist,
        rel_missile_x, rel_missile_y, norm_missile_dist, missile_active
    ], dtype=np.float32)

def evaluate_console(model_path, num_episodes=5):
    """
    Runs evaluation purely in the terminal console using the Gym environment.
    """
    print(f"\n[Evaluation] Starting headless console evaluation of model: {model_path}")
    env = AircraftEnv()
    
    # Load model
    model = PPO.load(model_path, env=env)
    
    for ep in range(1, num_episodes + 1):
        obs, info = env.reset()
        done = False
        episode_reward = 0.0
        steps = 0
        waypoint_reached = False
        aircraft_survived = True
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            steps += 1
            
            if terminated or truncated:
                done = True
                waypoint_reached = info.get("waypoint_reached", False)
                aircraft_survived = not info.get("missile_hit", False)
                
        print(f"Episode: {ep:02d} | Steps: {steps:04d} | Reward: {episode_reward:+.2f} | "
              f"Waypoint Reached: {waypoint_reached} | Survived: {aircraft_survived}")
        
    env.close()

def evaluate_gui(model_path, num_episodes=5):
    """
    Runs evaluation in a visual Pygame window, showing the PPO agent in action.
    """
    print(f"\n[Evaluation] Starting visual GUI evaluation of model: {model_path}")
    pygame.init()
    
    dashboard_width = 300
    bottom_bar_height = 50
    window_width = config.SCREEN_WIDTH + dashboard_width
    window_height = config.SCREEN_HEIGHT + bottom_bar_height
    
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("DRL Aircraft Control - Phase 8: PPO Agent Evaluation")
    
    clock = pygame.time.Clock()
    hud = HUD()
    reward_fn = RewardFunction()
    
    # Load PPO model
    model = PPO.load(model_path)
    
    for ep in range(1, num_episodes + 1):
        # Create objects for this episode
        aircraft = Aircraft(
            config.SCREEN_WIDTH // 2,
            config.SCREEN_HEIGHT // 2,
            speed=config.AIRCRAFT_START_SPEED,
            angle=0.0
        )
        aircraft.altitude = 2500.0
        
        missile = Missile()
        waypoint = Waypoint()
        
        episode_reward = 0.0
        steps_count = 0
        waypoints_reached_count = 0
        
        previous_distance_to_waypoint = 0.0
        previous_distance_to_missile = 9999.0
        missile_active_steps = 0
        missile_spawn_timer = 0
        
        aircraft_alive = True
        waiting_for_respawn = False
        respawn_timer = 0
        done = False
        
        running = True
        while running and not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
            reward = 0.0
            reward_breakdown = {k: 0.0 for k in ["survival", "stability", "waypoint", "missile_avoidance", "collision", "boundary", "missile_hit"]}
            waypoint_reached = False
            missile_hit = False
            missile_evaded = False
            wrapped = False
            
            # Predict action from PPO model
            if aircraft_alive:
                prev_angle = aircraft.angle
                prev_x, prev_y = aircraft.x, aircraft.y
                
                # Save distance trackers prior to update
                previous_distance_to_waypoint = math.sqrt((waypoint.x - aircraft.x) ** 2 + (waypoint.y - aircraft.y) ** 2)
                if missile.active:
                    previous_distance_to_missile = math.sqrt((missile.x - aircraft.x) ** 2 + (missile.y - aircraft.y) ** 2)
                else:
                    previous_distance_to_missile = 9999.0
                    
                aircraft.distance_to_waypoint = previous_distance_to_waypoint
                aircraft.distance_to_missile = previous_distance_to_missile
                
                # Get normalized observation vector
                obs = get_normalized_observation(aircraft, missile, waypoint)
                
                # Query the trained PPO agent
                action, _ = model.predict(obs, deterministic=True)
                action = int(action.item())
                
                # Apply predicted PPO action
                if action == 0:    # Turn Left
                    aircraft.turn_left()
                    translated_action = 0
                elif action == 1:  # Turn Right
                    aircraft.turn_right()
                    translated_action = 2
                elif action == 2:  # Accelerate
                    aircraft.accelerate()
                    translated_action = 1
                elif action == 3:  # Decelerate
                    aircraft.decelerate()
                    translated_action = 1
                elif action == 4:  # Climb
                    aircraft.altitude = min(aircraft.altitude + 50.0, 5000.0)
                    translated_action = 1
                elif action == 5:  # Dive
                    aircraft.altitude = max(aircraft.altitude - 50.0, 0.0)
                    translated_action = 1
                elif action == 6:  # Maintain Flight
                    translated_action = 1
                else:
                    translated_action = 1
                    
                aircraft.update()
                
                # Check wrapping
                wrapped_x = abs(aircraft.x - prev_x) > (aircraft.speed * 2)
                wrapped_y = abs(aircraft.y - prev_y) > (aircraft.speed * 2)
                wrapped = wrapped_x or wrapped_y
                
                # Check waypoint
                if aircraft.distance_to_waypoint < (config.WAYPOINT_RADIUS + 12.0):
                    waypoint.respawn()
                    waypoints_reached_count += 1
                    waypoint_reached = True
                    
                steps_count += 1
                
            # Missile lifecycle
            if not missile.active and not missile.exploding:
                missile_spawn_timer += 1
                frames_to_spawn = int(config.MISSILE_SPAWN_DELAY_SEC * 60)
                if missile_spawn_timer >= frames_to_spawn:
                    missile.spawn()
                    missile_spawn_timer = 0
                    missile_active_steps = 0
            else:
                if aircraft_alive:
                    missile.update(aircraft.x, aircraft.y)
                    if missile.active:
                        missile_active_steps += 1
                        if missile_active_steps >= 300:
                            missile.explode()
                            missile_evaded = True
                            missile_active_steps = 0
                            
                    if missile.active:
                        dx = aircraft.x - missile.x
                        dy = aircraft.y - missile.y
                        distance = math.sqrt(dx**2 + dy**2)
                        
                        if distance < config.MISSILE_COLLISION_RADIUS:
                            missile.explode()
                            aircraft_alive = False
                            aircraft.speed = 0.0
                            missile_hit = True
                            done = True
                else:
                    if missile.exploding:
                        missile.explosion_timer += 1
                        if missile.explosion_timer >= config.EXPLOSION_DURATION_FRAMES:
                            missile.exploding = False
                            done = True  # End evaluation episode when explosion ends
                            
            # Update post-action distance values
            curr_dist_to_waypoint = math.sqrt((waypoint.x - aircraft.x) ** 2 + (waypoint.y - aircraft.y) ** 2)
            aircraft.distance_to_waypoint = curr_dist_to_waypoint
            
            if missile.active:
                curr_dist_to_missile = math.sqrt((missile.x - aircraft.x) ** 2 + (missile.y - aircraft.y) ** 2)
            else:
                curr_dist_to_missile = 9999.0
            aircraft.distance_to_missile = curr_dist_to_missile
            
            # Calculate reward
            if aircraft_alive or missile_hit:
                reward, reward_breakdown = reward_fn.calculate_total_reward(
                    action=translated_action,
                    curr_dist_to_waypoint=curr_dist_to_waypoint,
                    prev_dist_to_waypoint=previous_distance_to_waypoint,
                    waypoint_reached=waypoint_reached,
                    curr_dist_to_missile=curr_dist_to_missile,
                    prev_dist_to_missile=previous_distance_to_missile,
                    missile_active=missile.active,
                    missile_evaded=missile_evaded,
                    collision_detected=False,
                    wrapped=wrapped,
                    missile_hit=missile_hit
                )
                episode_reward += reward
                
            # Truncation check
            if steps_count >= 1000:
                done = True
                
            # Render elements
            screen.fill(config.COLOR_BACKGROUND)
            
            if aircraft_alive or (not aircraft_alive and not waiting_for_respawn):
                waypoint.draw(screen)
            if aircraft_alive:
                aircraft.draw(screen)
            if missile.active or missile.exploding:
                missile.draw(screen)
                
            active_action_label = {
                0: "TURN LEFT",
                1: "TURN RIGHT",
                2: "ACCELERATE",
                3: "DECELERATE",
                4: "CLIMB",
                5: "DIVE",
                6: "MAINTAIN FLIGHT"
            }.get(action, "NONE") if aircraft_alive else "DEAD"
            
            summary_data = {
                "current_episode": ep,
                "steps_count": steps_count,
                "episode_reward": episode_reward,
                "waypoints_reached": waypoints_reached_count,
                "done": done
            }
            
            hud.draw_all(
                surface=screen,
                aircraft=aircraft,
                missile=missile,
                active_behavior=f"PPO: {active_action_label}",
                current_reward=reward if (aircraft_alive or missile_hit) else 0.0,
                reward_breakdown=reward_breakdown,
                summary_data=summary_data,
                fps=clock.get_fps()
            )
            
            pygame.display.flip()
            clock.tick(60)
            
        print(f"Episode: {ep:02d} | Steps: {steps_count:04d} | Reward: {episode_reward:+.2f} | "
              f"Waypoints Reached: {waypoints_reached_count} | Survived: {aircraft_alive}")
        
        # Pause slightly between episodes
        pygame.time.wait(1000)
        
    pygame.quit()

def main():
    parser = argparse.ArgumentParser(description="Evaluate a trained PPO agent.")
    parser.add_argument("--console", action="store_true", help="Run evaluation in headless console mode.")
    parser.add_argument("--episodes", type=int, default=3, help="Number of episodes to evaluate.")
    args = parser.parse_args()

    MODEL_PATH = "models/ppo_aircraft"

    if not os.path.exists(MODEL_PATH + ".zip"):
        print(f"[Error] No trained model found at {MODEL_PATH}.zip. Please train the agent first using ppo_trainer.py!")
        sys.exit(1)

    if args.console:
        evaluate_console(MODEL_PATH, num_episodes=args.episodes)
    else:
        evaluate_gui(MODEL_PATH, num_episodes=args.episodes)

if __name__ == "__main__":
    main()
