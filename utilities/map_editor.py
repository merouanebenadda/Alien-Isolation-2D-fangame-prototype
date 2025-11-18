"""
MAP EDITOR
Features:
- Zoom (Scroll Wheel) and Pan (Middle Click / Arrows)
- Draw Walls (Left Click)
- Mesh Visualization (Green Grid)
- Save complete Map instance via Pickle (S key)
"""

import pygame
import os
import sys
import pickle

# --- Path Setup ---
# Add project root to path so we can import environment.map, etc.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.append(project_root)

# Import your classes
# NOTE: Ensure 'entities' module exists as Map imports it.
try:
    from environment.map import Map
    from environment.walls import Wall
    from environment.mesh_loader import generate
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure this script is in a subfolder (e.g., 'tools/') and your project structure is correct.")
    sys.exit(1)

# --- Constants & Settings ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
FPS = 60

# Map Settings
MAP_NAME = "map2"
MAP_WIDTH, MAP_HEIGHT = 3000, 3000 # Example large map size
MESH_DENSITY = 40
EDGE_TOLERANCE = 0
OUTPUT_FILE = "maps/map2/map.pkl"

# Colors
COLOR_BG = (30, 30, 30)
COLOR_WALL = (200, 50, 50)
COLOR_WALL_PREVIEW = (200, 100, 50, 100)
COLOR_MESH = (0, 255, 0) # Green for mesh
COLOR_MAP_BORDER = (255, 255, 255)

# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption(f"Map Editor - {MAP_NAME}")
clock = pygame.time.Clock()

# --- Camera Variables ---
camera_offset = [0, 0]
camera_zoom = 1.0
min_zoom = 0.1
max_zoom = 5.0

# --- Editor State ---
# We use a Map instance to hold data
editor_map = Map(MAP_NAME, MAP_WIDTH, MAP_HEIGHT, MESH_DENSITY, EDGE_TOLERANCE)
drawn_rects = [] # Stores pygame.Rects for the editor view
drawing = False
start_pos_world = (0, 0)
current_rect = None

# Load the alien texture
size = (25, 25)
enemy_surface = pygame.image.load('assets/textures/enemy/red_dot.png').convert_alpha()
texture = pygame.transform.scale(enemy_surface, size)

# --- Helper Functions ---

def to_screen(world_x, world_y):
    """Convert world coordinates to screen coordinates."""
    screen_x = (world_x * camera_zoom) + camera_offset[0]
    screen_y = (world_y * camera_zoom) + camera_offset[1]
    return screen_x, screen_y

def to_world(screen_x, screen_y):
    """Convert screen coordinates to world coordinates."""
    world_x = (screen_x - camera_offset[0]) / camera_zoom
    world_y = (screen_y - camera_offset[1]) / camera_zoom
    return world_x, world_y

def adjust_rect(p1, p2):
    """Create a normalized Rect from two points."""
    x = min(p1[0], p2[0])
    y = min(p1[1], p2[1])
    w = abs(p1[0] - p2[0])
    h = abs(p1[1] - p2[1])
    return pygame.Rect(x, y, w, h)

def save_map():
    """Saves the Map instance with computed mesh using pickle."""
    print("--- Saving Map ---")
    
    # 1. Convert editor rects to Wall objects
    new_walls = []
    for r in drawn_rects:
        new_walls.append(Wall(r.x, r.y, r.width, r.height))
    
    editor_map.walls = new_walls
    
    # 2. Generate the Nav Mesh
    # We manually call the loader's generate function to ensure it's fresh
    # or use the map's method if preferred.
    print(f"Generating Mesh (Density: {MESH_DENSITY})...")
    try:
        # We update the internal nav_mesh of the map instance
        editor_map.nav_mesh = generate(editor_map.size, editor_map.walls, MESH_DENSITY, EDGE_TOLERANCE)
        editor_map.wall_corners = editor_map.init_wall_corners()
        print("Mesh generated successfully.")
    except Exception as e:
        print(f"Error generating mesh: {e}")
        return

    # 3. Pickle the Map instance
    try:
        with open(OUTPUT_FILE, 'wb') as f:
            pickle.dump(editor_map, f)
        print(f"Map saved to '{OUTPUT_FILE}'")
    except Exception as e:
        print(f"Error saving pickle: {e}")

# --- Main Loop ---
running = True
pan_active = False
last_mouse_pos = (0, 0)

