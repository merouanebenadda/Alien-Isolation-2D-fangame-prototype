import pygame
import math
from utilities.geometry import intersects

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # --- Position and Graphics ---
        self.x_pos, self.y_pos = x, y
        self.x_speed, self.y_speed = 0, 0
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.rect.center = (x, y)
        
        # --- Movement and State ---
        self.base_speed = 1
        self.sprint_speed = 5
        self.current_speed = self.base_speed

    def go_to(self, position, current_map, dt):
        x, y = position
        old_x = self.x_pos
        old_y = self.y_pos

        self.current_speed = self.base_speed

        if x == self.x_pos and y == self.y_pos:
            return None

        movement_vector_x = x - self.x_pos
        movement_vector_y = y - self.y_pos

        norm = math.sqrt(movement_vector_x**2 + movement_vector_y**2)
        
        if norm != 0:
            self.move(movement_vector_x, movement_vector_y, norm, old_x, old_y, current_map, dt)

    def move(self, movement_vector_x, movement_vector_y, norm, old_x, old_y, current_map, dt):
        self.x_pos += movement_vector_x/norm * self.current_speed
        self.rect.center = (self.x_pos, self.y_pos)
        dx = self.x_pos - old_x
        self.x_speed = dx/dt
        self.resolve_collision_x(current_map, dx)
        
        self.y_pos += movement_vector_y/norm * self.current_speed
        self.rect.center = (self.x_pos, self.y_pos)
        dy = self.y_pos - old_y
        self.y_speed = dy/dt
        self.resolve_collision_y(current_map, dy)

    def can_see_entity(self, entity, current_map):
        ray = (self.rect.center, entity.rect.center)

        for wall in current_map.walls:
            A = (wall.rect.left, wall.rect.top)
            B = (wall.rect.right, wall.rect.top)
            C = (wall.rect.right, wall.rect.bottom)
            D = (wall.rect.left, wall.rect.bottom)

            wall_edges = [(A, B), (B, C), (C, D), (D, A)]

            for edge in wall_edges:
                if intersects(ray, edge):
                    return False
                
        return True
    
    def can_see_point(self, point, current_map):
        ray = (self.rect.center, point)

        for wall in current_map.walls:
            A = (wall.rect.left, wall.rect.top)
            B = (wall.rect.right, wall.rect.top)
            C = (wall.rect.right, wall.rect.bottom)
            D = (wall.rect.left, wall.rect.bottom)

            wall_edges = [(A, B), (B, C), (C, D), (D, A)]

            for edge in wall_edges:
                if intersects(ray, edge):
                    return False
                
        return 

    def can_go_to_point(self, point, current_map):
        ray = (self.rect.center, point)

        for wall in current_map.nav_mesh_walls:
            A = (wall.rect.left, wall.rect.top)
            B = (wall.rect.right, wall.rect.top)
            C = (wall.rect.right, wall.rect.bottom)
            D = (wall.rect.left, wall.rect.bottom)

            wall_edges = [(A, B), (B, C), (C, D), (D, A)]

            for edge in wall_edges:
                if intersects(ray, edge):
                    return False
                
        return True
    
    def resolve_collision_x(self, current_map, dx):
        for wall in current_map.walls:
            if wall.rect.colliderect(self.rect):
                if dx < 0 and self.rect.left < wall.rect.right:
                    self.rect.left = wall.rect.right
                    self.x_speed = 0
                if dx > 0 and self.rect.right > wall.rect.left:
                    self.rect.right = wall.rect.left
                    self.x_speed = 0
                    
                self.x_pos, self.y_pos = self.rect.center

    def resolve_collision_y(self, current_map, dy):
        for wall in current_map.walls:
            if wall.rect.colliderect(self.rect):
                if dy < 0 and self.rect.top < wall.rect.bottom:
                    self.rect.top = wall.rect.bottom
                    self.y_speed = 0
                    
                if dy > 0 and self.rect.bottom > wall.rect.top:
                    self.rect.bottom = wall.rect.top
                    self.y_speed = 0

                self.x_pos, self.y_pos = self.rect.center

