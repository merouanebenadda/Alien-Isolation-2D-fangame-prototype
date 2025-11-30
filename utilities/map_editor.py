"""
MAP EDITOR - UPDATED
Features:
- Zoom & Pan
- Draw Walls
- Place Vent Nodes & Exits
- CONNECT Vent Nodes (New Mode)
- Visual Feedback (Lines, Selection)
- Enemy Texture Restored
"""

import pygame
import os
import sys
import pickle

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.append(project_root)

# Import your classes
try:
    from environment.map import Map
    from environment.walls import Wall
    from environment.mesh_loader import generate
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

# --- Constants & Settings ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
FPS = 60

# Map Settings
MAP_NAME = "map4"
MAP_WIDTH, MAP_HEIGHT = 750, 750
MESH_DENSITY = 40
EDGE_TOLERANCE = 0
OUTPUT_FILE = f"maps/{MAP_NAME}/map.pkl"

# Ensure directory exists
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# Colors
COLOR_BG = (30, 30, 30)
COLOR_WALL = (200, 50, 50)
COLOR_WALL_PREVIEW = (200, 100, 50, 100)
COLOR_MESH = (0, 255, 0) 
COLOR_MAP_BORDER = (255, 255, 255)

# Vent Colors
COLOR_VENT_NODE = (0, 0, 255, 150)    # Blue
COLOR_VENT_EXIT = (0, 255, 255, 150)  # Cyan
COLOR_VENT_SELECTED = (255, 255, 0, 200) # Yellow (Active selection)
COLOR_VENT_LINK = (200, 200, 200)     # White lines

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
editor_map = Map(MAP_NAME, MAP_WIDTH, MAP_HEIGHT, MESH_DENSITY, EDGE_TOLERANCE)

# Ensure structures exist
if editor_map.vents_mesh is None: editor_map.vents_mesh = {}
if editor_map.vents_access_points is None: editor_map.vents_access_points = []
# Ensure spawn exists if not loaded
if not hasattr(editor_map, 'enemy_spawn') or editor_map.enemy_spawn is None:
    editor_map.enemy_spawn = (0, 0)

drawn_rects = [] 
drawing = False
start_pos_world = (0, 0)
current_rect = None

# Modes
# WALLS: Draw walls
# VENT_NODES: Place grid nodes
# VENT_CONNECT: Link two nodes
# VENT_EXITS: Place access points
modes = ["WALLS", "VENT_NODES", "VENT_CONNECT", "VENT_EXITS"] 
current_mode = "WALLS"

# Selection state for connecting vents
selected_vent_node = None 

# Assets
size = (25, 25)
try:
    enemy_surface = pygame.image.load('assets/textures/alien/red_dot.png').convert_alpha()
except:
    enemy_surface = pygame.Surface((25, 25))
    enemy_surface.fill((255, 0, 0)) # Fallback Red Square

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

