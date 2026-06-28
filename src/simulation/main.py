import sys
import math
import pygame
from aircraft import Aircraft

def main():
    # Initialize the Pygame framework
    pygame.init()
    
    # Configure the window details
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("DRL Aircraft Control - Phase 2: Aircraft Test")
    
    # Instantiate the clock to manage the frame rate
    clock = pygame.time.Clock()
    
    # Instantiate our Aircraft object in the center of the screen
    # Starting at (400, 300), speed = 3.0 pixels/frame, facing right (0 radians)
    aircraft = Aircraft(width // 2, height // 2, speed=3.0, angle=0.0)
    
    # Setup text rendering for our dashboard
    font = pygame.font.SysFont("Arial", 16)
    
    # Main simulation loop
    running = True
    while running:
        # 1. Event Handling (check if user wants to close the window)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        # 2. Check Keyboard Inputs for flight controls
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            aircraft.turn_left()
        if keys[pygame.K_RIGHT]:
            aircraft.turn_right()
        if keys[pygame.K_UP]:
            aircraft.accelerate()
        if keys[pygame.K_DOWN]:
            aircraft.decelerate()
            
        # 3. Physics Updates
        aircraft.update()
        
        # 4. Render/Drawing
        # Clear screen with a premium dark Navy Sky background (RGB: 15, 23, 42)
        screen.fill((15, 23, 42))
        
        # Draw the aircraft
        aircraft.draw(screen)
        
        # 5. Render dashboard text overlay
        angle_deg = math.degrees(aircraft.angle)
        dashboard_lines = [
            f"Flight Status Dashboard",
            f"-------------------------",
            f"Position: X={aircraft.x:.1f}, Y={aircraft.y:.1f}",
            f"Speed: {aircraft.speed:.2f} px/frame",
            f"Heading: {angle_deg:.1f}°",
            f"Controls: Arrows (Move/Turn)"
        ]
        
        # Draw each line of dashboard text in light gray
        for idx, line in enumerate(dashboard_lines):
            text_surf = font.render(line, True, (200, 200, 200))
            screen.blit(text_surf, (15, 15 + idx * 20))
            
        # Swap buffers to show the new drawn screen
        pygame.display.flip()
        
        # Limit speed to 60 FPS
        clock.tick(60)
        
    # Safely close the Pygame window when loop exits
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
