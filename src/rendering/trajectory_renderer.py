import pygame

class TrajectoryRenderer:
    """
    Manages and draws fading path history trails for the aircraft and missile.
    """
    def __init__(self, max_aircraft_points=300, max_missile_points=150):
        self.aircraft_points = []
        self.missile_points = []
        self.max_aircraft_points = max_aircraft_points
        self.max_missile_points = max_missile_points

    def add_aircraft_point(self, x, y, alive=True):
        if alive:
            self.aircraft_points.append((x, y))
            if len(self.aircraft_points) > self.max_aircraft_points:
                self.aircraft_points.pop(0)
        else:
            # When dead, we don't append, but we can slowly fade out what's left
            pass

    def add_missile_point(self, x, y, active=True):
        if active:
            self.missile_points.append((x, y))
            if len(self.missile_points) > self.max_missile_points:
                self.missile_points.pop(0)
        else:
            # Fade out rapidly when inactive
            if self.missile_points:
                self.missile_points.pop(0)

    def clear(self):
        self.aircraft_points.clear()
        self.missile_points.clear()

    def draw(self, surface, screen_offset_x=250, screen_offset_y=0):
        # 1. Draw Aircraft Trajectory: Fading White Dotted Trail
        num_plane_points = len(self.aircraft_points)
        for idx, (x, y) in enumerate(self.aircraft_points):
            # Calculate alpha based on age (newer is brighter)
            alpha = int(255 * (idx / max(1, num_plane_points)))
            # Keep it faint but visible
            alpha = max(10, min(180, alpha))
            
            color = (226, 232, 240, alpha)  # Fading Slate 100
            
            # Create a transparent surface for drawing circles
            temp_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, color, (2, 2), 2)
            
            surface.blit(temp_surf, (screen_offset_x + int(x) - 2, screen_offset_y + int(y) - 2))

        # 2. Draw Missile Trajectory: Solid Fading Red Line
        num_missile_points = len(self.missile_points)
        if num_missile_points > 1:
            for idx in range(num_missile_points - 1):
                p1 = self.missile_points[idx]
                p2 = self.missile_points[idx + 1]
                
                # Fading red color
                alpha = int(255 * (idx / max(1, num_missile_points - 1)))
                alpha = max(10, min(220, alpha))
                color = (239, 68, 68, alpha)  # Red 500
                
                # Draw segment using standard line or AA line
                # Create a subsegment surface or draw directly if simple
                # To support alphas on lines, we draw on a transparent canvas
                # or draw thin lines. Given 2D screen width/height offset:
                line_start = (screen_offset_x + int(p1[0]), screen_offset_y + int(p1[1]))
                line_end = (screen_offset_x + int(p2[0]), screen_offset_y + int(p2[1]))
                
                # Draw thin lines directly with RGB (pygame draws alpha-less line quickly)
                # To maintain high visual quality, draw line with alpha using segment surface
                segment_w = abs(line_end[0] - line_start[0]) + 4
                segment_h = abs(line_end[1] - line_start[1]) + 4
                min_x = min(line_start[0], line_end[0]) - 2
                min_y = min(line_start[1], line_end[1]) - 2
                
                if segment_w > 0 and segment_h > 0:
                    temp_surf = pygame.Surface((segment_w, segment_h), pygame.SRCALPHA)
                    pygame.draw.line(
                        temp_surf, 
                        color, 
                        (line_start[0] - min_x, line_start[1] - min_y), 
                        (line_end[0] - min_x, line_end[1] - min_y), 
                        2
                    )
                    surface.blit(temp_surf, (min_x, min_y))
