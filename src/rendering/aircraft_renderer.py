import math
import random
import pygame

class ExhaustParticle:
    def __init__(self, x, y, angle, speed):
        spread = random.uniform(-0.1, 0.1)
        self.x = x
        self.y = y
        self.vx = -math.cos(angle + spread) * speed * random.uniform(0.5, 1.0)
        self.vy = -math.sin(angle + spread) * speed * random.uniform(0.5, 1.0)
        self.life = random.randint(10, 20)
        self.max_life = self.life
        self.size = random.randint(2, 5)
        self.color_start = (34, 211, 238)  # Hot Cyan core
        self.color_end = (71, 85, 105)      # Slate gray tail

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, surface, offset_x, offset_y):
        if self.life <= 0:
            return
        ratio = self.life / self.max_life
        r = int(self.color_end[0] + (self.color_start[0] - self.color_end[0]) * ratio)
        g = int(self.color_end[1] + (self.color_start[1] - self.color_end[1]) * ratio)
        b = int(self.color_end[2] + (self.color_start[2] - self.color_end[2]) * ratio)
        alpha = int(220 * ratio)
        
        temp = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(temp, (r, g, b, alpha), (self.size, self.size), self.size)
        surface.blit(temp, (offset_x + int(self.x) - self.size, offset_y + int(self.y) - self.size))

