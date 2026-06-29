import pygame
import math
from src.rendering.animations import AnimationManager
from src.rendering.trajectory_renderer import TrajectoryRenderer
from src.rendering.aircraft_renderer import AircraftRenderer
from src.rendering.missile_renderer import MissileRenderer
from src.rendering.waypoint_renderer import WaypointRenderer
from src.rendering.hud import HUD

class Renderer:
    """
    Master Renderer class orchestrating the entire 1350x650 aerospace dashboard.
    Renders glassmorphic sidebars, animated instrument tape dials, and the main 
    flight view.
    """
    def __init__(self):
        # Sub-components
        self.animations = AnimationManager(screen_w=800, screen_h=600)
        self.trajectories = TrajectoryRenderer()
        self.aircraft_render = AircraftRenderer()
        self.missile_render = MissileRenderer()
        self.waypoint_render = WaypointRenderer()
        self.hud = HUD()

        # Fonts
        if not pygame.font.get_init():
            pygame.font.init()
        self.font_title = pygame.font.SysFont("Arial", 11, bold=True)
        self.font_bold = pygame.font.SysFont("Arial", 10, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 10, bold=False)
        self.font_button = pygame.font.SysFont("Arial", 11, bold=True)
        self.font_pfd = pygame.font.SysFont("Arial", 9, bold=True)
        self.font_pfd_val = pygame.font.SysFont("Arial", 8, bold=False)

        # Tech colors
        self.c_bg_sidebar = (9, 15, 29)         # Cyber Navy
        self.c_bg_panel = (15, 23, 42, 200)     # Translucent Slate 900
        self.c_border_panel = (71, 85, 105, 150) # Slate 500
        self.c_active = (34, 211, 238)           # Neon Cyan 400
        self.c_title = self.c_active
        self.c_green = (34, 197, 94)             # Green 500
        self.c_red = (239, 68, 68)               # Red 500
        self.c_gray = (148, 163, 184)             # Slate 400

        # Clickable button rects (Left Column)
        self.btn_autopilot_rect = pygame.Rect(25, 520, 200, 32)
        self.btn_reset_rect = pygame.Rect(25, 565, 200, 32)

    def draw_left_panel(self, surface, autopilot_mode):
        """
        Draws the Left Column (Width: 250px, height: 650) as a glass touchscreen console.
        """
        left_rect = (0, 0, 250, 650)
        pygame.draw.rect(surface, self.c_bg_sidebar, left_rect)
        pygame.draw.line(surface, self.c_border_panel, (250, 0), (250, 650), 2)

        # Card 1: System Legend (x: 15, y: 15, w: 220, h: 150)
        legend_rect = pygame.Rect(15, 15, 220, 150)
        
        # Translucent glass blit
        legend_surf = pygame.Surface((220, 150), pygame.SRCALPHA)
        pygame.draw.rect(legend_surf, self.c_bg_panel, (0, 0, 220, 150), border_radius=8)
        pygame.draw.rect(legend_surf, self.c_border_panel, (0, 0, 220, 150), width=1, border_radius=8)
        
        # Corner brackets
        b_len = 4
        pygame.draw.line(legend_surf, self.c_active, (0, 0), (b_len, 0), 2)
        pygame.draw.line(legend_surf, self.c_active, (0, 0), (0, b_len), 2)
        pygame.draw.line(legend_surf, self.c_active, (219, 0), (219 - b_len, 0), 2)
        pygame.draw.line(legend_surf, self.c_active, (219, 0), (219, b_len), 2)
        pygame.draw.line(legend_surf, self.c_active, (0, 149), (b_len, 149), 2)
        pygame.draw.line(legend_surf, self.c_active, (0, 149), (0, 149 - b_len), 2)
        pygame.draw.line(legend_surf, self.c_active, (219, 149), (219 - b_len, 149), 2)
        pygame.draw.line(legend_surf, self.c_active, (219, 149), (219, 149 - b_len), 2)
        
        surface.blit(legend_surf, (15, 15))

        title_legend = self.font_title.render("COCKPIT ICON LEGEND", True, self.c_active)
        surface.blit(title_legend, (27, 23))

        legend_items = [
            ("Twin-Engine Fighter Jet", (34, 211, 238)),  # Cyan
            ("Homing Weapon Target", (239, 68, 68)),      # Red
            ("Radar Waypoint Beacon", (34, 197, 94)),     # Green
            ("Dotted Flight Trajectory", (255, 255, 255)),
            ("Translucent Target Guide", (34, 211, 238))
        ]

        for idx, (label, color) in enumerate(legend_items):
            y_pos = 42 + idx * 20
            sym_x = 30
            if idx == 0:  # Jet wings
                pygame.draw.polygon(surface, color, [(sym_x, y_pos + 10), (sym_x - 5, y_pos + 4), (sym_x - 5, y_pos + 16)])
                pygame.draw.polygon(surface, (255, 255, 255), [(sym_x, y_pos + 10), (sym_x - 5, y_pos + 4), (sym_x - 5, y_pos + 16)], 1)
            elif idx == 1: # Weapon Red tip
                pygame.draw.rect(surface, color, (sym_x - 6, y_pos + 7, 8, 4), border_radius=1)
                pygame.draw.polygon(surface, (255, 255, 255), [(sym_x + 2, y_pos + 7), (sym_x + 6, y_pos + 9), (sym_x + 2, y_pos + 11)])
            elif idx == 2: # Beacon crosshair
                pygame.draw.circle(surface, color, (sym_x - 3, y_pos + 10), 4, 1)
                pygame.draw.circle(surface, (255, 255, 255), (sym_x - 3, y_pos + 10), 1)
            elif idx == 3: # Path dots
                pygame.draw.circle(surface, color, (sym_x - 7, y_pos + 10), 2)
                pygame.draw.circle(surface, color, (sym_x - 3, y_pos + 10), 2)
                pygame.draw.circle(surface, color, (sym_x + 1, y_pos + 10), 2)
            elif idx == 4: # Guided neon line
                pygame.draw.line(surface, (34, 211, 238, 120), (sym_x - 8, y_pos + 10), (sym_x + 2, y_pos + 10), 1)

            lbl_surf = self.font_label.render(label, True, (255, 255, 255))
            surface.blit(lbl_surf, (45, y_pos + 4))

        # Card 2: Manual Control Bindings (x: 15, y: 175, w: 220, h: 460)
        controls_rect = pygame.Rect(15, 175, 220, 460)
        
        controls_surf = pygame.Surface((220, 460), pygame.SRCALPHA)
        pygame.draw.rect(controls_surf, self.c_bg_panel, (0, 0, 220, 460), border_radius=8)
        pygame.draw.rect(controls_surf, self.c_border_panel, (0, 0, 220, 460), width=1, border_radius=8)
        
        # Corner brackets
        pygame.draw.line(controls_surf, self.c_active, (0, 0), (b_len, 0), 2)
        pygame.draw.line(controls_surf, self.c_active, (0, 0), (0, b_len), 2)
        pygame.draw.line(controls_surf, self.c_active, (219, 0), (219 - b_len, 0), 2)
        pygame.draw.line(controls_surf, self.c_active, (219, 0), (219, b_len), 2)
        pygame.draw.line(controls_surf, self.c_active, (0, 459), (b_len, 459), 2)
        pygame.draw.line(controls_surf, self.c_active, (0, 459), (0, 459 - b_len), 2)
        pygame.draw.line(controls_surf, self.c_active, (219, 459), (219 - b_len, 459), 2)
        pygame.draw.line(controls_surf, self.c_active, (219, 459), (219, 459 - b_len), 2)

        surface.blit(controls_surf, (15, 175))

        title_controls = self.font_title.render("MANUAL CONTROL OVERRIDES", True, self.c_active)
        surface.blit(title_controls, (27, 183))

        bindings = [
            ("Autopilot System Mode", "Key 'M' / TOUCH BUTTON"),
            ("Abort / Force Reset", "Key 'R' / TOUCH BUTTON"),
            ("Accelerate Jet Thruster", "Key 'W' / Up Arrow"),
            ("Decelerate / Decel Flaps", "Key 'S' / Down Arrow"),
            ("Aileron Yaw Left", "Key 'A' / Left Arrow"),
            ("Aileron Yaw Right", "Key 'D' / Right Arrow"),
            ("Elevator Pitch Climb", "Spacebar"),
            ("Elevator Pitch Dive", "Left Shift / R-Shift")
        ]

        for idx, (action, bind) in enumerate(bindings):
            y_pos = 205 + idx * 30
            act_surf = self.font_bold.render(action, True, self.c_active)
            surface.blit(act_surf, (27, y_pos))
            bind_surf = self.font_label.render(bind, True, (255, 255, 255))
            surface.blit(bind_surf, (27, y_pos + 12))

        # Render Interactive Overlays Buttons
        mx, my = pygame.mouse.get_pos()
        
        # 1. Autopilot Button
        ap_hover = self.btn_autopilot_rect.collidepoint(mx, my)
        ap_color = (22, 101, 52) if autopilot_mode else (185, 28, 28) # green vs red
        if ap_hover:
            ap_color = (21, 128, 61) if autopilot_mode else (220, 38, 38)
            
        pygame.draw.rect(surface, ap_color, self.btn_autopilot_rect, border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), self.btn_autopilot_rect, width=1, border_radius=6)
        ap_txt = "SYSTEM AUTOPILOT: ON" if autopilot_mode else "SYSTEM AUTOPILOT: OFF"
        ap_surf = self.font_button.render(ap_txt, True, (255, 255, 255))
        surface.blit(ap_surf, (self.btn_autopilot_rect.x + (200 - ap_surf.get_width()) // 2, self.btn_autopilot_rect.y + 8))

        # 2. Reset Button
        rst_hover = self.btn_reset_rect.collidepoint(mx, my)
        rst_color = (30, 41, 59)
        if rst_hover:
            rst_color = (51, 65, 85)
            
        pygame.draw.rect(surface, rst_color, self.btn_reset_rect, border_radius=6)
        pygame.draw.rect(surface, self.c_border_panel, self.btn_reset_rect, width=1, border_radius=6)
        rst_surf = self.font_button.render("FORCE SIMULATOR RESET", True, (255, 255, 255))
        surface.blit(rst_surf, (self.btn_reset_rect.x + (200 - rst_surf.get_width()) // 2, self.btn_reset_rect.y + 8))

    def draw_bottom_bar(self, surface, rect, aircraft, missile, fps):
        """
        Draws the Bottom PFD instrument cockpit bar (800x50 px, starting x: 250, y: 600)
        featuring detailed rotating dials and sliding ladders.
        """
        pygame.draw.rect(surface, self.c_bg_panel, rect)
        pygame.draw.line(surface, self.c_border_panel, (rect[0], rect[1]), (rect[0] + rect[2], rect[1]), 2)

        heading_deg = (math.degrees(aircraft.angle) + 180) % 360 - 180
        if not hasattr(aircraft, "altitude"):
            aircraft.altitude = 2500.0

        # Number columns width
        col_w = rect[2] / 6.0
        center_y = rect[1] + 25

        # -----------------------------
        # Gauge 1: Heading Compass Dial (x: 250 + 60)
        # -----------------------------
        compass_x = rect[0] + 60
        pygame.draw.circle(surface, (71, 85, 105), (compass_x, center_y), 18, 1) # Dial ring
        # Draw needle pointing at angle
        nx = int(compass_x + math.cos(aircraft.angle) * 14)
        ny = int(center_y + math.sin(aircraft.angle) * 14)
        pygame.draw.line(surface, self.c_active, (compass_x, center_y), (nx, ny), 2)
        # Cardinal marks
        pygame.draw.line(surface, (255, 255, 255), (compass_x, center_y - 18), (compass_x, center_y - 14), 1)
        pygame.draw.line(surface, (255, 255, 255), (compass_x + 14, center_y), (compass_x + 18, center_y), 1)
        
        lbl_hdg = self.font_pfd.render("COMPASS", True, self.c_title)
        surface.blit(lbl_hdg, (compass_x + 24, center_y - 10))
        val_hdg = self.font_label.render(f"{heading_deg:.1f}°", True, (255, 255, 255))
        surface.blit(val_hdg, (compass_x + 24, center_y + 3))

        # -----------------------------
        # Gauge 2: Speed Meter Dial (x: 250 + 190)
        # -----------------------------
        speed_x = rect[0] + 190
        pygame.draw.circle(surface, (71, 85, 105), (speed_x, center_y), 18, 1)
        # Sweeping speed indicator (max speed = 6.0)
        spd_ratio = min(1.0, max(0.0, aircraft.speed / 6.0))
        spd_angle = -math.pi + spd_ratio * math.pi  # semi circle sweep
        sx = int(speed_x + math.cos(spd_angle) * 14)
        sy = int(center_y + math.sin(spd_angle) * 14)
        pygame.draw.line(surface, self.c_active, (speed_x, center_y), (sx, sy), 2)
        
        lbl_spd = self.font_pfd.render("AIRSPEED", True, self.c_title)
        surface.blit(lbl_spd, (speed_x + 24, center_y - 10))
        val_spd = self.font_label.render(f"{aircraft.speed:.2f} px/f", True, (255, 255, 255))
        surface.blit(val_spd, (speed_x + 24, center_y + 3))

        # -----------------------------
        # Gauge 3: Altitude Sliding tape (x: 250 + 330)
        # -----------------------------
        alt_x = rect[0] + 330
        pygame.draw.rect(surface, (30, 41, 59), (alt_x, rect[1] + 10, 10, 30), border_radius=2)
        # Slider indicator
        alt_ratio = min(1.0, max(0.0, aircraft.altitude / 5000.0))
        indicator_y = rect[1] + 40 - int(alt_ratio * 30)
        pygame.draw.circle(surface, self.c_active, (alt_x + 5, indicator_y), 3)

        lbl_alt = self.font_pfd.render("ALTITUDE", True, self.c_title)
        surface.blit(lbl_alt, (alt_x + 20, center_y - 10))
        val_alt = self.font_label.render(f"{aircraft.altitude:.1f}m", True, (255, 255, 255))
        surface.blit(val_alt, (alt_x + 20, center_y + 3))

        # -----------------------------
        # Info Columns 4 & 5: Targets & Threats
        # -----------------------------
        inf_x = rect[0] + 450
        lbl_inf1 = self.font_pfd.render("WAYPOINT DISTANCE", True, self.c_title)
        surface.blit(lbl_inf1, (inf_x, center_y - 10))
        val_inf1 = self.font_label.render(f"{aircraft.distance_to_waypoint:.1f} px", True, (255, 255, 255))
        surface.blit(val_inf1, (inf_x, center_y + 3))

        threat_x = rect[0] + 580
        lbl_thr = self.font_pfd.render("THREAT DISTANCE", True, self.c_title)
        surface.blit(lbl_thr, (threat_x, center_y - 10))
        
        is_close = missile.active and aircraft.distance_to_missile < 200.0
        val_thr_color = self.c_red if is_close else (self.c_gray if not missile.active else (255, 255, 255))
        missile_dist_str = "CLEAR (NO TARGET)" if not missile.active else f"{aircraft.distance_to_missile:.1f} px"
        val_thr = self.font_label.render(missile_dist_str, True, val_thr_color)
        surface.blit(val_thr, (threat_x, center_y + 3))

        # -----------------------------
        # Info Column 6: FPS Meter
        # -----------------------------
        fps_x = rect[0] + 710
        lbl_fps = self.font_pfd.render("SYSTEM FPS", True, self.c_title)
        surface.blit(lbl_fps, (fps_x, center_y - 10))
        val_fps = self.font_label.render(f"{fps:.1f}", True, (255, 255, 255))
        surface.blit(val_fps, (fps_x, center_y + 3))

    def draw_simulation_window(self, surface, aircraft, missile, waypoint, aircraft_alive, offset_x=250, offset_y=0):
        """
        Draws the center simulation window coordinates (800x600 px)
        """
        sim_rect = (offset_x, offset_y, 800, 600)
        pygame.draw.rect(surface, (8, 12, 24), sim_rect) # Space Black base
        
        # Draw subtle cyber radar grids (circular scanning grid from center)
        center_x = offset_x + 400
        center_y = offset_y + 300
        grid_color = (15, 23, 42)
        
        # Radial concentric rings
        for rad in [100, 200, 300, 400]:
            pygame.draw.circle(surface, grid_color, (center_x, center_y), rad, 1)
        # Radar diagonal dividers
        pygame.draw.line(surface, grid_color, (offset_x, offset_y), (offset_x + 800, offset_y + 600), 1)
        pygame.draw.line(surface, grid_color, (offset_x, offset_y + 600), (offset_x + 800, offset_y), 1)
        pygame.draw.line(surface, grid_color, (center_x, offset_y), (center_x, offset_y + 600), 1)
        pygame.draw.line(surface, grid_color, (offset_x, center_y), (offset_x + 800, center_y), 1)

        # Drifting stars & wind clouds background
        self.animations.update()
        self.animations.draw_background(surface, offset_x, offset_y)

        # DRAW NEON HUD PITCH LADDER rotating behind elements
        if aircraft_alive:
            self.animations.draw_pitch_ladder(surface, aircraft, offset_x, offset_y)

        # Trajectories (aircraft & missile)
        self.trajectories.add_aircraft_point(aircraft.x, aircraft.y, alive=aircraft_alive)
        self.trajectories.add_missile_point(missile.x, missile.y, active=missile.active)
        self.trajectories.draw(surface, offset_x, offset_y)

        # Waypoint beacon scanner reticle
        self.waypoint_render.draw(surface, waypoint, aircraft, offset_x, offset_y, alive=aircraft_alive)

        # Homing Missile threat rocket
        self.missile_render.draw(surface, missile, offset_x, offset_y)

        # Twin-Engine Fighter Jet
        self.aircraft_render.draw(surface, aircraft, offset_x, offset_y, alive=aircraft_alive)

        # 8. Draw neon borders around the viewport
        border_rect = pygame.Rect(offset_x, offset_y, 800, 600)
        pygame.draw.rect(surface, self.c_border_panel, border_rect, width=1)

    def draw_mission_overlay(self, surface, outcome, offset_x=250, offset_y=0):
        """
        Draws a glowing GCS tactical mission overlay at the center of simulator viewport.
        """
        center_x = offset_x + 400
        center_y = offset_y + 300
        
        w, h = 340, 110
        rx = center_x - w // 2
        ry = center_y - h // 2
        
        # 1. Glassmorphic card surface
        overlay_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        bg_color = (15, 23, 42, 220)  # Dark slate with opacity
        pygame.draw.rect(overlay_surf, bg_color, (0, 0, w, h), border_radius=12)
        
        border_color = self.c_green if outcome == "SUCCESS" else self.c_red
        pygame.draw.rect(overlay_surf, border_color, (0, 0, w, h), width=2, border_radius=12)
        
        # Neon brackets
        b_len = 8
        pygame.draw.line(overlay_surf, border_color, (0, 0), (b_len, 0), 3)
        pygame.draw.line(overlay_surf, border_color, (0, 0), (0, b_len), 3)
        pygame.draw.line(overlay_surf, border_color, (w - 1, 0), (w - 1 - b_len, 0), 3)
        pygame.draw.line(overlay_surf, border_color, (w - 1, 0), (w - 1, b_len), 3)
        pygame.draw.line(overlay_surf, border_color, (0, h - 1), (b_len, h - 1), 3)
        pygame.draw.line(overlay_surf, border_color, (0, h - 1), (0, h - 1 - b_len), 3)
        pygame.draw.line(overlay_surf, border_color, (w - 1, h - 1), (w - 1 - b_len, h - 1), 3)
        pygame.draw.line(overlay_surf, border_color, (w - 1, h - 1), (w - 1, h - 1 - b_len), 3)
        
        surface.blit(overlay_surf, (rx, ry))
        
        # 2. Main title text
        font_main = pygame.font.SysFont("Arial", 16, bold=True)
        title_text = "TACTICAL MISSION COMPLETE" if outcome == "SUCCESS" else "TACTICAL MISSION FAILED"
        title_surf = font_main.render(title_text, True, border_color)
        surface.blit(title_surf, (center_x - title_surf.get_width() // 2, ry + 25))
        
        # 3. Subtext description
        font_sub = pygame.font.SysFont("Arial", 11, bold=True)
        sub_text = "AUTO-RESPAWNING IN COCKPIT..." if outcome == "FAILED" else "TARGET OBJECTIVE DURATION SURVIVED"
        sub_surf = font_sub.render(sub_text, True, (255, 255, 255))
        surface.blit(sub_surf, (center_x - sub_surf.get_width() // 2, ry + 60))

    def draw(self, surface, aircraft, missile, waypoint, active_behavior, current_reward, reward_breakdown, summary_data, average_reward, success_rate, autopilot_mode, fps, aircraft_alive=True, ppo_probabilities=None, episode_outcome=None):
        """
        Redraws the entire 1350x650 demo dashboard.
        """
        surface.fill((8, 12, 24))

        # 1. Left interactive column panel
        self.draw_left_panel(surface, autopilot_mode)

        # 2. Center Flight Simulator viewport (800x600)
        self.draw_simulation_window(surface, aircraft, missile, waypoint, aircraft_alive, offset_x=250, offset_y=0)

        # 3. Draw Mission Success/Failure overlay if episode finished
        if episode_outcome is not None:
            self.draw_mission_overlay(surface, episode_outcome, offset_x=250, offset_y=0)

        # 4. Bottom primary instrument panel (800x50)
        self.draw_bottom_bar(surface, (250, 600, 800, 50), aircraft, missile, fps)

        # 5. Right glassmorphism HUD telemetry columns (300px wide, starting x: 1050)
        self.hud.draw_all(
            surface=surface,
            aircraft=aircraft,
            missile=missile,
            active_behavior=active_behavior,
            current_reward=current_reward,
            reward_breakdown=reward_breakdown,
            summary_data=summary_data,
            average_reward=average_reward,
            success_rate=success_rate,
            autopilot_mode=autopilot_mode,
            ppo_probabilities=ppo_probabilities
        )
