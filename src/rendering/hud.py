import pygame
from src.rendering.behavior_tree_panel import BehaviorTreePanel
from src.rendering.reward_panel import RewardPanel
from src.rendering.episode_panel import EpisodePanel

class HUD:
    """
    HUD sidebar columns coordinator.
    Manages drawing the glassmorphic panels on the right side of the screen.
    """
    def __init__(self):
        # Sub-panels
        self.bt_panel = BehaviorTreePanel()
        self.reward_panel = RewardPanel()
        self.episode_panel = EpisodePanel()
        
        # Sidebar Fonts
        if not pygame.font.get_init():
            pygame.font.init()
        self.font_title = pygame.font.SysFont("Arial", 11, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 10, bold=False)
        self.font_value = pygame.font.SysFont("Arial", 10, bold=True)

        self.c_bg_sidebar = (9, 15, 29)           # Very Dark cyber navy base background
        self.c_bg_panel = (15, 23, 42, 200)       # Translucent Slate 900
        self.c_border_panel = (71, 85, 105, 150)   # Slate 500
        self.c_active = (34, 211, 238)             # Cyan 400
        self.c_green = (34, 197, 94)               # Green 500
        self.c_red = (239, 68, 68)                 # Red 500
        self.c_gray = (148, 163, 184)              # Slate 400
        self.c_title = (34, 211, 238)              # Cyan 400

    def draw_flight_status(self, surface, rect, active_behavior, aircraft_alive, autopilot_mode, missile_active):
        """
        Draws the basic flight system status panel with glassmorphism.
        """
        x, y, w, h = rect
        
        # Create and blit glassmorphic panel
        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, self.c_bg_panel, (0, 0, w, h), border_radius=8)
        pygame.draw.rect(panel_surf, self.c_border_panel, (0, 0, w, h), width=1, border_radius=8)
        
        # Corner neon brackets
        b_len = 4
        pygame.draw.line(panel_surf, self.c_active, (0, 0), (b_len, 0), 2)
        pygame.draw.line(panel_surf, self.c_active, (0, 0), (0, b_len), 2)
        pygame.draw.line(panel_surf, self.c_active, (w - 1, 0), (w - 1 - b_len, 0), 2)
        pygame.draw.line(panel_surf, self.c_active, (w - 1, 0), (w - 1, b_len), 2)
        pygame.draw.line(panel_surf, self.c_active, (0, h - 1), (b_len, h - 1), 2)
        pygame.draw.line(panel_surf, self.c_active, (0, h - 1), (0, h - 1 - b_len), 2)
        pygame.draw.line(panel_surf, self.c_active, (w - 1, h - 1), (w - 1 - b_len, h - 1), 2)
        pygame.draw.line(panel_surf, self.c_active, (w - 1, h - 1), (w - 1, h - 1 - b_len), 2)
        
        surface.blit(panel_surf, (x, y))

        # Title
        title_surf = self.font_title.render("FLIGHT SYSTEM STATUS", True, self.c_title)
        surface.blit(title_surf, (x + 12, y + 8))

        status_items = [
            ("Autopilot System Mode", "ON (ACTIVE)" if autopilot_mode else "OFF (MANUAL OVERRIDE)", self.c_green if autopilot_mode else self.c_red),
            ("Aircraft Telemetry", "CONNECTED" if aircraft_alive else "SIGNAL LOST / DEAD", self.c_green if aircraft_alive else self.c_red),
            ("Radar Threat Alert", "WARNING: MISSILE ENGAGED" if missile_active else "CLEAR (NO THREAT)", self.c_red if missile_active else self.c_gray)
        ]

        start_y = y + 24
        for idx, (label, val, color) in enumerate(status_items):
            y_pos = start_y + idx * 11
            
            lbl_surf = self.font_label.render(label, True, (255, 255, 255))
            surface.blit(lbl_surf, (x + 12, y_pos))

            val_surf = self.font_value.render(val, True, color)
            val_x = x + w - 12 - val_surf.get_width()
            surface.blit(val_surf, (val_x, y_pos))

    def draw_all(self, surface, aircraft, missile, active_behavior, current_reward, reward_breakdown, summary_data, average_reward, success_rate, autopilot_mode, ppo_probabilities=None):
        """
        Draws all HUD components of the right-side dashboard panel.
        """
        # Draw base sidebar solid panel background
        sidebar_rect = (1050, 0, 300, 650)
        pygame.draw.rect(surface, self.c_bg_sidebar, sidebar_rect)
        pygame.draw.line(surface, self.c_border_panel, (1050, 0), (1050, 650), 2)

        # Card 1: Flight Status Panel (Height: 75)
        self.draw_flight_status(
            surface=surface,
            rect=(1065, 15, 270, 75),
            active_behavior=active_behavior,
            aircraft_alive=aircraft.speed > 0,
            autopilot_mode=autopilot_mode,
            missile_active=missile.active
        )

        # Card 2: Behavior Tree Node Flow (Height: 110)
        clean_bt_behavior = active_behavior.replace("PPO: ", "")
        if "DEAD" in clean_bt_behavior or "MANUAL" in clean_bt_behavior:
            clean_bt_behavior = "NONE"
        self.bt_panel.draw(
            surface=surface,
            rect=(1065, 95, 270, 110),
            active_behavior=clean_bt_behavior,
            missile_active=missile.active
        )

        # Card 3: Neural Network Action Inference probabilities (Height: 110)
        self.episode_panel.draw_rl_visualization(
            surface=surface,
            rect=(1065, 215, 270, 110),
            active_behavior=active_behavior,
            ppo_probabilities=ppo_probabilities
        )

        # Card 4: Step Reward large badge display (Height: 55)
        self.reward_panel.draw_badge(
            surface=surface,
            rect=(1065, 335, 270, 55),
            current_reward=current_reward
        )

        # Card 5: Tabular Reward Component Breakdown weights (Height: 135)
        self.reward_panel.draw_breakdown(
            surface=surface,
            rect=(1065, 400, 270, 135),
            reward_breakdown=reward_breakdown
        )

        # Card 6: Mission Metric Logs (Height: 95)
        self.episode_panel.draw_episode_summary(
            surface=surface,
            rect=(1065, 545, 270, 95),
            summary_data=summary_data,
            average_reward=average_reward,
            success_rate=success_rate
        )