class AircraftRenderer:
    """
    Renders a highly detailed twin-engine jet model utilizing matrix coordinates 
    rotation to prevent distortion. Includes dynamic canopy glares, wingtip rails, 
    and twin pulsating afterburner exhausts.
    """
    def __init__(self, interpolation_rate=0.2):
        self.drawn_angle = None
        self.interpolation_rate = interpolation_rate
        self.particles = []
        self.pulse_timer = 0.0

    def rotate_point(self, pt, cos_a, sin_a):
        x, y = pt
        rx = x * cos_a - y * sin_a
        ry = x * sin_a + y * cos_a
        return rx, ry

    def update_particles(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface, aircraft, offset_x=250, offset_y=0, alive=True):
        # Interpolate heading angle smoothly
        target_angle = aircraft.angle
        if self.drawn_angle is None:
            self.drawn_angle = target_angle
        else:
            angle_diff = (target_angle - self.drawn_angle + math.pi) % (2 * math.pi) - math.pi
            self.drawn_angle += angle_diff * self.interpolation_rate
            self.drawn_angle = (self.drawn_angle + math.pi) % (2 * math.pi) - math.pi

        self.pulse_timer += 0.4
        cos_a = math.cos(self.drawn_angle)
        sin_a = math.sin(self.drawn_angle)

        # Local Jet coordinates relative to Center (0, 0):
        # Fuselage Main body
        fuselage_pts = [
            (25, 0),    # Nose
            (10, 4),    # Forward canopy right
            (-15, 4),   # Fuselage right
            (-22, 2),   # Engine nozzle right
            (-22, -2),  # Engine nozzle left
            (-15, -4),  # Fuselage left
            (10, -4),   # Forward canopy left
        ]

        # Swept Main Wings
        left_wing_pts = [
            (-3, -4),     # Wing root forward
            (-16, -26),   # Wing tip forward
            (-20, -26),   # Wing tip trailing
            (-14, -4)     # Wing root trailing
        ]
        right_wing_pts = [
            (-3, 4),
            (-16, 26),
            (-20, 26),
            (-14, 4)
        ]

        # Horizontal Stabilizers (Tail Wings)
        left_stabilizer_pts = [
            (-16, -4),    # Root forward
            (-22, -13),   # Tip forward
            (-24, -13),   # Tip trailing
            (-22, -2)     # Root trailing
        ]
        right_stabilizer_pts = [
            (-16, 4),
            (-22, 13),
            (-24, 13),
            (-22, 2)
        ]

        # Twin engine exhausts emitter coordinates
        left_nozzle_local = (-22, -2.5)
        right_nozzle_local = (-22, 2.5)

        # 1. Emit exhaust particles (Only when alive and moving)
        if alive and aircraft.speed > 0:
            for nozzle in [left_nozzle_local, right_nozzle_local]:
                rx, ry = self.rotate_point(nozzle, cos_a, sin_a)
                ex = aircraft.x + rx
                ey = aircraft.y + ry
                self.particles.append(ExhaustParticle(ex, ey, self.drawn_angle, aircraft.speed))
                if random.random() > 0.6:
                    self.particles.append(ExhaustParticle(ex, ey, self.drawn_angle, aircraft.speed))

        # Update and draw exhaust particles
        self.update_particles()
        for p in self.particles:
            p.draw(surface, offset_x, offset_y)

        # 2. Draw afterburner flames (Only when alive and moving)
        if alive and aircraft.speed > 0:
            flame_len = 10 + 4 * math.sin(self.pulse_timer)
            flame_color = (6, 182, 212, 180)  # Translucent Cyan
            for nozzle in [left_nozzle_local, right_nozzle_local]:
                rx_nz, ry_nz = self.rotate_point(nozzle, cos_a, sin_a)
                nz_tip_local = (nozzle[0] - flame_len, nozzle[1])
                rx_tip, ry_tip = self.rotate_point(nz_tip_local, cos_a, sin_a)
                
                # Left nozzle flame polygon
                nz_side_l = (nozzle[0], nozzle[1] - 2)
                nz_side_r = (nozzle[0], nozzle[1] + 2)
                rx_sl, ry_sl = self.rotate_point(nz_side_l, cos_a, sin_a)
                rx_sr, ry_sr = self.rotate_point(nz_side_r, cos_a, sin_a)
                
                flame_pts = [
                    (int(offset_x + aircraft.x + rx_sl), int(offset_y + aircraft.y + ry_sl)),
                    (int(offset_x + aircraft.x + rx_tip), int(offset_y + aircraft.y + ry_tip)),
                    (int(offset_x + aircraft.x + rx_sr), int(offset_y + aircraft.y + ry_sr))
                ]
                
                temp_flame = pygame.Surface((800, 600), pygame.SRCALPHA)
                pygame.draw.polygon(temp_flame, flame_color, flame_pts)
                surface.blit(temp_flame, (0, 0))

        # Set color scheme based on alive/wreckage state
        if alive:
            wing_color = (100, 116, 139)       # Slate 500
            stab_color = (71, 85, 105)         # Slate 600
            fuse_color = (148, 163, 184)       # Slate 400
            border_color = (255, 255, 255)     # High-contrast white skeleton
            canopy_color = (34, 211, 238, 180) # Cyan canopy
        else:
            # Wreckage color theme (dark metallic gray colors)
            wing_color = (55, 65, 81)          # Slate 700
            stab_color = (31, 41, 55)          # Slate 900
            fuse_color = (75, 85, 99)          # Slate 600
            border_color = (55, 65, 81)        # Slate 700 skeleton
            canopy_color = (15, 23, 42, 100)   # Dark inert glass

        # 3. Draw Jet Wings & Fuselage parts
        parts = [
            (left_wing_pts, wing_color),
            (right_wing_pts, wing_color),
            (left_stabilizer_pts, stab_color),
            (right_stabilizer_pts, stab_color),
            (fuselage_pts, fuse_color)
        ]

        for pts, color in parts:
            rot_pts = []
            for p in pts:
                rx, ry = self.rotate_point(p, cos_a, sin_a)
                rot_pts.append((int(offset_x + aircraft.x + rx), int(offset_y + aircraft.y + ry)))
            pygame.draw.polygon(surface, color, rot_pts)
            pygame.draw.polygon(surface, border_color, rot_pts, 1)

        # 4. Draw Wingtip missile rails (Only when alive)
        if alive:
            wingtips = [(-18, -26), (-18, 26)]
            for tip in wingtips:
                rx, ry = self.rotate_point(tip, cos_a, sin_a)
                tx = int(offset_x + aircraft.x + rx)
                ty = int(offset_y + aircraft.y + ry)
                
                # Tiny line tip
                rx_t2, ry_t2 = self.rotate_point((tip[0] + 5, tip[1]), cos_a, sin_a)
                t2_x = int(offset_x + aircraft.x + rx_t2)
                t2_y = int(offset_y + aircraft.y + ry_t2)
                pygame.draw.line(surface, (34, 211, 238), (tx, ty), (t2_x, t2_y), 2) # Cyan 400

        # 5. Draw Glass Canopy
        canopy_pts = [
            (8, 0),
            (2, 2.5),
            (-7, 2.5),
            (-10, 0),
            (-7, -2.5),
            (2, -2.5)
        ]
        rot_canopy = []
        for p in canopy_pts:
            rx, ry = self.rotate_point(p, cos_a, sin_a)
            rot_canopy.append((int(offset_x + aircraft.x + rx), int(offset_y + aircraft.y + ry)))
        
        # Draw canopy
        canopy_surf = pygame.Surface((800, 600), pygame.SRCALPHA)
        pygame.draw.polygon(canopy_surf, canopy_color, rot_canopy)
        surface.blit(canopy_surf, (0, 0))
        pygame.draw.polygon(surface, border_color, rot_canopy, 1)