def to_grid(world_x, world_y):
    """Convert world coordinates to Mesh Grid Indices (i, j)."""
    i = int(world_x // MESH_DENSITY)
    j = int(world_y // MESH_DENSITY)
    return i, j

def get_tile_center_world(i, j):
    """Returns world coordinates of the center of tile (i, j)."""
    return (i * MESH_DENSITY + MESH_DENSITY / 2, 
            j * MESH_DENSITY + MESH_DENSITY / 2)

def adjust_rect(p1, p2):
    x = min(p1[0], p2[0])
    y = min(p1[1], p2[1])
    w = abs(p1[0] - p2[0])
    h = abs(p1[1] - p2[1])
    return pygame.Rect(x, y, w, h)

def save_map():
    print("--- Saving Map ---")
    
    # 1. Walls
    new_walls = []
    for r in drawn_rects:
        new_walls.append(Wall(r.x, r.y, r.width, r.height))
    editor_map.walls = new_walls
    
    # 2. Generate Nav Mesh
    print(f"Generating Mesh (Density: {MESH_DENSITY})...")
    try:
        editor_map.nav_mesh = generate(editor_map.size, editor_map.walls, MESH_DENSITY, EDGE_TOLERANCE)
        editor_map.wall_corners = editor_map.init_wall_corners()
        print("Mesh generated successfully.")
    except Exception as e:
        print(f"Error generating mesh: {e}")
        return

    # 3. Save
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
            
            world_after_x = (mouse_x - camera_offset[0]) / camera_zoom
            world_after_y = (mouse_y - camera_offset[1]) / camera_zoom
            camera_offset[0] += (world_after_x - world_before[0]) * camera_zoom
            camera_offset[1] += (world_after_y - world_before[1]) * camera_zoom

        # Mouse Buttons
        if event.type == pygame.MOUSEBUTTONDOWN:
            wx, wy = to_world(*event.pos)
            
            # --- WALL MODE ---
            if current_mode == "WALLS":
                if event.button == 1: 
                    drawing = True
                    start_pos_world = (wx, wy)
                    current_rect = pygame.Rect(wx, wy, 0, 0)
                elif event.button == 2 or event.button == 3: 
                    pan_active = True
                    last_mouse_pos = event.pos

            # --- VENT NODE MODE ---
            elif current_mode == "VENT_NODES":
                if event.button == 1: 
                    i, j = to_grid(wx, wy)
                    # Check bounds
                    if 0 <= i < (MAP_WIDTH // MESH_DENSITY) and 0 <= j < (MAP_HEIGHT // MESH_DENSITY):
                        if (i, j) in editor_map.vents_mesh:
                            # Remove node and clean up connections to it
                            del editor_map.vents_mesh[(i, j)]
                            for neighbors in editor_map.vents_mesh.values():
                                if (i, j) in neighbors:
                                    neighbors.remove((i, j))
                        else:
                            editor_map.vents_mesh[(i, j)] = [] 
                elif event.button == 2 or event.button == 3:
                     pan_active = True
                     last_mouse_pos = event.pos

            # --- VENT CONNECT MODE ---
            elif current_mode == "VENT_CONNECT":
                if event.button == 1:
                    i, j = to_grid(wx, wy)
                    if (i, j) in editor_map.vents_mesh:
                        if selected_vent_node is None:
                            selected_vent_node = (i, j)
                        else:
                            # If clicked same node, deselect
                            if selected_vent_node == (i, j):
                                selected_vent_node = None
                            else:
                                # Create bidirectional link
                                if (i, j) not in editor_map.vents_mesh[selected_vent_node]:
                                    editor_map.vents_mesh[selected_vent_node].append((i, j))
                                if selected_vent_node not in editor_map.vents_mesh[(i, j)]:
                                    editor_map.vents_mesh[(i, j)].append(selected_vent_node)
                                selected_vent_node = None # Reset after link
                    else:
                        selected_vent_node = None # Deselect if clicking empty space

                elif event.button == 2 or event.button == 3:
                     pan_active = True
                     last_mouse_pos = event.pos

            # --- VENT EXIT MODE ---
            elif current_mode == "VENT_EXITS":
                if event.button == 1:
                    i, j = to_grid(wx, wy)
                    if 0 <= i < (MAP_WIDTH // MESH_DENSITY) and 0 <= j < (MAP_HEIGHT // MESH_DENSITY):
                        if (i, j) in editor_map.vents_access_points:
                            editor_map.vents_access_points.remove((i, j))
                        else:
                            editor_map.vents_access_points.append((i, j))
                elif event.button == 2 or event.button == 3:
                     pan_active = True
                     last_mouse_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if current_mode == "WALLS":
                if event.button == 1 and drawing: 
                    drawing = False
                    end_pos_world = to_world(*event.pos)
                    final_rect = adjust_rect(start_pos_world, end_pos_world)
                    if final_rect.w > 0 and final_rect.h > 0:
                        drawn_rects.append(final_rect)
                    current_rect = None
                elif event.button == 2 or event.button == 3:
                    pan_active = False
            else:
                 if event.button == 2 or event.button == 3:
                    pan_active = False

        elif event.type == pygame.MOUSEMOTION:
            if pan_active:
                dx = event.pos[0] - last_mouse_pos[0]
                dy = event.pos[1] - last_mouse_pos[1]
                camera_offset[0] += dx
                camera_offset[1] += dy
                last_mouse_pos = event.pos
            
            if drawing and current_mode == "WALLS":
                cur_world = to_world(*event.pos)
                current_rect = adjust_rect(start_pos_world, cur_world)

        # Keyboard
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                save_map()
            elif event.key == pygame.K_c:
                drawn_rects.clear()
            elif event.key == pygame.K_r:
                camera_offset = [0, 0]
                camera_zoom = 1.0
            elif event.key == pygame.K_m:
                # Cycle Modes
                current_index = modes.index(current_mode)
                current_mode = modes[(current_index + 1) % len(modes)]
                selected_vent_node = None # Reset selection on mode switch
                print(f"Switched to mode: {current_mode}")

    # 2. Update Logic
    keys = pygame.key.get_pressed()
    pan_speed = 10
    if keys[pygame.K_LEFT]: camera_offset[0] += pan_speed
    if keys[pygame.K_RIGHT]: camera_offset[0] -= pan_speed
    if keys[pygame.K_UP]: camera_offset[1] += pan_speed
    if keys[pygame.K_DOWN]: camera_offset[1] -= pan_speed

    # 3. Rendering
    screen.fill(COLOR_BG)

    # -- Draw Mesh Grid (Green) --
    for x in range(0, MAP_WIDTH + 1, MESH_DENSITY):
        start = to_screen(x, 0)
        end = to_screen(x, MAP_HEIGHT)
        if 0 <= start[0] <= SCREEN_WIDTH or 0 <= end[0] <= SCREEN_WIDTH:
            pygame.draw.line(screen, COLOR_MESH, start, end, 1)
    
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

    # -- Draw Vent Connections (White Lines) --
    if editor_map.vents_mesh:
        for (i, j), neighbors in editor_map.vents_mesh.items():
            start_center = get_tile_center_world(i, j)
            start_screen = to_screen(*start_center)
            
            for (ni, nj) in neighbors:
                # Simple check to avoid double drawing (only draw if node < neighbor)
                # or just draw everything (easier for bidirectional)
                end_center = get_tile_center_world(ni, nj)
                end_screen = to_screen(*end_center)
                pygame.draw.line(screen, COLOR_VENT_LINK, start_screen, end_screen, 2)

    # -- Draw Vent Nodes (Blue) --
    if editor_map.vents_mesh:
        for (i, j) in editor_map.vents_mesh.keys():
            world_x = i * MESH_DENSITY
            world_y = j * MESH_DENSITY
            screen_x, screen_y = to_screen(world_x, world_y)
            cell_size = MESH_DENSITY * camera_zoom
            
            s = pygame.Surface((int(cell_size), int(cell_size)), pygame.SRCALPHA)
            
            # Highlight selected node in CONNECT mode
            if current_mode == "VENT_CONNECT" and selected_vent_node == (i, j):
                s.fill(COLOR_VENT_SELECTED)
            else:
                s.fill(COLOR_VENT_NODE)
            
            screen.blit(s, (screen_x, screen_y))

    # -- Draw Vent Access Points (Cyan) --
    if editor_map.vents_access_points:
        for (i, j) in editor_map.vents_access_points:
            world_x = i * MESH_DENSITY
            world_y = j * MESH_DENSITY
            screen_x, screen_y = to_screen(world_x, world_y)
            cell_size = MESH_DENSITY * camera_zoom
            padding = cell_size * 0.2
            
            s = pygame.Surface((int(cell_size - padding*2), int(cell_size - padding*2)), pygame.SRCALPHA)
            s.fill(COLOR_VENT_EXIT)
            screen.blit(s, (screen_x + padding, screen_y + padding))

    # -- Draw Walls --
    for rect in drawn_rects:
        screen_x, screen_y = to_screen(rect.x, rect.y)
        screen_w = rect.w * camera_zoom
        screen_h = rect.h * camera_zoom
        pygame.draw.rect(screen, COLOR_WALL, (screen_x, screen_y, screen_w, screen_h))

    # -- Draw Preview Wall --
    if current_rect:
        screen_x, screen_y = to_screen(current_rect.x, current_rect.y)
        screen_w = current_rect.w * camera_zoom
        screen_h = current_rect.h * camera_zoom
        s = pygame.Surface((int(screen_w), int(screen_h)), pygame.SRCALPHA)
        s.fill(COLOR_WALL_PREVIEW)
        screen.blit(s, (screen_x, screen_y))
        pygame.draw.rect(screen, (255, 255, 255), (screen_x, screen_y, screen_w, screen_h), 1)

    # -- Draw Enemy (Alien) --
    # Drawn at center of screen
    screen_cx = SCREEN_WIDTH // 2
    screen_cy = SCREEN_HEIGHT // 2
    # Scale texture
    tex_w = size[0] * camera_zoom
    tex_h = size[1] * camera_zoom
    alien_tex = pygame.transform.scale(enemy_surface, (int(tex_w), int(tex_h)))
    # Centered on screen
    alien_rect = alien_tex.get_rect(center=(screen_cx, screen_cy))
    screen.blit(alien_tex, alien_rect)

    # -- UI Info --
    font = pygame.font.SysFont("Arial", 18)
    info_text = f"Zoom: {camera_zoom:.2f} | Walls: {len(drawn_rects)} | Vents: {len(editor_map.vents_mesh)} | Exits: {len(editor_map.vents_access_points)}"
    text_surf = font.render(info_text, True, (255, 255, 255))
    screen.blit(text_surf, (20, 10))
    
    # Mode Text with color feedback
    mode_color = (255, 255, 255)
    if current_mode == "VENT_NODES": mode_color = (100, 100, 255)
    elif current_mode == "VENT_CONNECT": mode_color = (255, 255, 100)
    elif current_mode == "VENT_EXITS": mode_color = (0, 255, 255)
    
    mode_text = f"MODE: {current_mode} (Press 'M')"
    if current_mode == "VENT_CONNECT" and selected_vent_node:
        mode_text += " - Select Target Node"
        
    mode_surf = font.render(mode_text, True, mode_color)
    screen.blit(mode_surf, (20, 35))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()