import os
import sys
import math
import pygame
import config
from aircraft import Aircraft
from missile import Missile
from waypoint import Waypoint
import behavior_tree

# Add the project root and source folders to Python's import paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from rl.reward.reward_function import RewardFunction
from rendering.renderer import Renderer

def main():
    # Initialize the Pygame framework
    pygame.init()

    # Configure the game window dimensions for Phase 10 Overhaul
    # Left Panel: 250px | Sim Screen: 800px | Right HUD Panel: 300px
    # Total Width: 1350px | Total Height: 650px (Sim Screen: 600px, Bottom Bar: 50px)
    window_width = 1350
    window_height = 650

    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("DRL Aircraft Control - Phase 10: Cockpit Overhaul Demonstration")

    # Create a clock for 60 FPS
    clock = pygame.time.Clock()

    # Create the aircraft
    aircraft = Aircraft(
        config.SCREEN_WIDTH // 2,
        config.SCREEN_HEIGHT // 2,
        speed=config.AIRCRAFT_START_SPEED,
        angle=0.0,
    )

    # Create the missile threat
    missile = Missile()

    # Create the navigation waypoint target
    waypoint = Waypoint()

    # Create the Behavior Tree
    # Roots a Selector that prioritizes EvadeMissile over NavigateToWaypoint
    bt = behavior_tree.Selector([
        behavior_tree.EvadeMissile(),
        behavior_tree.NavigateToWaypoint()
    ])

    # Instantiate the modular Reward Function and the Overhauled Renderer
    reward_fn = RewardFunction()
    renderer = Renderer()

    # Telemetry and state trackers
    episode_reward = 0.0
    steps_count = 0
    current_episode = 1
    waypoints_reached_count = 0
    
    previous_distance_to_waypoint = 0.0
    previous_distance_to_missile = 9999.0
    missile_active_steps = 0

    # Timer before a missile appears (used for the initial/regular spawns)
    missile_spawn_timer = 0

    # Aircraft lifecycle and state tracking variables
    aircraft_alive = True
    waiting_for_respawn = False
    respawn_timer = 0
    done = False

    # Phase 10: Cockpit history trackers
    past_episode_rewards = []
    episode_success_history = []
    autopilot_mode = True

    # Main game loop
    running = True
    while running:
        # Check for episode truncation (1000 steps reached)
        if steps_count >= 1000:
            past_episode_rewards.append(episode_reward)
            episode_success_history.append(1)  # Survival of 1000 steps is success
            done = True
            waiting_for_respawn = True
            respawn_timer = 0
            aircraft_alive = False

        # -----------------------------
        # Handle window events
        # -----------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:  # Toggle Autopilot mode with M key
                    autopilot_mode = not autopilot_mode
                elif event.key == pygame.K_r:  # Trigger Reset with R key
                    steps_count = 1000
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    if renderer.btn_autopilot_rect.collidepoint(mouse_pos):
                        autopilot_mode = not autopilot_mode
                    elif renderer.btn_reset_rect.collidepoint(mouse_pos):
                        steps_count = 1000

        # Initialize step metrics
        reward = 0.0
        reward_breakdown = {k: 0.0 for k in ["survival", "stability", "waypoint", "missile_avoidance", "collision", "boundary", "missile_hit"]}
        waypoint_reached = False
        missile_hit = False
        missile_evaded = False
        wrapped = False

        # -------------------------------------------------
        # Aircraft Decision Making & Movement (Autopilot / Manual)
        # Only evaluate decisions and move if aircraft is alive
        # -------------------------------------------------
        if aircraft_alive:
            # Save state prior to update for change metrics
            prev_angle = aircraft.angle
            prev_x, prev_y = aircraft.x, aircraft.y
            
            # Save distance trackers prior to update
            previous_distance_to_waypoint = math.sqrt(
                (waypoint.x - aircraft.x) ** 2 + (waypoint.y - aircraft.y) ** 2
            )
            if missile.active:
                previous_distance_to_missile = math.sqrt(
                    (missile.x - aircraft.x) ** 2 + (missile.y - aircraft.y) ** 2
                )
            else:
                previous_distance_to_missile = 9999.0

            # 1. Update distance inputs for the Behavior Tree
            aircraft.distance_to_waypoint = previous_distance_to_waypoint
            aircraft.distance_to_missile = previous_distance_to_missile
                
            if autopilot_mode:
                # 2. Tick the Behavior Tree (runs Selector, evaluates Evade/Navigate)
                bt.tick(aircraft, missile, waypoint)
                
                # 3. Determine the discrete action taken by the Behavior Tree
                angle_diff = aircraft.angle - prev_angle
                angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
                if angle_diff < -0.001:
                    action = 0  # Turn Left
                elif angle_diff > 0.001:
                    action = 2  # Turn Right
                else:
                    action = 1  # Go Straight
            else:
                # Manual control input checks
                keys = pygame.key.get_pressed()
                action = 1  # Default action
                
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    aircraft.turn_left()
                    action = 0
                elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    aircraft.turn_right()
                    action = 2
                    
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    aircraft.accelerate()
                elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    aircraft.decelerate()
                    
                if not hasattr(aircraft, "altitude"):
                    aircraft.altitude = 2500.0
                if keys[pygame.K_SPACE]:
                    aircraft.altitude = min(aircraft.altitude + 50.0, 5000.0)
                elif keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                    aircraft.altitude = max(aircraft.altitude - 50.0, 0.0)
            
            # 4. Apply physics movement updates
            aircraft.update()
            
            # Check if coordinate wrapping occurred (boundary violation)
            wrapped_x = abs(aircraft.x - prev_x) > (aircraft.speed * 2)
            wrapped_y = abs(aircraft.y - prev_y) > (aircraft.speed * 2)
            wrapped = wrapped_x or wrapped_y

            # 5. Check if the aircraft has reached the waypoint target
            if aircraft.distance_to_waypoint < (config.WAYPOINT_RADIUS + 12.0):
                waypoint.respawn()
                waypoints_reached_count += 1
                waypoint_reached = True

            steps_count += 1

        # -----------------------------
        # Missile Lifecycle Logic
        # -----------------------------
        if not missile.active and not missile.exploding:
            # Only tick the spawn timer if we are NOT waiting for the aircraft to respawn
            if not waiting_for_respawn:
                missile_spawn_timer += 1
                frames_to_spawn = int(config.MISSILE_SPAWN_DELAY_SEC * 60)
                if missile_spawn_timer >= frames_to_spawn:
                    missile.spawn()
                    missile_spawn_timer = 0
                    missile_active_steps = 0
        else:
            if aircraft_alive:
                # Update missile tracking or explosion state
                missile.update(aircraft.x, aircraft.y)
                if missile.active:
                    missile_active_steps += 1
                    # If active for more than 5 seconds (300 frames), the missile is successfully evaded
                    if missile_active_steps >= 300:
                        missile.explode()
                        missile_evaded = True
                        missile_active_steps = 0

                # Check for collision only if the missile is active
                if missile.active:
                    dx = aircraft.x - missile.x
                    dy = aircraft.y - missile.y
                    distance = math.sqrt(dx ** 2 + dy ** 2)

                    if distance < config.MISSILE_COLLISION_RADIUS:
                        # Start the explosion sequence and mark aircraft as dead
                        missile.explode()
                        aircraft_alive = False
                        aircraft.speed = 0.0  # Reset speed to 0.0 so HUD displays DEAD
                        missile_hit = True
                        done = True
                        past_episode_rewards.append(episode_reward)
                        episode_success_history.append(0)  # Missile hit is failure
            else:
                # During the explosion animation, continue animating the explosion but do not chase
                if missile.exploding:
                    missile.explosion_timer += 1
                    if missile.explosion_timer >= config.EXPLOSION_DURATION_FRAMES:
                        missile.exploding = False

        # Update post-action distance values for reward functions
        curr_dist_to_waypoint = math.sqrt((waypoint.x - aircraft.x) ** 2 + (waypoint.y - aircraft.y) ** 2)
        aircraft.distance_to_waypoint = curr_dist_to_waypoint
        
        if missile.active:
            curr_dist_to_missile = math.sqrt((missile.x - aircraft.x) ** 2 + (missile.y - aircraft.y) ** 2)
        else:
            curr_dist_to_missile = 9999.0
        aircraft.distance_to_missile = curr_dist_to_missile

        # Calculate reward at each step (only if aircraft was active or just hit)
        if aircraft_alive or missile_hit:
            reward, reward_breakdown = reward_fn.calculate_total_reward(
                action=action,
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

        # -----------------------------
        # Transition from Explosion to Respawn
        # -----------------------------
        if not aircraft_alive and not waiting_for_respawn:
            # If the missile explosion animation has finished (exploding turned False)
            if not missile.exploding:
                waiting_for_respawn = True
                respawn_timer = 0

        # -----------------------------
        # Respawn Timer Logic (New Episode Starts)
        # -----------------------------
        if waiting_for_respawn:
            respawn_timer += 1
            if respawn_timer >= 180: # 3 seconds delay
                # Recreate aircraft
                aircraft = Aircraft(
                    config.SCREEN_WIDTH // 2,
                    config.SCREEN_HEIGHT // 2,
                    speed=config.AIRCRAFT_START_SPEED,
                    angle=0.0,
                )
                aircraft.altitude = 2500.0  # Alt init
                missile.spawn()
                
                # Reset episode telemetry
                current_episode += 1
                episode_reward = 0.0
                steps_count = 0
                
                aircraft_alive = True
                waiting_for_respawn = False
                respawn_timer = 0
                done = False
                
                # Clear visual trails on respawn
                renderer.trajectories.clear()

        # -----------------------------
        # Drawing / Rendering
        # -----------------------------
        active_bt_state = bt.active_behavior if aircraft_alive else "DEAD"
        if not autopilot_mode and aircraft_alive:
            # Map action back to labels if in manual mode
            manual_action_label = {0: "L-Turn", 2: "R-Turn", 1: "Steady"}.get(action, "Steady")
            active_bt_state = f"MANUAL: {manual_action_label}"

        # Calculate running stats
        avg_reward = sum(past_episode_rewards) / max(1, len(past_episode_rewards))
        success_rate = sum(episode_success_history) / max(1, len(episode_success_history))
        if len(episode_success_history) == 0:
            success_rate = 1.0  # Default to 100% initially

        # Prepare summary packet for HUD
        summary_data = {
            "current_episode": current_episode,
            "steps_count": steps_count,
            "episode_reward": episode_reward,
            "waypoints_reached": waypoints_reached_count,
            "done": done
        }

        # Draw the complete overhauled visualization dashboard
        renderer.draw(
            surface=screen,
            aircraft=aircraft,
            missile=missile,
            waypoint=waypoint,
            active_behavior=active_bt_state,
            current_reward=reward if (aircraft_alive or missile_hit) else 0.0,
            reward_breakdown=reward_breakdown,
            summary_data=summary_data,
            average_reward=avg_reward,
            success_rate=success_rate,
            autopilot_mode=autopilot_mode,
            fps=clock.get_fps(),
            aircraft_alive=aircraft_alive,
            ppo_probabilities=None,
            episode_outcome="FAILED" if (waiting_for_respawn and missile_hit) else ("SUCCESS" if waiting_for_respawn else None)
        )

        # Refresh screen
        pygame.display.flip()

        # Frame rate lock (60 FPS)
        clock.tick(60)

    # Safely close Pygame
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()