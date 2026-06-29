import pygame

class EpisodePanel:
    """
    Renders the episode telemetry statistics and the active PPO 
    reinforcement learning action weights using glassmorphism.
    """
    def __init__(self):
        if not pygame.font.get_init():
            pygame.font.init()
        self.font_title = pygame.font.SysFont("Arial", 11, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 10, bold=False)
        self.font_value = pygame.font.SysFont("Arial", 10, bold=True)
        self.font_action = pygame.font.SysFont("Arial", 9, bold=False)

        self.c_bg_panel = (15, 23, 42, 200)      # Translucent Slate 900
        self.c_border_panel = (71, 85, 105, 150)  # Slate 500
        self.c_active = (34, 211, 238)            # Cyan 400
        self.c_green = (34, 197, 94)              # Green 500
        self.c_blue = (14, 165, 233)              # Sky 500
        self.c_gray = (148, 163, 184)              # Slate 400
        self.c_title = (34, 211, 238)             # Cyan 400

        self.action_labels = ["L-Turn", "R-Turn", "Accel", "Decel", "Climb", "Dive", "Steady"]

    def draw_episode_summary(self, surface, rect, summary_data, average_reward, success_rate):
        """
        Draws the episode summary statistics panel with glassmorphism.
        """
        x, y, w, h = rect
        
        # Create and blit glassmorphic panel
        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, self.c_bg_panel, (0, 0, w, h), border_radius=8)
        pygame.draw.rect(panel_surf, self.c_border_panel, (0, 0, w, h), width=1, border_radius=8)
        
        # Neon brackets
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
        title_surf = self.font_title.render("MISSION METRICS LOG", True, self.c_title)
        surface.blit(title_surf, (x + 12, y + 8))

        steps = summary_data.get("steps_count", 0)
        done_flag = summary_data.get("done", False)

        items = [
            ("Episode Count", f"{summary_data.get('current_episode', 1)}"),
            ("Simulation Step", f"{steps} / 1000"),
            ("Accumulated Reward", f"{summary_data.get('episode_reward', 0.0):+.2f}", self.c_green if summary_data.get('episode_reward', 0.0) >= 0 else (239, 68, 68)),
            ("Rolling Avg Reward", f"{average_reward:+.2f}", self.c_green if average_reward >= 0 else (239, 68, 68)),
            ("Mission Success Rate", f"{success_rate * 100.0:.1f}%", self.c_green),
            ("Episode Terminated", "TRUE" if done_flag else "FALSE", (239, 68, 68) if done_flag else self.c_gray)
        ]

        start_y = y + 24
        for idx, (label, val, *opt_color) in enumerate(items):
            color = opt_color[0] if opt_color else (255, 255, 255)
            y_pos = start_y + idx * 11

            # Label text
            lbl_surf = self.font_label.render(label, True, (255, 255, 255))
            surface.blit(lbl_surf, (x + 12, y_pos))

            # Value text
            val_surf = self.font_value.render(val, True, color)
            val_x = x + w - 12 - val_surf.get_width()
            surface.blit(val_surf, (val_x, y_pos))

    def draw_rl_visualization(self, surface, rect, active_behavior, ppo_probabilities=None):
        """
        Draws PPO predicted action and probability bars inside glassmorphism card.
        """
        x, y, w, h = rect
        
        # Create and blit glassmorphic panel
        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, self.c_bg_panel, (0, 0, w, h), border_radius=8)
        pygame.draw.rect(panel_surf, self.c_border_panel, (0, 0, w, h), width=1, border_radius=8)
        
        # Neon brackets
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
        title_surf = self.font_title.render("NEURAL NETWORK INFERENCE", True, self.c_title)
        surface.blit(title_surf, (x + 12, y + 8))

        # Selected Action
        lbl_surf = self.font_label.render("Selected Action:", True, (255, 255, 255))
        surface.blit(lbl_surf, (x + 12, y + 23))

        clean_act = active_behavior.replace("PPO: ", "")
        val_surf = self.font_value.render(clean_act, True, self.c_green if "DEAD" not in clean_act else (239, 68, 68))
        surface.blit(val_surf, (x + 105, y + 23))

        # PPO Probabilities Check
        if ppo_probabilities is None or len(ppo_probabilities) != 7:
            ppo_probabilities = [0.14, 0.14, 0.14, 0.14, 0.14, 0.14, 0.14]

        # Draw probability chart bars
        chart_start_y = y + 41
        bar_max_w = 110
        bar_h = 6

        for idx, prob in enumerate(ppo_probabilities):
            y_pos = chart_start_y + idx * 8
            
            # Label
            lbl = self.action_labels[idx]
            act_lbl_surf = self.font_action.render(f"{lbl:<8}", True, self.c_gray)
            surface.blit(act_lbl_surf, (x + 12, y_pos - 2))

            # Bar Slot Slot Background
            bar_x = x + 72
            pygame.draw.rect(surface, (30, 41, 59), (bar_x, y_pos, bar_max_w, bar_h), border_radius=2)

            # Filled neon indicator
            fill_w = int(bar_max_w * prob)
            if fill_w > 0:
                bar_color = self.c_green if idx in [0, 1] else (self.c_blue if idx in [2, 3] else (251, 146, 60)) # steering vs acceleration vs altitude
                pygame.draw.rect(surface, bar_color, (bar_x, y_pos, fill_w, bar_h), border_radius=2)

            # Numerical percentages
            pct_surf = self.font_action.render(f"{prob * 100.0:.0f}%", True, (255, 255, 255))
            surface.blit(pct_surf, (x + 190, y_pos - 2))
