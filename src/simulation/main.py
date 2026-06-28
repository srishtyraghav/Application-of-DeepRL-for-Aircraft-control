import sys
import math
import pygame
import config
from aircraft import Aircraft
from missile import Missile
from waypoint import Waypoint
import behavior_tree

def main():
    # Initialize the Pygame framework
    pygame.init()

    # Configure the game window using settings in config.py
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("DRL Aircraft Control - Phase 4: Behavior Trees")

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

    # Timer before a missile appears (used for the initial/regular spawns)
    missile_spawn_timer = 0

    # Score tracker for waypoints reached
    waypoints_reached_count = 0

    # Aircraft lifecycle and state tracking variables
    aircraft_alive = True
    waiting_for_respawn = False
    respawn_timer = 0

    # Font for dashboard HUD
    font = pygame.font.SysFont("Arial", 16)

    # Main game loop
    running = True
    while running:
        # -----------------------------
        # Handle window events
        # -----------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # -------------------------------------------------
        # Aircraft Decision Making & Movement (Autopilot)
        # Only evaluate decisions and move if aircraft is alive
        # -------------------------------------------------
        if aircraft_alive:
            # 1. Update distance inputs for the Behavior Tree
            aircraft.distance_to_waypoint = math.sqrt(
                (waypoint.x - aircraft.x) ** 2 + (waypoint.y - aircraft.y) ** 2
            )
            
            if missile.active:
                aircraft.distance_to_missile = math.sqrt(
                    (missile.x - aircraft.x) ** 2 + (missile.y - aircraft.y) ** 2
                )
            else:
                aircraft.distance_to_missile = 9999.0  # Set to a very safe value
                
            # 2. Tick the Behavior Tree (runsSelector, evaluates Evade/Navigate)
            bt.tick(aircraft, missile, waypoint)
            
            # 3. Apply physics movement updates
            aircraft.update()
            
            # 4. Check if the aircraft has reached the waypoint target
            # Safe boundary distance to reach the waypoint (radius + buffer)
            if aircraft.distance_to_waypoint < (config.WAYPOINT_RADIUS + 12.0):
                waypoint.respawn()
                waypoints_reached_count += 1

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
        else:
            # Update missile tracking or explosion state
            # If the aircraft is hit, we pass its last frozen position to the missile
            missile.update(aircraft.x, aircraft.y)

            # Check for collision only if the missile is active and aircraft is alive
            if missile.active and aircraft_alive:
                dx = aircraft.x - missile.x
                dy = aircraft.y - missile.y
                distance = math.sqrt(dx ** 2 + dy ** 2)

                if distance < config.MISSILE_COLLISION_RADIUS:
                    # 1. Start the explosion sequence
                    missile.explode()
                    # 2. Mark the aircraft as dead (disables decisions/movement)
                    aircraft_alive = False

        # -----------------------------
        # Transition from Explosion to Respawn
        # -----------------------------
        # If the aircraft was hit, but we haven't started the respawn timer yet:
        if not aircraft_alive and not waiting_for_respawn:
            # If the missile explosion animation has finished (exploding turned False)
            if not missile.exploding:
                waiting_for_respawn = True
                respawn_timer = 0

        # -----------------------------
        # Respawn Timer Logic
        # -----------------------------
        if waiting_for_respawn:
            respawn_timer += 1
            # 3 seconds * 60 FPS = 180 frames
            if respawn_timer >= 180:
                # 1. Create a completely NEW Aircraft object at the center
                aircraft = Aircraft(
                    config.SCREEN_WIDTH // 2,
                    config.SCREEN_HEIGHT // 2,
                    speed=config.AIRCRAFT_START_SPEED,
                    angle=0.0,
                )
                # 2. Spawn a NEW missile immediately
                missile.spawn()
                # 3. Reset states
                aircraft_alive = True
                waiting_for_respawn = False
                respawn_timer = 0

        # -----------------------------
        # Drawing / Rendering
        # -----------------------------
        # Clear screen with premium Slate Navy background
        screen.fill(config.COLOR_BACKGROUND)

        # Draw the target waypoint
        if aircraft_alive or (not aircraft_alive and not waiting_for_respawn):
            waypoint.draw(screen)

        # Draw the aircraft ONLY if it is alive, OR during the explosion phase
        if aircraft_alive or (not aircraft_alive and not waiting_for_respawn):
            aircraft.draw(screen)

        # Draw the missile if it is active or exploding
        if missile.active or missile.exploding:
            missile.draw(screen)

        # -----------------------------
        # Render Dashboard HUD
        # -----------------------------
        angle_deg = math.degrees(aircraft.angle)

        # Determine the status text of the missile / game state
        if missile.active:
            status_text = "ACTIVE - CHASING!"
        elif missile.exploding:
            status_text = "EXPLODING - IMPACT!"
        elif waiting_for_respawn:
            seconds_left = 3.0 - (respawn_timer / 60.0)
            status_text = f"RESPAWNING - Aircraft in {max(0.0, seconds_left):.1f}s"
        else:
            seconds_left = config.MISSILE_SPAWN_DELAY_SEC - (missile_spawn_timer / 60.0)
            status_text = f"INACTIVE - Spawning in {max(0.0, seconds_left):.1f}s"

        # Read active behavior from Behavior Tree
        active_bt_state = bt.active_behavior if aircraft_alive else "NONE (AIRCRAFT DEAD)"

        dashboard_lines = [
            "Flight Status Dashboard",
            "-------------------------",
            f"Aircraft Position : X={aircraft.x:.1f}, Y={aircraft.y:.1f}",
            f"Aircraft Speed    : {aircraft.speed:.2f} px/frame",
            f"Aircraft Heading  : {angle_deg:.1f}°",
            f"Active Behavior   : {active_bt_state}",
            f"Missile Status    : {status_text}",
            f"Waypoints Reached : {waypoints_reached_count}",
            f"Dist to Waypoint  : {aircraft.distance_to_waypoint:.1f} px",
            f"Dist to Missile   : {('N/A' if not missile.active else f'{aircraft.distance_to_missile:.1f} px')}",
            "-------------------------",
            "State: Autopilot (Behavior Tree)"
        ]

        for idx, line in enumerate(dashboard_lines):
            # Highlight warning values in red
            if idx == 5 and "EvadeMissile" in line:
                text_color = (251, 146, 60) # Warning Orange
            elif idx == 6 and (missile.active or waiting_for_respawn):
                text_color = (239, 68, 68)  # Warning Red
            elif idx == 7:
                text_color = (34, 197, 94)  # Success Green
            else:
                text_color = (200, 200, 200) # Soft Gray

            text_surface = font.render(line, True, text_color)
            screen.blit(text_surface, (15, 15 + idx * 20))

        # Refresh screen
        pygame.display.flip()

        # Frame rate lock (60 FPS)
        clock.tick(60)

    # Safely close Pygame
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()