while running:
    # 1. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Zoom
        elif event.type == pygame.MOUSEWHEEL:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_before = to_world(mouse_x, mouse_y)
            
            zoom_change = 1.1 if event.y > 0 else 0.9
            camera_zoom *= zoom_change
            camera_zoom = max(min_zoom, min(max_zoom, camera_zoom))
            
            # Adjust offset to zoom towards mouse
            world_after_x = (mouse_x - camera_offset[0]) / camera_zoom
            world_after_y = (mouse_y - camera_offset[1]) / camera_zoom
            camera_offset[0] += (world_after_x - world_before[0]) * camera_zoom
            camera_offset[1] += (world_after_y - world_before[1]) * camera_zoom

        # Mouse Buttons
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click: Start Draw
                drawing = True
                start_pos_world = to_world(*event.pos)
                current_rect = pygame.Rect(start_pos_world[0], start_pos_world[1], 0, 0)
            
            elif event.button == 2 or event.button == 3: # Middle/Right: Start Pan
                pan_active = True
                last_mouse_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and drawing: # Stop Draw
                drawing = False
                end_pos_world = to_world(*event.pos)
                final_rect = adjust_rect(start_pos_world, end_pos_world)
                # Only add if it has size
                if final_rect.w > 0 and final_rect.h > 0:
                    drawn_rects.append(final_rect)
                current_rect = None
            
            elif event.button == 2 or event.button == 3: # Stop Pan
                pan_active = False

        elif event.type == pygame.MOUSEMOTION:
            if pan_active:
                dx = event.pos[0] - last_mouse_pos[0]
                dy = event.pos[1] - last_mouse_pos[1]
                camera_offset[0] += dx
                camera_offset[1] += dy
                last_mouse_pos = event.pos
            
            if drawing:
                cur_world = to_world(*event.pos)
                current_rect = adjust_rect(start_pos_world, cur_world)

        # Keyboard
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                save_map()
            elif event.key == pygame.K_c:
                drawn_rects.clear()
                print("Cleared walls.")
            elif event.key == pygame.K_r:
                # Reset Camera
                camera_offset = [0, 0]
                camera_zoom = 1.0

    # 2. Update Logic
    # (Keys for panning)
    keys = pygame.key.get_pressed()
    pan_speed = 10
    if keys[pygame.K_LEFT]: camera_offset[0] += pan_speed
    if keys[pygame.K_RIGHT]: camera_offset[0] -= pan_speed
    if keys[pygame.K_UP]: camera_offset[1] += pan_speed
    if keys[pygame.K_DOWN]: camera_offset[1] -= pan_speed

    # 3. Rendering
    screen.fill(COLOR_BG)

    # -- Draw Mesh Grid (Green) --
    # We draw lines based on density
    # Vertical Lines
    for x in range(0, MAP_WIDTH + 1, MESH_DENSITY):
        start = to_screen(x, 0)
        end = to_screen(x, MAP_HEIGHT)
        # Optimization: Don't draw if off screen
        if 0 <= start[0] <= SCREEN_WIDTH or 0 <= end[0] <= SCREEN_WIDTH: # Simple check
            pygame.draw.line(screen, COLOR_MESH, start, end, 1)
    
    # Horizontal Lines
    for y in range(0, MAP_HEIGHT + 1, MESH_DENSITY):
        start = to_screen(0, y)
        end = to_screen(MAP_WIDTH, y)
        if 0 <= start[1] <= SCREEN_HEIGHT or 0 <= end[1] <= SCREEN_HEIGHT:
            pygame.draw.line(screen, COLOR_MESH, start, end, 1)

    # -- Draw Map Border --
    tl = to_screen(0, 0)
    bl = to_screen(0, MAP_HEIGHT)
    tr = to_screen(MAP_WIDTH, 0)
    br = to_screen(MAP_WIDTH, MAP_HEIGHT)
    pygame.draw.lines(screen, COLOR_MAP_BORDER, True, [tl, tr, br, bl], 2)

    # -- Draw Saved Walls --
    for rect in drawn_rects:
        # Convert world rect to screen rect for drawing
        screen_x, screen_y = to_screen(rect.x, rect.y)
        screen_w = rect.w * camera_zoom
        screen_h = rect.h * camera_zoom
        screen_rect = pygame.Rect(screen_x, screen_y, screen_w, screen_h)
        pygame.draw.rect(screen, COLOR_WALL, screen_rect)

    # -- Draw Preview Wall --
    if current_rect:
        screen_x, screen_y = to_screen(current_rect.x, current_rect.y)
        screen_w = current_rect.w * camera_zoom
        screen_h = current_rect.h * camera_zoom
        
        # Transparent surface
        s = pygame.Surface((int(screen_w), int(screen_h)), pygame.SRCALPHA)
        s.fill(COLOR_WALL_PREVIEW)
        screen.blit(s, (screen_x, screen_y))
        pygame.draw.rect(screen, (255, 255, 255), (screen_x, screen_y, screen_w, screen_h), 1)

    # Draw the alien
    sx, sy = size
    sx, sy = sx*camera_zoom, sy*camera_zoom
    texture = pygame.transform.scale(enemy_surface, (sx, sy))
    screen.blit(texture, (960, 540))

    # -- UI Info --
    font = pygame.font.SysFont("Arial", 18)
    info_text = f"Zoom: {camera_zoom:.2f} | Walls: {len(drawn_rects)} | 'S' to Save, 'C' to Clear, Mouse Wheel to Zoom, Middle Click to Pan"
    text_surf = font.render(info_text, True, (255, 255, 255))
    screen.blit(text_surf, (190, 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()