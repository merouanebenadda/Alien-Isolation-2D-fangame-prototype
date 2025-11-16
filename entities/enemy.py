from .entity import Entity
from .player import Player
from utilities.mesh import Mesh
from utilities import geometry
import pygame
import math
import sys

class Enemy(Entity):
    def __init__(self, x, y=None):
        if y == None: x, y = x
        super().__init__(x, y)
        
        # --- Appearance and Collision ---
        self.ENEMY_SIZE = (25, 25)
        enemy_surface = pygame.image.load('textures/enemy/red_dot.png').convert_alpha()
        self.texture = pygame.transform.scale(enemy_surface, self.ENEMY_SIZE)
        self.rect = self.texture.get_rect()
        self.rect.center = (x, y)
        
        # --- Movement and State ---
        self.sprint_speed = 3
        self.catch_speed = 5
        self.state = 'COMPUTE_PATROL' # 'RUSH', 'FIND', 'PATROL', 'HISS', 'SEARCH'
        self.rush_threshold = 64
        
        # --- Pathfinding and Navigation ---
        self.current_path = None
        self.next_position = None
        self.current_objective = None
        self.is_on_unaccessible_tile = None
        
        # --- Timing and Refresh ---
        self.last_path_computation_time = 0
        self.path_computation_refresh = 1000 # in ms
        self.hiss_timer = 0
        self.hiss_duration = 2000
        self.chase_timer = 0
        self.chase_duration = 3000

    def rush(self, player:Player, current_map, dt):
        old_x = self.x_pos
        old_y = self.y_pos

        self.current_speed = self.sprint_speed

        if player.x_pos == self.x_pos and player.y_pos == self.y_pos:
            return None

        movement_vector_x = player.x_pos - self.x_pos
        movement_vector_y = player.y_pos - self.y_pos

        norm = math.sqrt(movement_vector_x**2 + movement_vector_y**2)
        
        if norm != 0:
            super().move(movement_vector_x, movement_vector_y, norm, old_x, old_y, current_map, dt)

    def update_path(self, player, current_map):
        player_pos = player.rect.centerx, player.rect.centery
        self.is_on_unaccessible_tile, path = current_map.nav_mesh.compute_path(self, player_pos)
        if path != None: 
            self.current_path = path
            self.next_position = self.current_path.pop()
            self.current_objective = (player.x_pos, player.y_pos)
        else:
            return None

    def follow_path(self, current_map, dt):
        corner_tolerance = current_map.nav_mesh.density*2*math.sqrt(2) # allows the enemy to cur corners if next way point is under this distance

        if not self.current_path and geometry.euclidian_distance((self.x_pos, self.y_pos), self.next_position) < self.ENEMY_SIZE[0]//2:
            raise ValueError
        
        if self.is_on_unaccessible_tile:
            while self.current_path and (self.can_see_point(self.current_path[-1], current_map) 
                                        and geometry.euclidian_distance((self.x_pos, self.y_pos), self.current_path[-1]) < corner_tolerance):
                self.next_position = self.current_path.pop()
        else:
            while self.current_path and ((self.can_see_point(self.current_path[-1], current_map) 
                                          and geometry.euclidian_distance((self.x_pos, self.y_pos), self.current_path[-1]) < corner_tolerance) 
                                         or (self.can_go_to_point(self.current_path[-1], current_map) 
                                    and geometry.euclidian_distance((self.x_pos, self.y_pos), self.current_path[-1]) < 100)):
                self.next_position = self.current_path.pop()
        
        if self.current_path and geometry.euclidian_distance((self.x_pos, self.y_pos), self.next_position) < self.ENEMY_SIZE[0]//2:
            self.next_position = self.current_path.pop()

        super().go_to(self.next_position, current_map, dt)

    def update_hiss(self, player, current_map, dt):
        if not self.can_see_entity(player, current_map):
            self.chase_timer = pygame.time.get_ticks()
            self.state = 'COMPUTE_CHASE'
        if pygame.time.get_ticks() - self.hiss_timer > self.hiss_duration:
            self.state = 'COMPUTE_CHASE'

    def update_rush(self, player, current_map, dt):
        self.current_speed = self.catch_speed
        if self.can_see_entity(player, current_map):
            self.rush(player, current_map, dt)
        else:
            self.state = 'FINDING'

    def update_finding(self, player, current_map, dt):
        self.update_path(player, current_map)
        self.last_path_computation_time = pygame.time.get_ticks()
        self.state = 'CHASE'

    def update_compute_chase(self, player, current_map, dt):
        self.chase_timer = pygame.time.get_ticks()
        # Ensure path computation is only done periodically to avoid lag
        if pygame.time.get_ticks() - self.last_path_computation_time < 1000: 
             return

        # The path computation function should ideally take a target position tuple
        self.is_on_unaccessible_tile, path = current_map.nav_mesh.compute_path(self, (player.x_pos, player.y_pos)) 
        
        if path: # Check for truthiness of path (not None)
            self.current_path = path
            self.next_position = self.current_path.pop()
            self.current_objective = (player.x_pos, player.y_pos)
            self.state = 'CHASE'
        else:
            # If the random point is unreachable, stay in COMPUTE_PATROL 
            # (or switch to a neutral 'IDLE' state) and try again next frame.
            self.last_path_computation_time = pygame.time.get_ticks()
            pass

    def update_chase(self, player, current_map, dt):
        self.current_speed = self.sprint_speed
        if pygame.time.get_ticks() - self.last_path_computation_time > self.path_computation_refresh:
            self.state = 'COMPUTE_CHASE'
        if self.can_see_entity(player, current_map) or pygame.time.get_ticks() - self.chase_timer < self.chase_duration:
            try:
                self.follow_path(current_map, dt)
            except ValueError:
                self.state = 'COMPUTE_CHASE'
        else:
            if pygame.time.get_ticks() - self.chase_timer > self.chase_duration:
                self.state = 'PATROL'

    def update_compute_patrol(self, current_map, dt):
        if pygame.time.get_ticks() - self.last_path_computation_time < self.path_computation_refresh: 
             return

        rand_x, rand_y =  current_map.nav_mesh.random_tile(self) # Assuming this gets coordinates

        self.is_on_unaccessible_tile, path = current_map.nav_mesh.compute_path(self, (rand_x, rand_y)) 
        
        if path:
            self.current_path = path
            self.next_position = self.current_path.pop()
            self.current_objective = (rand_x, rand_y)
            self.state = 'PATROL'
        else:
            self.last_path_computation_time = pygame.time.get_ticks()
            pass

    def update_patrol(self, current_map, dt):
        self.current_speed = self.base_speed
        try:
            self.follow_path(current_map, dt)
        except ValueError:
            self.state = 'COMPUTE_PATROL'
    
    
    def update(self, player, current_map, dt):
        self.current_speed = self.base_speed
        current_time = pygame.time.get_ticks()

        print(self.state)
        
        if (self.state != 'HISS' and self.state != 'CHASE' and self.state != 'COMPUTE_CHASE'
            and self.can_see_entity(player, current_map)):# and geometry.euclidian_distance_entities(self, player) < self.rush_threshold:
            self.state = 'HISS'
            self.hiss_timer = pygame.time.get_ticks()
            
        if self.state == 'HISS':
            self.update_hiss(player, current_map, dt)

        if self.state == 'CHASE':
            self.update_chase(player, current_map, dt)

        if self.state == 'FINDING':
            self.update_finding(player, current_map, dt)

        if self.state == 'COMPUTE_PATROL':
            self.update_compute_patrol(current_map, dt)

        if self.state == 'PATROL':
            self.update_patrol(current_map, dt)

        if self.state == 'COMPUTE_CHASE':
            self.update_compute_chase(player, current_map, dt)