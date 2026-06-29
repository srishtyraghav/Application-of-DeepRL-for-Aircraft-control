import pygame

class RewardPanel:
    """
    Renders the current step reward and reward components breakdown 
    as transparent cyber panels with neon cyan brackets.
    """
    def __init__(self):
        if not pygame.font.get_init():
            pygame.font.init()
        self.font_title = pygame.font.SysFont("Arial", 11, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 10, bold=False)
        self.font_value = pygame.font.SysFont("Arial", 10, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 22, bold=True)

        self.c_bg_panel = (15, 23, 42, 200)      # Translucent Slate 900
        self.c_border_panel = (71, 85, 105, 150)  # Slate 500
        self.c_active = (34, 211, 238)            # Cyan 400
        self.c_green = (34, 197, 94)              # Green 500
        self.c_red = (239, 68, 68)                # Red 500
        self.c_gray = (148, 163, 184)              # Slate 400
        self.c_title = (34, 211, 238)             # Cyan 400

    def draw_badge(self, surface, rect, current_reward):
        """
        Draws the large current reward card with glassmorphism.
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
        lbl_surf = self.font_title.render("CURRENT STEP REWARD", True, self.c_title)
        surface.blit(lbl_surf, (x + 12, y + 8))

        # Format number value
        if current_reward > 0.001:
            color = self.c_green
            sign = "+"
        elif current_reward < -0.001:
            color = self.c_red
            sign = ""
        else:
            color = self.c_gray
            sign = ""

        reward_str = f"{sign}{current_reward:.2f}"
        val_surf = self.font_large.render(reward_str, True, color)
        
        # Center value text
        val_x = x + (w - val_surf.get_width()) // 2
        val_y = y + 20
        surface.blit(val_surf, (val_x, val_y))

    def draw_breakdown(self, surface, rect, reward_breakdown):
        """
        Draws the reward breakdown table with glassmorphism.
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
        title_surf = self.font_title.render("REWARD BREAKDOWN", True, self.c_title)
        surface.blit(title_surf, (x + 12, y + 8))

        component_labels = {
            "survival": "Survival Reward",
            "stability": "Stable Flight",
            "waypoint": "Closer to Waypoint",
            "missile_avoidance": "Missile Dist Avoid",
            "boundary": "Boundary Penalty",
            "collision": "Collision Penalty",
            "missile_hit": "Missile Hit Penalty"
        }

        start_y = y + 26
        total_val = 0.0

        for idx, (key, label) in enumerate(component_labels.items()):
            val = reward_breakdown.get(key, 0.0)
            total_val += val
            y_pos = start_y + idx * 12

            # Value format sign
            if val > 0.001:
                color = self.c_green
                sign = "+"
            elif val < -0.001:
                color = self.c_red
                sign = ""
            else:
                color = self.c_gray
                sign = ""

            # Label text
            lbl_surf = self.font_label.render(label, True, (255, 255, 255))
            surface.blit(lbl_surf, (x + 12, y_pos))

            # Value text
            val_surf = self.font_value.render(f"{sign}{val:.2f}", True, color)
            val_x = x + w - 12 - val_surf.get_width()
            surface.blit(val_surf, (val_x, y_pos))

        # Table Divider line
        divider_y = start_y + len(component_labels) * 12 + 2
        pygame.draw.line(surface, self.c_border_panel, (x + 8, divider_y), (x + w - 8, divider_y), 1)

        # Total Row
        total_y = divider_y + 3
        tot_lbl_surf = self.font_title.render("TOTAL STEP REWARD", True, self.c_title)
        surface.blit(tot_lbl_surf, (x + 12, total_y))

        if total_val > 0.001:
            tot_color = self.c_green
            tot_sign = "+"
        elif total_val < -0.001:
            tot_color = self.c_red
            tot_sign = ""
        else:
            tot_color = self.c_gray
            tot_sign = ""

        total_val_surf = self.font_value.render(f"{tot_sign}{total_val:.2f}", True, tot_color)
        total_val_x = x + w - 12 - total_val_surf.get_width()
        surface.blit(total_val_surf, (total_val_x, total_y))
