# Configuration constants for the DRL Aircraft Simulation

# 1. Screen size variables (width and height in pixels)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# 2. Colors defined in RGB format (Red, Green, Blue values from 0 to 255)
COLOR_BACKGROUND = (15, 23, 42)      # Sleek Slate Navy representing the night sky
COLOR_WHITE = (255, 255, 255)        # Pure white for text and borders
COLOR_AIRCRAFT = (30, 144, 255)      # Dodger Blue for the aircraft body
COLOR_MISSILE = (220, 38, 38)        # Crimson Red for the threatening missile
COLOR_EXPLOSION_INNER = (249, 115, 22) # Bright Orange for the hot core of the explosion
COLOR_EXPLOSION_OUTER = (239, 68, 68)  # Red for the outer blast boundary

# 3. Aircraft parameters
AIRCRAFT_START_SPEED = 3.0
AIRCRAFT_MIN_SPEED = 1.5
AIRCRAFT_MAX_SPEED = 6.0

# 4. Missile parameters
MISSILE_SPEED = 3.2                  # Slightly faster than aircraft's default speed to keep it challenging
MISSILE_COLLISION_RADIUS = 18.0      # How close (in pixels) the missile needs to get to hit the aircraft
MISSILE_SPAWN_DELAY_SEC = 3.0        # Delay in seconds before a missile spawns
EXPLOSION_DURATION_FRAMES = 60       # 60 frames = 1 second at 60 FPS

# 5. Waypoint & Behavior Tree constants
WAYPOINT_RADIUS = 8.0                # Visual radius of the target waypoint circle
COLOR_WAYPOINT = (34, 197, 94)       # Emerald Green for the target waypoint
SAFE_DISTANCE = 180.0                # Radius in pixels within which evasion behavior is triggered

