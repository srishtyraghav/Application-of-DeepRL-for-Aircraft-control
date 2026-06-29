import pygame

class BehaviorTreePanel:
    """
    Renders the Behavior Tree panel with glassmorphism nodes, 
    connecting lines, neon borders, and sci-fi node modules.
    """
    def __init__(self):
        if not pygame.font.get_init():
            pygame.font.init()
        self.font_title = pygame.font.SysFont("Arial", 11, bold=True)
        self.font_node = pygame.font.SysFont("Arial", 10, bold=True)

        self.c_bg_panel = (15, 23, 42, 200)      # Translucent Slate 900
        self.c_border_panel = (71, 85, 105, 150)  # Slate 500
        self.c_active = (34, 211, 238)            # Cyan 400
        self.c_active_bg = (8, 51, 68, 220)       # Dark Cyan 900
        self.c_inactive = (71, 85, 105)           # Slate 600
        self.c_inactive_bg = (30, 41, 59, 180)    # Slate 800
        self.c_text_inactive = (148, 163, 184)    # Slate 400
        self.c_title = (34, 211, 238)             # Cyan 400

    def draw(self, surface, rect, active_behavior, missile_active):
        """
        Draws the Behavior Tree panel inside the specified rect with glassmorphism.
        """
        x, y, w, h = rect
        
        # 1. Create and blit glassmorphism background surface
        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, self.c_bg_panel, (0, 0, w, h), border_radius=8)
        pygame.draw.rect(panel_surf, self.c_border_panel, (0, 0, w, h), width=1, border_radius=8)
        
        # Add sci-fi neon corner brackets to panel
        b_len = 5
        # Top-Left
        pygame.draw.line(panel_surf, self.c_active, (0, 0), (b_len, 0), 2)
        pygame.draw.line(panel_surf, self.c_active, (0, 0), (0, b_len), 2)
        # Top-Right
        pygame.draw.line(panel_surf, self.c_active, (w - 1, 0), (w - 1 - b_len, 0), 2)
        pygame.draw.line(panel_surf, self.c_active, (w - 1, 0), (w - 1, b_len), 2)
        # Bottom-Left
        pygame.draw.line(panel_surf, self.c_active, (0, h - 1), (b_len, h - 1), 2)
        pygame.draw.line(panel_surf, self.c_active, (0, h - 1), (0, h - 1 - b_len), 2)
        # Bottom-Right
        pygame.draw.line(panel_surf, self.c_active, (w - 1, h - 1), (w - 1 - b_len, h - 1), 2)
        pygame.draw.line(panel_surf, self.c_active, (w - 1, h - 1), (w - 1, h - 1 - b_len), 2)

        surface.blit(panel_surf, (x, y))

        # Title
        title_surf = self.font_title.render("BEHAVIOR TREE TELEMETRY", True, self.c_title)
        surface.blit(title_surf, (x + 12, y + 8))

        # Coordinates for nodes
        center_x = x + w // 2
        
        # Node locations
        root_y = y + 26
        root_w, root_h = 42, 14
        root_rect = (center_x - root_w // 2, root_y, root_w, root_h)

        threat_y = y + 49
        threat_w, threat_h = 55, 14
        threat_rect = (center_x - threat_w // 2, threat_y, threat_w, threat_h)

        leaf_y = y + 74
        evade_w, evade_h = 92, 15
        evade_rect = (center_x - evade_w - 6, leaf_y, evade_w, evade_h)

        navigate_w, navigate_h = 100, 15
        navigate_rect = (center_x + 6, leaf_y, navigate_w, navigate_h)

        # Active state calculations
        is_root_active = True
        is_threat_active = missile_active
        is_evade_active = active_behavior == "EvadeMissile"
        is_navigate_active = active_behavior == "NavigateToWaypoint"

        # 2. Draw active flow connector lines
        # Root -> Threat?
        c_root_thr = self.c_active if (is_root_active and is_threat_active) else self.c_inactive
        pygame.draw.line(surface, c_root_thr, (center_x, root_y + root_h), (center_x, threat_y), 2)
        
        # Threat? -> Evade (Left)
        c_thr_evd = self.c_active if (is_threat_active and is_evade_active) else self.c_inactive
        pygame.draw.line(surface, c_thr_evd, (center_x, threat_y + threat_h), (evade_rect[0] + evade_w // 2, leaf_y), 2)
        
        # Threat? -> Navigate (Right)
        c_thr_nav = self.c_active if (is_navigate_active) else self.c_inactive
        pygame.draw.line(surface, c_thr_nav, (center_x, threat_y + threat_h), (navigate_rect[0] + navigate_w // 2, leaf_y), 2)

        # 3. Draw modular glass nodes
        self.draw_node(surface, root_rect, "Root (Sel)", is_root_active)
        self.draw_node(surface, threat_rect, "Threat?", is_threat_active)
        self.draw_node(surface, evade_rect, "Evade Missile", is_evade_active)
        self.draw_node(surface, navigate_rect, "Navigate Waypoint", is_navigate_active)

    def draw_node(self, surface, rect, text, active):
        rx, ry, rw, rh = rect
        bg = self.c_active_bg if active else self.c_inactive_bg
        border = self.c_active if active else self.c_inactive
        txt_color = (255, 255, 255) if active else self.c_text_inactive

        # Draw translucent node box
        node_surf = pygame.Surface((rw, rh), pygame.SRCALPHA)
        pygame.draw.rect(node_surf, bg, (0, 0, rw, rh), border_radius=4)
        pygame.draw.rect(node_surf, border, (0, 0, rw, rh), width=1, border_radius=4)
        surface.blit(node_surf, (rx, ry))

        # Node Label
        text_surf = self.font_node.render(text, True, txt_color)
        tx = rx + (rw - text_surf.get_width()) // 2
        ty = ry + (rh - text_surf.get_height()) // 2
        surface.blit(text_surf, (tx, ty))
