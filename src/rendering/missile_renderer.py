import math
import random
import pygame

class SmokeParticle:
    def __init__(self, x, y, angle):
        spread = random.uniform(-0.2, 0.2)
        self.x = x
        self.y = y
        self.vx = -math.cos(angle + spread) * 1.2 * random.uniform(0.5, 1.0)
        self.vy = -math.sin(angle + spread) * 1.2 * random.uniform(0.5, 1.0)
        self.life = random.randint(15, 30)
        self.max_life = self.life
        self.size = random.randint(3, 6)
        # Military rocket exhaust color (glowing orange to dark gray smoke)
        self.color = random.choice([
            (249, 115, 22), # Orange 500
            (239, 68, 68),  # Red 500
            (100, 116, 139) # Slate 500 smoke
        ])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, surface, offset_x, offset_y):
        if self.life <= 0:
            return
        ratio = self.life / self.max_life
        alpha = int(140 * ratio)
        current_size = int(self.size * (1.3 - ratio * 0.3))
        
        temp_surf = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            temp_surf, 
            (self.color[0], self.color[1], self.color[2], alpha), 
            (current_size, current_size), 
            current_size
        )
        surface.blit(temp_surf, (offset_x + int(self.x) - current_size, offset_y + int(self.y) - current_size))

class MissileRenderer:
    """
    Renders the missile as a cylindrical weapon casing with stabilizer fins 
    and guidance nose. Exits into hot shockwaves upon impact.
    """
    def __init__(self):
        self.particles = []
        self.casing_len = 10.0
        self.casing_width = 2.0
        self.pulse = 0.0

    def rotate_point(self, pt, cos_a, sin_a):
        x, y = pt
        rx = x * cos_a - y * sin_a
        ry = x * sin_a + y * cos_a
        return rx, ry

    def update_particles(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface, missile, offset_x=250, offset_y=0):
        self.pulse += 0.5
        cos_a = math.cos(missile.angle)
        sin_a = math.sin(missile.angle)

        # 1. Update and draw trailing smoke particles
        if missile.active:
            emitter_x = missile.x - self.casing_len * cos_a
            emitter_y = missile.y - self.casing_len * sin_a
            self.particles.append(SmokeParticle(emitter_x, emitter_y, missile.angle))
            if random.random() > 0.5:
                self.particles.append(SmokeParticle(emitter_x, emitter_y, missile.angle))

        self.update_particles()
        for p in self.particles:
            p.draw(surface, offset_x, offset_y)

        # 2. Draw Active Missile Casing Shape
        if missile.active:
            # Missile Fuselage (white cylinder)
            casing_pts = [
                (self.casing_len, -self.casing_width),
                (self.casing_len, self.casing_width),
                (-self.casing_len, self.casing_width),
                (-self.casing_len, -self.casing_width)
            ]
            rot_casing = []
            for p in casing_pts:
                rx, ry = self.rotate_point(p, cos_a, sin_a)
                rot_casing.append((int(offset_x + missile.x + rx), int(offset_y + missile.y + ry)))
            pygame.draw.polygon(surface, (241, 245, 249), rot_casing) # Slate 50 white body
            pygame.draw.polygon(surface, (255, 255, 255), rot_casing, 1)

            # Red Nose Cone (guided dome)
            nose_pts = [
                (self.casing_len, -self.casing_width),
                (self.casing_len + 4, 0),
                (self.casing_len, self.casing_width)
            ]
            rot_nose = []
            for p in nose_pts:
                rx, ry = self.rotate_point(p, cos_a, sin_a)
                rot_nose.append((int(offset_x + missile.x + rx), int(offset_y + missile.y + ry)))
            pygame.draw.polygon(surface, (239, 68, 68), rot_nose) # Red 500 nose

            # Tail fins (military fins)
            left_fin_pts = [
                (-self.casing_len + 2, -self.casing_width),
                (-self.casing_len - 1, -self.casing_width - 3),
                (-self.casing_len - 2, -self.casing_width - 3),
                (-self.casing_len, -self.casing_width)
            ]
            right_fin_pts = [
                (-self.casing_len + 2, self.casing_width),
                (-self.casing_len - 1, self.casing_width + 3),
                (-self.casing_len - 2, self.casing_width + 3),
                (-self.casing_len, self.casing_width)
            ]
            for fin in [left_fin_pts, right_fin_pts]:
                rot_fin = []
                for p in fin:
                    rx, ry = self.rotate_point(p, cos_a, sin_a)
                    rot_fin.append((int(offset_x + missile.x + rx), int(offset_y + missile.y + ry)))
                pygame.draw.polygon(surface, (239, 68, 68), rot_fin)

            # Draw pulsating exhaust nozzles flare (orange)
            flame_len = 5 + 3 * math.sin(self.pulse)
            flame_pts = [
                (-self.casing_len, -1.5),
                (-self.casing_len - flame_len, 0),
                (-self.casing_len, 1.5)
            ]
            rot_flame = []
            for p in flame_pts:
                rx, ry = self.rotate_point(p, cos_a, sin_a)
                rot_flame.append((int(offset_x + missile.x + rx), int(offset_y + missile.y + ry)))
            pygame.draw.polygon(surface, (249, 115, 22), rot_flame)

        # 3. Draw contact shockwave explosion rings
        elif missile.exploding:
            progress = missile.explosion_timer / 60.0
            progress = min(1.0, max(0.0, progress))
            
            max_radius = 65.0
            # Ease-out scale
            current_radius = int(max_radius * (1.0 - (1.0 - progress)**3))
            
            if current_radius > 0:
                alpha = int(255 * (1.0 - progress))
                
                # Expand shockwave ring
                shock_surf = pygame.Surface((current_radius * 2, current_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    shock_surf, 
                    (239, 68, 68, alpha), 
                    (current_radius, current_radius), 
                    current_radius, 
                    4
                )
                surface.blit(shock_surf, (offset_x + int(missile.x) - current_radius, offset_y + int(missile.y) - current_radius))
                
                # Inner combustion orange core
                core_radius = max(1, int(current_radius * 0.7))
                core_surf = pygame.Surface((core_radius * 2, core_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    core_surf, 
                    (249, 115, 22, int(alpha * 0.8)), 
                    (core_radius, core_radius), 
                    core_radius
                )
                surface.blit(core_surf, (offset_x + int(missile.x) - core_radius, offset_y + int(missile.y) - core_radius))
                
                # White-hot fire flash center
                flash_radius = max(1, int(current_radius * 0.3))
                flash_surf = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    flash_surf, 
                    (254, 240, 138, int(alpha * 0.9)), 
                    (flash_radius, flash_radius), 
                    flash_radius
                )
                surface.blit(flash_surf, (offset_x + int(missile.x) - flash_radius, offset_y + int(missile.y) - flash_radius))
