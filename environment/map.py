from .walls import Wall
from .mesh_loader import generate
from entities import Player, Enemy
import pygame
import os
import math
import pickle

DENSITY = 15

class Map():
    def __init__(self, current_map):
        self.name = current_map
        self.walls = []
        self.background = pygame.image.load(f'maps/{current_map}/background.png')
        self.size = self.background.get_size()
        self.parse_walls()
        self.player_spawn = None 
        self.enemy_spawn = None
        density, edge_tolerance = self.parse_settings()
        self.nav_mesh = self.generate_nav_mesh(density, edge_tolerance)
        self.nav_mesh_walls = self.generate_nav_mesh_walls()
        self.wall_corners = self.init_wall_corners()

 
    def parse_walls(self):
        with open(f"maps/{self.name}/walls.txt") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                try:
                    x, y, height, width = map(int, line.split(','))
                    self.walls.append(Wall(x, y, height, width))
                except ValueError:
                    print(f"Error parsing line : {line}")
                    continue

    def init_wall_corners(self):
        wall_corners = {wall: [] for wall in self.walls}

        # 1. Add real rectangle corners
        for wall in self.walls:
            r = wall.rect
            wall_corners[wall].extend([
                r.topleft, r.topright, r.bottomleft, r.bottomright
            ])

        # Helper: rectangle intersection (pygame doesn't give its rect)
        def rect_intersection(r1, r2):
            x1 = max(r1.left,   r2.left)
            y1 = max(r1.top,    r2.top)
            x2 = min(r1.right,  r2.right)
            y2 = min(r1.bottom, r2.bottom)
            if x1 < x2 and y1 < y2:
                return pygame.Rect(x1, y1, x2 - x1, y2 - y1)
            return None

        # 2. Add corners of intersection rectangles between any overlapping walls
        for i, A in enumerate(self.walls):
            rA = A.rect
            for B in self.walls[i+1:]:
                rB = B.rect

                if rA.colliderect(rB):
                    inter = rect_intersection(rA, rB)
                    if inter:  # intersection has positive area
                        for pt in [inter.topleft, inter.topright, inter.bottomleft, inter.bottomright]:
                            if pt not in wall_corners[A]:
                                wall_corners[A].append(pt)
                            if pt not in wall_corners[B]:
                                wall_corners[B].append(pt)

        return wall_corners

    def parse_settings(self):
        with open(f"maps/{self.name}/settings.txt") as file:
            parsed_data = {}
            for line in file:
                line = line.strip()

                if not line:
                    continue

                try:
                    key, item = line.split(':')
                    key = key.strip()
                    values = list(map(int, item.split(',')))
                    if len(values) == 1:
                        parsed_data[key] = values[0]
                    else:
                        parsed_data[key] = tuple(values)
                except ValueError:
                    print(f"Error parsing line : {line}")
                    continue
            
            self.player_spawn = parsed_data["player_spawn"]
            self.enemy_spawn = parsed_data["enemy_spawn"]
            return parsed_data["density"], parsed_data["edge_tolerance"]

  
    def generate_nav_mesh(self, density, edge_tolerance):
        path = f"maps/{self.name}/navmesh.pkl"
        #commented for debugging, caches mesh calculation
        # if os.path.exists(path):
        #     with open(path, 'rb') as file:
        #         return pickle.load(file)
            
        # else:
        #     mesh = generate(self.size, self.walls, DENSITY)
        #     with open(path, 'wb') as f:
        #         pickle.dump(mesh, f)
        #     return mesh # density = distance in px between two nodes
        mesh = generate(self.size, self.walls, density, edge_tolerance)
        with open(path, 'wb') as f:
            pickle.dump(mesh, f)
        return mesh 
        
    def generate_nav_mesh_walls(self):
        walls = []
        mesh_width, mesh_height = self.nav_mesh.width, self.nav_mesh.height
        density = self.nav_mesh.density
        for i in range(mesh_width):
            for j in range(mesh_height):
                eps = self.nav_mesh.edge_tolerance
                r = pygame.Rect(i * density, j * density, density, density)
                r_inf = pygame.Rect(i * density-eps, j * density-eps, density+2*eps, density+2*eps)
                if r_inf.collidelist(self.walls) != -1:
                    walls.append(Wall(i*density, j*density, density, density))
        return walls

    def point_collidelist(self, point):
        for wall in self.walls:
            if wall.rect.collidepoint(point):
                return True
            
        return False