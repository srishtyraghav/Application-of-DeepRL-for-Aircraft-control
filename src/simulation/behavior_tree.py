import math
import config

class Node:
    """
    Base class representing a node in the Behavior Tree.
    Every custom node must inherit from this and override the tick method.
    """
    def tick(self, aircraft, missile, waypoint):
        raise NotImplementedError("The tick method must be overridden in subclasses!")


class Selector(Node):
    """
    A composite node that runs its children in order.
    If a child returns RUNNING or SUCCESS, the Selector returns that immediately.
    If a child returns FAILURE, the Selector moves to tick the next child.
    """
    def __init__(self, children):
        # A list of child nodes
        self.children = children
        # String representing which behavior is currently running (for HUD display)
        self.active_behavior = "NONE"

    def tick(self, aircraft, missile, waypoint):
        for child in self.children:
            # Evaluate the child node
            status = child.tick(aircraft, missile, waypoint)
            
            # If the child is running or succeeds, we stop and return its status
            if status == "SUCCESS" or status == "RUNNING":
                # Save the class name of the running node to display on the HUD dashboard
                self.active_behavior = child.__class__.__name__
                return status
        
        # If all children fail, the Selector returns failure
        self.active_behavior = "NONE"
        return "FAILURE"


class EvadeMissile(Node):
    """
    A leaf node that checks if a missile is close.
    If the missile is within SAFE_DISTANCE, it steers the aircraft away from the missile.
    """
    def tick(self, aircraft, missile, waypoint):
        # Check if the missile is active and within the threat zone
        if missile.active and aircraft.distance_to_missile < config.SAFE_DISTANCE:
            # 1. Calculate direction vector pointing AWAY from the missile
            dx = aircraft.x - missile.x
            dy = aircraft.y - missile.y
            
            # 2. Find target angle to escape (opposite to missile)
            target_angle = math.atan2(dy, dx)
            
            # 3. Calculate heading correction
            angle_diff = target_angle - aircraft.angle
            
            # 4. Normalize the angle difference to be within -pi to pi (shortest turn path)
            angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
            
            # 5. Turn the aircraft step-by-step using turn_rate limits
            turn_step = min(aircraft.turn_rate, abs(angle_diff))
            if angle_diff > 0:
                aircraft.angle += turn_step
            else:
                aircraft.angle -= turn_step
                
            # Keep aircraft's angle value within clean [-pi, pi] bounds
            aircraft.angle = (aircraft.angle + math.pi) % (2 * math.pi) - math.pi
            
            # Evasion action is successfully running
            return "RUNNING"
            
        # If no missile is close, this behavior is inactive
        return "FAILURE"


class NavigateToWaypoint(Node):
    """
    A leaf node that steers the aircraft toward the active waypoint.
    """
    def tick(self, aircraft, missile, waypoint):
        # 1. Calculate direction vector pointing TOWARDS the waypoint
        dx = waypoint.x - aircraft.x
        dy = waypoint.y - aircraft.y
        
        # 2. Find target angle to point at the waypoint
        target_angle = math.atan2(dy, dx)
        
        # 3. Calculate heading correction
        angle_diff = target_angle - aircraft.angle
        
        # 4. Normalize the angle difference to be within -pi to pi (shortest turn path)
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
        
        # 5. Turn the aircraft step-by-step using turn_rate limits
        turn_step = min(aircraft.turn_rate, abs(angle_diff))
        if angle_diff > 0:
            aircraft.angle += turn_step
        else:
            aircraft.angle -= turn_step
            
        # Keep aircraft's angle value within clean [-pi, pi] bounds
        aircraft.angle = (aircraft.angle + math.pi) % (2 * math.pi) - math.pi
        
        # Navigation action is successfully running
        return "RUNNING"
