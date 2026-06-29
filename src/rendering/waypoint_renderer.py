import math
import pygame

class WaypointRenderer:
    """
    Overhauls the target waypoint into an animated military radar beacon:
    - Rotating radar scan crosshair reticle.
    - Pulsing square lock box coordinates.
    - Translucent green dashed vector path line.
    """
    def __init__(self):
        self.pulse_timer = 0.0
        self.rotate_angle = 0.0

    def update(self):
        self.pulse_timer += 0.08
        self.rotate_angle += 0.02
        if self.pulse_timer > 2 * math.pi:
            self.pulse_timer -= 2 * math.pi
        if self.rotate_angle > 2 * math.pi:
            self.rotate_angle -= 2 * math.pi

    def draw(self, surface, waypoint, aircraft, offset_x=250, offset_y=0, alive=True):
        self.update()
        
        wp_cx = offset_x + int(waypoint.x)
        wp_cy = offset_y + int(waypoint.y)

        # 1. Renders translucent neon dashed guideline from aircraft to waypoint
        if alive:
            self.draw_dashed_line(
                surface, 
                (34, 211, 238, 120),  # Neon Cyan 400 with alpha
                (offset_x + int(aircraft.x), offset_y + int(aircraft.y)),
                (wp_cx, wp_cy),
                dash_len=8,
                gap_len=6
            )

        # 2. Draw outer concentric radar dotted circle
        radar_rad = 22
        radar_surf = pygame.Surface((radar_rad * 2, radar_rad * 2), pygame.SRCALPHA)
        # Draw thin dotted cyan circle
        pygame.draw.circle(radar_surf, (34, 211, 238, 50), (radar_rad, radar_rad), radar_rad, 1)
        surface.blit(radar_surf, (wp_cx - radar_rad, wp_cy - radar_rad))

        # 3. Draw pulsing locking square box
        box_size = 14 + int(3.5 * math.sin(self.pulse_timer))
        box_color = (34, 211, 238, 150) # Cyan 400
        
        # Create a surface for glassmorphic box blitting
        box_surf = pygame.Surface((box_size * 2, box_size * 2), pygame.SRCALPHA)
        box_rect = pygame.Rect(0, 0, box_size * 2, box_size * 2)
        # Draw neon corners of box only (sci-fi bracket style)
        b_len = 4
        # Top-Left corner
        pygame.draw.line(box_surf, box_color, (0, 0), (b_len, 0), 1)
        pygame.draw.line(box_surf, box_color, (0, 0), (0, b_len), 1)
        # Top-Right
        pygame.draw.line(box_surf, box_color, (box_size * 2 - 1, 0), (box_size * 2 - 1 - b_len, 0), 1)
        pygame.draw.line(box_surf, box_color, (box_size * 2 - 1, 0), (box_size * 2 - 1, b_len), 1)
        # Bottom-Left
        pygame.draw.line(box_surf, box_color, (0, box_size * 2 - 1), (b_len, box_size * 2 - 1), 1)
        pygame.draw.line(box_surf, box_color, (0, box_size * 2 - 1), (0, box_size * 2 - 1 - b_len), 1)
        # Bottom-Right
        pygame.draw.line(box_surf, box_color, (box_size * 2 - 1, box_size * 2 - 1), (box_size * 2 - 1 - b_len, box_size * 2 - 1), 1)
        pygame.draw.line(box_surf, box_color, (box_size * 2 - 1, box_size * 2 - 1), (box_size * 2 - 1, box_size * 2 - 1 - b_len), 1)

        surface.blit(box_surf, (wp_cx - box_size, wp_cy - box_size))

        # 4. Draw rotating radar scan reticle (4 crosshair notches)
        notches = [0, math.pi/2, math.pi, 3*math.pi/2]
        cross_len = 6
        cross_start = 2
        for angle in notches:
            final_a = angle + self.rotate_angle
            sx = wp_cx + math.cos(final_a) * cross_start
            sy = wp_cy + math.sin(final_a) * cross_start
            ex = wp_cx + math.cos(final_a) * (cross_start + cross_len)
            ey = wp_cy + math.sin(final_a) * (cross_start + cross_len)
            pygame.draw.line(
    surface,
    (34, 211, 238),
    (int(sx), int(sy)),
    (int(ex), int(ey)),
    2
)

        # 5. Draw waypoint hot core
        pygame.draw.circle(surface, (34, 211, 238), (wp_cx, wp_cy), 2)

    def draw_dashed_line(self, surface, color, start_pos, end_pos, width=1, dash_len=8, gap_len=6):
        x1, y1 = start_pos
        x2, y2 = end_pos
        dx = x2 - x1
        dy = y2 - y1
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0:
            return
        ux = dx / dist
        uy = dy / dist
        step = dash_len + gap_len
        num_dashes = int(dist / step)
        
        # Batch transparent drawings
        for i in range(num_dashes):
            sx = x1 + ux * i * step
            sy = y1 + uy * i * step
            ex = sx + ux * dash_len
            ey = sy + uy * dash_len
            
            # Since standard line drawing doesn't support alpha values natively,
            # we draw on a tiny segment surface and blit it.
            seg_w = max(1, int(abs(ex - sx))) + 2
            seg_h = max(1, int(abs(ey - sy))) + 2
            min_x = min(sx, ex) - 1
            min_y = min(sy, ey) - 1
            
            temp_surf = pygame.Surface((seg_w, seg_h), pygame.SRCALPHA)
            pygame.draw.line(
                temp_surf, 
                color, 
                (int(sx - min_x), int(sy - min_y)), 
                (int(ex - min_x), int(ey - min_y)), 
                int(width)
            )
            surface.blit(temp_surf, (min_x, min_y))
