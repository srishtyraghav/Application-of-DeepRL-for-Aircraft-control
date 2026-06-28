import random
import pygame
import config

class Waypoint:
    """
    Represents a navigation target for the aircraft.
    When reached, it respawns at a new random location.
    """
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        # Automatically choose a starting position
        self.respawn()

    def respawn(self):
        """
        Randomly select a new position for the waypoint.
        We include a 100-pixel margin from the borders so the waypoint
        is fully visible and easy to navigate to.
        """
        margin = 100
        self.x = float(random.randint(margin, config.SCREEN_WIDTH - margin))
        self.y = float(random.randint(margin, config.SCREEN_HEIGHT - margin))

    def draw(self, screen):
        """
        Draw the waypoint on the screen.
        It is rendered as a green circle with a white center dot.
        """
        # Outer green target circle
        pygame.draw.circle(
            screen,
            config.COLOR_WAYPOINT,
            (int(self.x), int(self.y)),
            int(config.WAYPOINT_RADIUS)
        )
        
        # Inner white indicator dot
        pygame.draw.circle(
            screen,
            config.COLOR_WHITE,
            (int(self.x), int(self.y)),
            2
        )
