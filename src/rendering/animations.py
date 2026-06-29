import random
import pygame
import math

class BackgroundStar:
    """
    Represents a single background star with twinkling animation.
    """
    def __init__(self, width: int, height: int):
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.size = random.choice([1, 2, 2, 3])
        self.twinkle_speed = random.uniform(0.01, 0.05)
        self.time = random.uniform(0, 100.0)

    def update(self):
        self.time += self.twinkle_speed

    def draw(self, surface, screen_offset_x: int, screen_offset_y: int):
        brightness = int(100 + 155 * math.sin(self.time))
        brightness = max(0, min(255, brightness))
        color = (brightness, brightness, brightness)
        
        draw_x = screen_offset_x + self.x
        draw_y = screen_offset_y + self.y
        
        if self.size == 1:
            surface.set_at((draw_x, draw_y), color)
        else:
            pygame.draw.circle(surface, color, (draw_x, draw_y), self.size // 2)

class BackgroundCloud:
    """
    Represents a slow-moving translucent clouds to represent wind drift.
    """
    def __init__(self, max_width: int, max_height: int):
        self.max_width = max_width
        self.max_height = max_height
        self.reset(start_on_screen=False)

    def reset(self, start_on_screen=True):
        self.size = random.randint(50, 120)
        self.speed = random.uniform(0.05, 0.2)
        self.alpha = random.randint(8, 18)  # Faint opacity
        self.y = random.randint(50, self.max_height - 50)
        
        if start_on_screen:
            self.x = random.randint(0, self.max_width)
        else:
            self.x = -self.size * 2

    def update(self):
        self.x += self.speed
        if self.x > self.max_width + self.size * 2:
            self.reset(start_on_screen=False)

    def draw(self, surface, screen_offset_x: int, screen_offset_y: int):
        surf = pygame.Surface((self.size * 3, self.size * 2), pygame.SRCALPHA)
        color = (100, 116, 139, self.alpha)  # Translucent Slate Blue-Gray Cloud
        
        pygame.draw.circle(surf, color, (self.size, self.size), self.size // 2)
        pygame.draw.circle(surf, color, (int(self.size * 1.4), self.size), int(self.size * 0.6))
        pygame.draw.circle(surf, color, (int(self.size * 0.7), int(self.size * 1.15)), int(self.size * 0.45))
        
        surface.blit(surf, (screen_offset_x + int(self.x) - self.size, screen_offset_y + self.y - self.size))

class AnimationManager:
    """
    Manages atmospheric animations and draws a dynamic tilting HUD horizon pitch ladder.
    """
    def __init__(self, screen_w=800, screen_h=600):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.stars = [BackgroundStar(screen_w, screen_h) for _ in range(70)]
        self.clouds = [BackgroundCloud(screen_w, screen_h) for _ in range(5)]
        
        # Initialize fonts
        if not pygame.font.get_init():
            pygame.font.init()
        self.hud_font = pygame.font.SysFont("Arial", 8, bold=True)
        
        for cloud in self.clouds:
            cloud.reset(start_on_screen=True)

    def update(self):
        for star in self.stars:
            star.update()
        for cloud in self.clouds:
            cloud.update()

    def draw_background(self, surface, offset_x=250, offset_y=0):
        # Draw starfields and drifting clouds
        for star in self.stars:
            star.draw(surface, offset_x, offset_y)
        for cloud in self.clouds:
            cloud.draw(surface, offset_x, offset_y)

    def draw_pitch_ladder(self, surface, aircraft, offset_x=250, offset_y=0):
        """
        Renders a rotating military HUD pitch ladder in the background of simulation.
        The ladder tilts matching the aircraft heading roll.
        """
        center_x = offset_x + self.screen_w // 2
        center_y = offset_y + self.screen_h // 2
        
        # 1. Create a transparent drawing canvas for the pitch ladder
        ladder_size = 400
        ladder_surf = pygame.Surface((ladder_size, ladder_size), pygame.SRCALPHA)
        mid = ladder_size // 2
        
        hud_color = (6, 182, 212, 45)       # Cyan 500 with light transparency
        hud_text_color = (6, 182, 212, 70)  # Text slightly brighter
        
        # 2. Draw horizon line (center line)
        pygame.draw.line(ladder_surf, hud_color, (mid - 120, mid), (mid - 25, mid), 1)
        pygame.draw.line(ladder_surf, hud_color, (mid + 25, mid), (mid + 120, mid), 1)
        
        # Horizon center breaks (small tick marks pointing down)
        pygame.draw.line(ladder_surf, hud_color, (mid - 120, mid), (mid - 120, mid + 6), 1)
        pygame.draw.line(ladder_surf, hud_color, (mid + 120, mid), (mid + 120, mid + 6), 1)
        
        # 3. Draw Pitch Lines (e.g. +10, -10, +20, -20 degrees)
        pitch_lines = [
            (30, "10", True),    # +10 (above horizon)
            (-30, "-10", False),  # -10 (below horizon)
            (60, "20", True),    # +20
            (-60, "-20", False)   # -20
        ]
        
        for offset, label, is_positive in pitch_lines:
            y = mid - offset
            
            # Draw dashed or solid horizontal ticks
            if is_positive:
                # Positive pitch bars: Solid line with downward ticks on ends
                pygame.draw.line(ladder_surf, hud_color, (mid - 70, y), (mid - 20, y), 1)
                pygame.draw.line(ladder_surf, hud_color, (mid + 20, y), (mid + 70, y), 1)
                
                pygame.draw.line(ladder_surf, hud_color, (mid - 70, y), (mid - 70, y + 4), 1)
                pygame.draw.line(ladder_surf, hud_color, (mid + 70, y), (mid + 70, y + 4), 1)
            else:
                # Negative pitch bars: Dashed lines with upward ticks
                self.draw_dashed_line(ladder_surf, hud_color, (mid - 70, y), (mid - 20, y), dash_len=4, gap_len=3)
                self.draw_dashed_line(ladder_surf, hud_color, (mid + 20, y), (mid + 70, y), dash_len=4, gap_len=3)
                
                pygame.draw.line(ladder_surf, hud_color, (mid - 70, y), (mid - 70, y - 4), 1)
                pygame.draw.line(ladder_surf, hud_color, (mid + 70, y), (mid + 70, y - 4), 1)
                
            # Text pitch indicator labels
            lbl_surf = self.hud_font.render(label, True, hud_text_color)
            ladder_surf.blit(lbl_surf, (mid - 85, y - 5))
            ladder_surf.blit(lbl_surf, (mid + 75, y - 5))
            
        # 4. Rotate the pitch ladder relative to aircraft angle
        # Convert aircraft heading angle to degrees
        deg_angle = math.degrees(aircraft.angle)
        # Invert rotation so sky horizon moves oppositely to aircraft banking
        rotated_surf = pygame.transform.rotate(ladder_surf, -deg_angle - 90)
        
        # Center rotated surface in viewport
        rotated_rect = rotated_surf.get_rect(center=(center_x, center_y))
        surface.blit(rotated_surf, rotated_rect.topleft)

        # 5. Draw static boresight crosshair in center (represents nose of plane)
        bs_color = (34, 211, 238)  # Glowing Cyan 400
        # Airplane shape reticle
        pygame.draw.circle(surface, bs_color, (center_x, center_y), 2)
        pygame.draw.line(surface, bs_color, (center_x - 12, center_y), (center_x - 4, center_y), 2)
        pygame.draw.line(surface, bs_color, (center_x + 4, center_y), (center_x + 12, center_y), 2)
        pygame.draw.line(surface, bs_color, (center_x, center_y + 2), (center_x, center_y + 6), 2)

    def draw_dashed_line(self, surface, color, start, end, dash_len=5, gap_len=3):
        x1, y1 = start
        x2, y2 = end
        
        dx = x2 - x1
        dy = y2 - y1
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist == 0:
            return
            
        ux = dx / dist
        uy = dy / dist
        
        step = dash_len + gap_len
        num_dashes = int(dist / step)
        
        for i in range(num_dashes):
            sx = x1 + ux * i * step
            sy = y1 + uy * i * step
            ex = sx + ux * dash_len
            ey = sy + uy * dash_len
            pygame.draw.line(surface, color, (int(sx), int(sy)), (int(ex), int(ey)), 1)
