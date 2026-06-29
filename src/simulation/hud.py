import pygame
import math

class HUD:
    """
    HUD (Heads-Up Display) visualizer class.
    Renders flight status parameters, reinforcement learning reward metrics, 
    and diagnostic information in a structured, multi-panel dashboard.
    
    Aesthetics:
    - Dark navy background with contrasting off-white and blue accents.
    - Rounded rectangular cards grouping related parameters.
    - Live reward history graph showing progress over the last 50 steps.
    """
    def __init__(self):
        # Initialize Pygame's font module if it hasn't been initialized yet
        if not pygame.font.get_init():
            pygame.font.init()
            
        # Set up fonts for rendering text
        self.font_title = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 12, bold=False)
        self.font_value = pygame.font.SysFont("Arial", 12, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_bottom = pygame.font.SysFont("Arial", 13, bold=False)
        self.font_bottom_val = pygame.font.SysFont("Arial", 13, bold=True)

        # Color system
        self.c_bg_sidebar = (30, 41, 59)      # Slate 800 (slightly lighter dark navy for sidebar background)
        self.c_bg_card = (15, 23, 42)         # Slate 900 (dark navy background for panel cards)
        self.c_border_card = (71, 85, 105)     # Slate 500 (gray border for panel cards)
        self.c_title = (96, 165, 250)         # Sky Blue (section header title)
        self.c_label = (255, 255, 255)        # Pure White (standard labels)
        self.c_val_neutral = (203, 213, 225)  # Slate 300 (off-white for normal text values)
        
        # Color codes based on values
        self.c_green = (74, 222, 128)         # Emerald 400 (green for positive rewards/success)
        self.c_red = (248, 113, 113)          # Red 400 (red for negative rewards/warnings)
        self.c_gray = (156, 163, 175)         # Gray 400 (neutral/inactive gray)
        self.c_orange = (251, 146, 60)        # Orange 400 (alert color)

        # Scrolling line graph tracking
        self.reward_history = []
        self.max_history = 50

    def add_reward_to_history(self, reward: float):
        """
        Appends the latest step reward to history, keeping size capped at 50 values.
        """
        self.reward_history.append(reward)
        if len(self.reward_history) > self.max_history:
            self.reward_history.pop(0)

    def draw_panel(self, surface, rect, title):
        """
        Helper method to draw a rounded rectangular panel card with a border 
        and section header title.
        """
        # Draw solid panel card background
        pygame.draw.rect(surface, self.c_bg_card, rect, border_radius=12)
        # Draw thin gray border
        pygame.draw.rect(surface, self.c_border_card, rect, width=1, border_radius=12)
        
        # Render and draw the section title text at the top of the card
        title_surf = self.font_title.render(title.upper(), True, self.c_title)
        surface.blit(title_surf, (rect[0] + 12, rect[1] + 10))

    def draw_flight_status(self, surface, rect, active_behavior, aircraft_alive, missile_status, autopilot_on):
        """
        Renders the current flight state, behavior model, and status values inside the panel.
        """
        self.draw_panel(surface, rect, "Flight Status")
        
        # Set up parameters to draw
        # Format: (label, value, value_color)
        status_items = [
            ("Active Behavior", active_behavior, self.c_orange if "Evade" in active_behavior else self.c_val_neutral),
            ("Aircraft Alive", "ALIVE" if aircraft_alive else "DEAD", self.c_green if aircraft_alive else self.c_red),
            ("Missile Status", missile_status, self.c_red if "ACTIVE" in missile_status or "EXPLODING" in missile_status else self.c_gray),
            ("Autopilot Status", "ON" if autopilot_on else "OFF", self.c_green if autopilot_on else self.c_gray)
        ]
        
        start_y = rect[1] + 32
        for idx, (label, val, color) in enumerate(status_items):
            y_pos = start_y + idx * 18
            
            # Draw label
            lbl_surf = self.font_label.render(label, True, self.c_label)
            surface.blit(lbl_surf, (rect[0] + 15, y_pos))
            
            # Draw value (right-aligned)
            val_surf = self.font_value.render(val, True, color)
            val_x = rect[0] + rect[2] - 15 - val_surf.get_width()
            surface.blit(val_surf, (val_x, y_pos))

    def draw_reward(self, surface, rect, current_reward):
        """
        Displays the current step reward in large numbers and draws the reward history graph.
        """
        self.draw_panel(surface, rect, "Current Reward")
        
        # Determine reward sign and value text color
        if current_reward > 0.001:
            color = self.c_green
            sign = "+"
        elif current_reward < -0.001:
            color = self.c_red
            sign = ""
        else:
            color = self.c_gray
            sign = ""
            
        reward_text = f"{sign}{current_reward:.2f}"
        
        # Render reward value
        val_surf = self.font_large.render(reward_text, True, color)
        surface.blit(val_surf, (rect[0] + 12, rect[1] + 28))
        
        # Graph Bounding Box inside the panel
        graph_x = rect[0] + 12
        graph_y = rect[1] + 70
        graph_w = rect[2] - 24
        graph_h = rect[3] - 82
        
        # Draw background container for the graph
        pygame.draw.rect(surface, (15, 23, 42), (graph_x, graph_y, graph_w, graph_h), border_radius=8)
        pygame.draw.rect(surface, (51, 65, 85), (graph_x, graph_y, graph_w, graph_h), width=1, border_radius=8)
        
        # Plot reward history line
        if len(self.reward_history) > 1:
            # Scale y-axis based on current history values
            min_r = min(self.reward_history)
            max_r = max(self.reward_history)
            
            # Ensure we don't divide by zero and have a minimum bounding height/scale
            if abs(max_r - min_r) < 1.0:
                min_r -= 1.0
                max_r += 1.0
                
            y_range = max_r - min_r
            
            # Draw zero-reference line
            zero_y = graph_y + graph_h - int(((0.0 - min_r) / y_range) * graph_h)
            if graph_y <= zero_y <= graph_y + graph_h:
                pygame.draw.line(surface, (51, 65, 85), (graph_x + 2, zero_y), (graph_x + graph_w - 2, zero_y), 1)
                
            # Compute point coordinates
            points = []
            dx = graph_w / (self.max_history - 1)
            
            for idx, val in enumerate(self.reward_history):
                pt_x = graph_x + idx * dx
                # In Pygame, Y coordinates increase downwards
                normalized_val = (val - min_r) / y_range
                pt_y = graph_y + graph_h - (normalized_val * graph_h)
                
                # Constrain coordinates to fit inside graph area
                pt_y = max(graph_y + 2, min(graph_y + graph_h - 2, pt_y))
                points.append((pt_x, pt_y))
                
            # Draw lines connecting the plot points
            pygame.draw.lines(surface, self.c_green, False, points, 2)
            
        else:
            # Draw placeholder message if history is empty
            placeholder = self.font_label.render("Awaiting telemetry...", True, self.c_gray)
            surface.blit(placeholder, (graph_x + (graph_w - placeholder.get_width()) // 2, graph_y + (graph_h - placeholder.get_height()) // 2))

    def draw_reward_breakdown(self, surface, rect, breakdown_data):
        """
        Renders the itemized list of all reward and penalty components.
        Colors positive values green, negative values red, and zero values gray.
        """
        self.draw_panel(surface, rect, "Reward Breakdown")
        
        # Component mappings for cleaner names
        component_labels = {
            "survival": "Survival Reward",
            "stability": "Flight Stability",
            "waypoint": "Waypoint Navigation",
            "missile_avoidance": "Missile Avoidance",
            "boundary": "Boundary Penalty",
            "collision": "Collision Penalty",
            "missile_hit": "Missile Hit Penalty"
        }
        
        start_y = rect[1] + 30
        idx = 0
        total_val = 0.0
        
        for key, label in component_labels.items():
            val = breakdown_data.get(key, 0.0)
            total_val += val
            y_pos = start_y + idx * 16
            
            # Select color based on sign of component
            if val > 0.001:
                color = self.c_green
                sign = "+"
            elif val < -0.001:
                color = self.c_red
                sign = ""
            else:
                color = self.c_gray
                sign = ""
                
            lbl_surf = self.font_label.render(label, True, self.c_label)
            surface.blit(lbl_surf, (rect[0] + 15, y_pos))
            
            val_surf = self.font_value.render(f"{sign}{val:.2f}", True, color)
            val_x = rect[0] + rect[2] - 15 - val_surf.get_width()
            surface.blit(val_surf, (val_x, y_pos))
            
            idx += 1
            
        # Draw table divider line
        divider_y = start_y + idx * 16 + 5
        pygame.draw.line(surface, self.c_border_card, (rect[0] + 12, divider_y), (rect[0] + rect[2] - 12, divider_y), 1)
        
        # Draw Total Row
        total_y = divider_y + 6
        total_lbl_surf = self.font_title.render("TOTAL", True, self.c_title)
        surface.blit(total_lbl_surf, (rect[0] + 15, total_y))
        
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
        total_val_x = rect[0] + rect[2] - 15 - total_val_surf.get_width()
        surface.blit(total_val_surf, (total_val_x, total_y))

    def draw_episode_summary(self, surface, rect, summary_data):
        """
        Displays summary counters for steps, episode accumulator metrics, and outcomes.
        """
        self.draw_panel(surface, rect, "Episode Summary")
        
        summary_items = [
            ("Current Episode", f"{summary_data.get('current_episode', 1)}"),
            ("Current Step", f"{summary_data.get('steps_count', 0)} / 1000"),
            ("Episode Reward", f"{summary_data.get('episode_reward', 0.0):+.2f}", self.c_green if summary_data.get('episode_reward', 0.0) >= 0 else self.c_red),
            ("Waypoints Reached", f"{summary_data.get('waypoints_reached', 0)}", self.c_green),
            ("Done (Terminated)", "True" if summary_data.get('done', False) else "False", self.c_red if summary_data.get('done', False) else self.c_gray)
        ]
        
        start_y = rect[1] + 30
        for idx, item in enumerate(summary_items):
            label, val = item[0], item[1]
            color = item[2] if len(item) > 2 else self.c_val_neutral
            y_pos = start_y + idx * 15
            
            lbl_surf = self.font_label.render(label, True, self.c_label)
            surface.blit(lbl_surf, (rect[0] + 15, y_pos))
            
            val_surf = self.font_value.render(val, True, color)
            val_x = rect[0] + rect[2] - 15 - val_surf.get_width()
            surface.blit(val_surf, (val_x, y_pos))

    def draw_bottom_status_bar(self, surface, rect, speed, heading_deg, pos_x, pos_y, dist_waypoint, dist_missile, fps):
        """
        Draws the horizontal bottom panel containing real-time aircraft telemetry.
        """
        # Draw background panel
        pygame.draw.rect(surface, (15, 23, 42), rect)
        # Top dividing line to separate bar from simulation space
        pygame.draw.line(surface, self.c_border_card, (rect[0], rect[1]), (rect[0] + rect[2], rect[1]), 2)
        
        missile_dist_str = "N/A" if dist_missile > 9000.0 else f"{dist_missile:.1f} px"
        missile_color = self.c_red if dist_missile < 200.0 and dist_missile > 0.0 else self.c_val_neutral
        
        # Telemetry values to draw
        items = [
            ("SPEED:", f"{speed:.2f} px/f"),
            ("HEADING:", f"{heading_deg:.1f}°"),
            ("POSITION:", f"({pos_x:.1f}, {pos_y:.1f})"),
            ("DIST TO WAYPOINT:", f"{dist_waypoint:.1f} px"),
            ("DIST TO MISSILE:", missile_dist_str, missile_color),
            ("FPS:", f"{fps:.1f}")
        ]
        
        # Evenly space columns across the status bar
        num_items = len(items)
        col_width = rect[2] / num_items
        
        y_pos = rect[1] + (rect[3] - 14) // 2
        
        for idx, item in enumerate(items):
            label, val = item[0], item[1]
            val_color = item[2] if len(item) > 2 else self.c_val_neutral
            
            # Compute centering offsets
            col_x = rect[0] + idx * col_width + 10
            
            # Render label (white)
            lbl_surf = self.font_bottom.render(label, True, self.c_gray)
            surface.blit(lbl_surf, (col_x, y_pos))
            
            # Render value (off-white or specialized color)
            val_surf = self.font_bottom_val.render(val, True, val_color)
            surface.blit(val_surf, (col_x + lbl_surf.get_width() + 4, y_pos))

    def draw_all(self, surface, aircraft, missile, active_behavior, current_reward, reward_breakdown, summary_data, fps):
        """
        Draws the complete HUD layout by updating values and triggering separate panel renders.
        """
        # Append the latest reward to the rolling chart history
        self.add_reward_to_history(current_reward)
        
        # Draw sidebar solid background panel
        sidebar_rect = (800, 0, 300, 650)
        pygame.draw.rect(surface, self.c_bg_sidebar, sidebar_rect)
        # Left boundary divider between simulation and HUD
        pygame.draw.line(surface, self.c_border_card, (800, 0), (800, 650), 2)
        
        # Draw vertical panels in sidebar
        self.draw_flight_status(
            surface, 
            (815, 15, 270, 110), 
            active_behavior, 
            aircraft.speed > 0,  # Is alive if speed > 0
            "ACTIVE" if missile.active else ("EXPLODING" if missile.exploding else "INACTIVE"), 
            autopilot_on=True
        )
        
        self.draw_reward(
            surface, 
            (815, 135, 270, 160), 
            current_reward
        )
        
        self.draw_reward_breakdown(
            surface, 
            (815, 305, 270, 205), 
            reward_breakdown
        )
        
        self.draw_episode_summary(
            surface, 
            (815, 520, 270, 115), 
            summary_data
        )
        
        # Draw bottom status bar
        angle_deg = math.degrees(aircraft.angle)
        # Handle wraparound values to keep heading between -180 and 180 degrees
        angle_deg = (angle_deg + 180) % 360 - 180
        
        self.draw_bottom_status_bar(
            surface=surface,
            rect=(0, 600, 800, 50),
            speed=aircraft.speed,
            heading_deg=angle_deg,
            pos_x=aircraft.x,
            pos_y=aircraft.y,
            dist_waypoint=aircraft.distance_to_waypoint,
            dist_missile=aircraft.distance_to_missile,
            fps=fps
        )
