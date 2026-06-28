import math
import random
import pygame
import config

class Missile:
    """
    Represents a homing missile threat.
    It spawns at screen edges, tracks the aircraft, and explodes on contact.
    """
    def __init__(self):
        # Position coordinates
        self.x = 0.0
        self.y = 0.0
        
        # Heading angle in radians (for drawing the tail flame)
        self.angle = 0.0
        
        # State flags
        self.active = False       # True when chasing the aircraft
        self.exploding = False    # True during the explosion animation
        
        # Frame counter to animate and time the explosion
        self.explosion_timer = 0
        
        # Speed of the missile in pixels per frame
        self.speed = config.MISSILE_SPEED
        
    def spawn(self):
        """
        Spawns the missile randomly on one of the four edges of the screen.
        """
        # Choose a random edge: 0=Left, 1=Right, 2=Top, 3=Bottom
        edge = random.randint(0, 3)
        
        if edge == 0:  # Spawn on Left Edge
            self.x = 0.0
            self.y = random.uniform(0, config.SCREEN_HEIGHT)
        elif edge == 1:  # Spawn on Right Edge
            self.x = float(config.SCREEN_WIDTH)
            self.y = random.uniform(0, config.SCREEN_HEIGHT)
        elif edge == 2:  # Spawn on Top Edge
            self.x = random.uniform(0, config.SCREEN_WIDTH)
            self.y = 0.0
        elif edge == 3:  # Spawn on Bottom Edge
            self.x = random.uniform(0, config.SCREEN_WIDTH)
            self.y = float(config.SCREEN_HEIGHT)
            
        # Activate the missile and reset explosion state
        self.active = True
        self.exploding = False
        self.explosion_timer = 0
        
    def explode(self):
        """
        Triggers the explosion sequence on collision.
        """
        self.active = False
        self.exploding = True
        self.explosion_timer = 0
        
    def update(self, target_x, target_y):
        """
        Updates the position or explosion progress of the missile.
        """
        # If the missile is in the process of exploding
        if self.exploding:
            self.explosion_timer += 1
            # Once the animation runs for its duration, deactivate completely
            if self.explosion_timer >= config.EXPLOSION_DURATION_FRAMES:
                self.exploding = False
                # The missile is now fully inert and ready to be reset
            return
            
        # If the missile is actively chasing the aircraft
        if self.active:
            # 1. Calculate direction vector to target
            dx = target_x - self.x
            dy = target_y - self.y
            
            # 2. Calculate straight-line distance
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 0:
                # 3. Normalize the direction vector (convert to unit length 1)
                # and multiply by speed to move a fixed step size
                self.x += (dx / distance) * self.speed
                self.y += (dy / distance) * self.speed
                
                # Update the heading angle of the missile
                self.angle = math.atan2(dy, dx)
                
    def draw(self, screen):
        """
        Draws either the active missile or the explosion blast on the screen.
        """
        # Case A: Draw the active flying missile
        if self.active:
            # Draw a small trailing flame behind the missile (opposite to direction of travel)
            trail_x = self.x - 12 * math.cos(self.angle)
            trail_y = self.y - 12 * math.sin(self.angle)
            pygame.draw.line(screen, config.COLOR_EXPLOSION_INNER, (self.x, self.y), (trail_x, trail_y), 4)
            
            # Draw the main missile body (Crimson circle)
            pygame.draw.circle(screen, config.COLOR_MISSILE, (int(self.x), int(self.y)), 7)
            # Draw a white core/ring for high visibility
            pygame.draw.circle(screen, config.COLOR_WHITE, (int(self.x), int(self.y)), 7, 1)
            
        # Case B: Draw the growing explosion circles
        elif self.exploding:
            # Calculate how far along the explosion is (fraction between 0.0 and 1.0)
            progress = self.explosion_timer / config.EXPLOSION_DURATION_FRAMES
            
            # The explosion circle grows over time
            max_radius = 50.0
            current_radius = int(max_radius * progress)
            
            if current_radius > 0:
                # Draw outer blast outline (Red color)
                pygame.draw.circle(screen, config.COLOR_EXPLOSION_OUTER, (int(self.x), int(self.y)), current_radius, 2)
                # Draw inner hot filled core (Orange color, slightly smaller)
                inner_radius = max(1, int(current_radius * 0.7))
                pygame.draw.circle(screen, config.COLOR_EXPLOSION_INNER, (int(self.x), int(self.y)), inner_radius)
