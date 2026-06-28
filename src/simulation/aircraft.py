import math
import pygame

class Aircraft:
    """
    Represents the 2D aircraft in the simulation.
    It tracks position, velocity, and orientation, and updates them based on physics rules.
    """
    def __init__(self, x, y, speed=3.0, angle=0.0):
        # Coordinates on the 2D simulation window
        self.x = x
        self.y = y
        
        # Flight dynamics parameters
        self.speed = speed
        self.angle = angle  # Heading angle in radians (0 is right, positive is clockwise)
        
        # Flight boundaries/limits
        self.min_speed = 1.5      # Stall limit (aircraft cannot stop in mid-air)
        self.max_speed = 6.0      # Maximum engine speed limit
        self.acceleration = 0.05  # How fast the aircraft gains/loses speed
        self.turn_rate = 0.04     # Maximum heading angle change per frame (approx. 2.3 degrees)
        
        # Visual size parameters
        self.size = 15.0  # Size of the aircraft triangle
        
    def accelerate(self):
        """Increase the speed, capped at max_speed."""
        self.speed = min(self.speed + self.acceleration, self.max_speed)
        
    def decelerate(self):
        """Decrease the speed, bounded by min_speed to prevent stalling."""
        self.speed = max(self.speed - self.acceleration, self.min_speed)
        
    def turn_left(self):
        """Rotate heading angle counter-clockwise."""
        self.angle -= self.turn_rate
        # Keep the angle clean within -pi to pi range
        self.angle = (self.angle + math.pi) % (2 * math.pi) - math.pi
        
    def turn_right(self):
        """Rotate heading angle clockwise."""
        self.angle += self.turn_rate
        # Keep the angle clean within -pi to pi range
        self.angle = (self.angle + math.pi) % (2 * math.pi) - math.pi
        
    def update(self):
        """
        Move the aircraft forward based on its current speed and direction.
        This uses basic trigonometry:
        - cos(angle) gives the fraction of speed moving horizontally (x)
        - sin(angle) gives the fraction of speed moving vertically (y)
        """
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)

        # Wrap around the screen
        self.x %= 800
        self.y %= 600
        
    def draw(self, screen):
        """
        Draw the aircraft as a triangle pointing in the direction of its angle.
        
        We calculate 3 points:
        1. Nose (pointing forward)
        2. Left Wing (back and to the left)
        3. Right Wing (back and to the right)
        """
        # 1. Calculate nose position (pointing in the heading direction)
        nose_x = self.x + self.size * math.cos(self.angle)
        nose_y = self.y + self.size * math.sin(self.angle)
        
        # 2. Calculate wing positions (140 degrees away from the nose vector to make a swept-wing shape)
        wing_angle_offset = math.radians(140)
        
        left_wing_x = self.x + self.size * 0.8 * math.cos(self.angle + wing_angle_offset)
        left_wing_y = self.y + self.size * 0.8 * math.sin(self.angle + wing_angle_offset)
        
        right_wing_x = self.x + self.size * 0.8 * math.cos(self.angle - wing_angle_offset)
        right_wing_y = self.y + self.size * 0.8 * math.sin(self.angle - wing_angle_offset)
        
        points = [
            (nose_x, nose_y),
            (left_wing_x, left_wing_y),
            (self.x, self.y),  # Tail center point to make it look like a chevron/plane
            (right_wing_x, right_wing_y)
        ]
        
        # Draw the aircraft as a sleek blue filled polygon with a white border
        pygame.draw.polygon(screen, (30, 144, 255), points)       # Dodger Blue body
        pygame.draw.polygon(screen, (255, 255, 255), points, 2)   # White border
