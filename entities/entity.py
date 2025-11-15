import pygame
import math
from utilities.geometry import intersects, angle
from numpy import cos, sin
import bisect

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
                
        return True

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


    @staticmethod
    def furthest_point_in_direction(point, angle, current_map):
        x, y = point
        
        step = 1
        x += step*cos(angle*math.pi/180)
        y += step*sin(angle*math.pi/180)

        if current_map.point_collidelist((x, y)):
            return None

        while not current_map.point_collidelist((x, y)):
            x += step*cos(angle*math.pi/180)
            y += step*sin(angle*math.pi/180)

        return x, y
    
    @staticmethod
    def in_fov(angle, orientation, fov):
        eps = 100
        delta = (angle - orientation + 180) % 360 - 180
        return abs(delta) <= fov/2 + eps

    def cast_rays(self, orientation, fov, current_map):
        """
        Casts ray in an angle, and returns a list of triangles formed by the player and successive corners
        """

        pos = self.x_pos, self.y_pos
        corner_angles = []
        triangles_list = []

        pixel_eps = 1e-6
        angle_eps = 1e-6

        right_limit = (orientation-fov/2)%360
        left_limit = (orientation+fov/2)%360

        furthest_right = 0, right_limit, self.furthest_point_in_direction((self.x_pos, self.y_pos), right_limit, current_map) # relative_angle, abs_angle, point
        bisect.insort_left(corner_angles, furthest_right)
        furthest_left = (left_limit-right_limit)%360, left_limit, self.furthest_point_in_direction((self.x_pos, self.y_pos), left_limit, current_map)
        bisect.insort_left(corner_angles, furthest_left)

        for wall in current_map.wall_corners.keys():
            corners = current_map.wall_corners[wall]

            for corner in corners:
                if self.can_see_point(corner, current_map):
                    corner_angle = angle(pos, corner)%360
                    vision_angle = (corner_angle-right_limit)%360, corner_angle, corner

                    if not furthest_right[0] <= vision_angle[0] <= furthest_left[0]: #self.in_fov(vision_angle[0], orientation, fov): #checks if point is within cone of vision
                        continue

                    bisect.insort_left(corner_angles, vision_angle)

                    x = corner[0]-self.x_pos
                    y = corner[1]-self.y_pos
                    norm = math.sqrt(x**2 + y**2)
                    dx_orth, dy_orth = -y/norm*pixel_eps, x/norm*pixel_eps

                    ray_collides_right = wall.rect.collidepoint(corner[0]+dx_orth, corner[1]+dy_orth)
                    ray_collides_left = wall.rect.collidepoint(corner[0]-dx_orth, corner[1]-dy_orth)

                    if ray_collides_right and not ray_collides_left: # we determine in which direction the corner ends
                        furthest = self.furthest_point_in_direction(corner, vision_angle[1], current_map)
                        if furthest == None:
                           continue
                        furthest_point = (vision_angle[0]-angle_eps)%360, (vision_angle[1]+angle_eps)%360, furthest
                        bisect.insort_left(corner_angles, furthest_point)

                    elif ray_collides_left and not ray_collides_right:
                        furthest = self.furthest_point_in_direction(corner, vision_angle[1], current_map)
                        if furthest == None:
                            continue
                        furthest_point = (vision_angle[0]+angle_eps)%360, (vision_angle[1]+angle_eps)%360, furthest
                        bisect.insort_left(corner_angles, furthest_point)

        
        n = len(corner_angles)
        for i in range(n-1):
            triangles_list.append((pos, corner_angles[i][2], corner_angles[(i+1)%n][2])) # i%n so the last triangle that loops back is included

        return triangles_list