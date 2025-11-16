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
        self.base_speed = 1
        self.sprint_speed = 3
        self.rush_speed = 5
        self.state = 'COMPUTE_PATROL' # 'RUSH', 'FIND', 'PATROL', 'HISS', 'SEARCH'
        self.rush_threshold = 64
        
        # --- Pathfinding and Navigation ---
        self.current_path = None
        self.next_position = None
        self.current_objective = None
        self.is_on_unaccessible_tile = None
        self.rush_range = 100
        self.kill_range = self.ENEMY_SIZE[0]
        self.patrol_range = (350, 1e9)
        self.search_range = (50, 150)
        
        # --- Timing and Refresh ---
        self.last_path_computation_time = 0
        self.path_computation_refresh = 1000 # in ms
        self.hiss_timer = 0
        self.hiss_duration = 2000
        self.chase_timer = 0
        self.chase_duration = 10000
        self.search_timer = 0
        self.search_duration = 5000

    def switch_state(self, state):
        current_time = pygame.time.get_ticks()
        if state in ['COMPUTE_SEARCH', 'COMPUTE_PATROL', 'HISS']:
            self.hiss_timer = current_time
            self.chase_timer = current_time
            self.search_timer = current_time

        self.state = state

    def rush(self, player:Player, current_map, dt):
        old_x = self.x_pos
        old_y = self.y_pos

        self.current_speed = self.rush_speed

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
            self.switch_state('COMPUTE_CHASE')
        if pygame.time.get_ticks() - self.hiss_timer > self.hiss_duration:
            self.switch_state('COMPUTE_CHASE')

    def update_rush(self, player, current_map, dt):
        self.current_speed = self.rush_speed
        if self.can_see_entity(player, current_map):
            self.rush(player, current_map, dt)
        else:
            self.switch_state('COMPUTE_SEARCH')

    def update_finding(self, player, current_map, dt):
        self.update_path(player, current_map)
        self.last_path_computation_time = pygame.time.get_ticks()
        self.switch_state('CHASE')

    def update_compute_chase(self, player, current_map, dt):
        self.is_on_unaccessible_tile, path = current_map.nav_mesh.compute_path(self, (player.x_pos, player.y_pos)) 
        
        if path: # Check for truthiness of path (not None)
            self.current_path = path
            self.next_position = self.current_path.pop()
            self.current_objective = (player.x_pos, player.y_pos)
            self.last_path_computation_time = pygame.time.get_ticks()
            self.switch_state('CHASE')
        else:
            # If the random point is unreachable, stay in COMPUTE_PATROL 
            # (or switch to a neutral 'IDLE' state) and try again next frame.
            self.last_path_computation_time = pygame.time.get_ticks()
            pass

    def update_chase(self, player, current_map, dt):
        self.current_speed = self.sprint_speed
        if self.can_see_entity(player, current_map) and pygame.time.get_ticks() - self.last_path_computation_time > self.path_computation_refresh:
            self.switch_state('COMPUTE_CHASE')

        # try:
        #     self.follow_path(current_map, dt)
        # except ValueError:
        #     self.switch_state('COMPUTE_CHASE')
        if self.can_see_entity(player, current_map):
            try:
                self.follow_path(current_map, dt)
            except ValueError:
                self.switch_state('COMPUTE_CHASE')
        elif pygame.time.get_ticks() - self.chase_timer < self.chase_duration:
            try:
                self.follow_path(current_map, dt)
            except ValueError:
                self.switch_state('COMPUTE_SEARCH')
        else:
            if pygame.time.get_ticks() - self.chase_timer > self.chase_duration:
                self.switch_state('COMPUTE_SEARCH')

    def update_compute_patrol(self, current_map, dt):
        if pygame.time.get_ticks() - self.last_path_computation_time < self.path_computation_refresh: 
             return

        rand_x, rand_y =  current_map.nav_mesh.random_tile(self, self.patrol_range)

        self.is_on_unaccessible_tile, path = current_map.nav_mesh.compute_path(self, (rand_x, rand_y)) 
        
        if path:
            self.current_path = path
            self.next_position = self.current_path.pop()
            self.current_objective = (rand_x, rand_y)
            self.switch_state('PATROL')
        else:
            self.last_path_computation_time = pygame.time.get_ticks()
            pass

    def update_patrol(self, current_map, dt):
        self.current_speed = self.base_speed
        try:
            self.follow_path(current_map, dt)
        except ValueError:
            self.switch_state('COMPUTE_PATROL')

    def update_compute_search(self, current_map, dt): 

        rand_x, rand_y =  current_map.nav_mesh.random_tile(self, self.search_range)

        self.is_on_unaccessible_tile, path = current_map.nav_mesh.compute_path(self, (rand_x, rand_y)) 
        
        if path:
            self.current_path = path
            self.next_position = self.current_path.pop()
            self.current_objective = (rand_x, rand_y)
            self.switch_state('SEARCH')
        else:
            self.last_path_computation_time = pygame.time.get_ticks()
            pass
    
    def update_search(self, current_map, dt):
        self.current_speed = self.base_speed
        if pygame.time.get_ticks() - self.search_timer > self.search_duration:
            self.switch_state('COMPUTE_PATROL')
        else:    
            try:
                self.follow_path(current_map, dt)
            except ValueError:
                self.switch_state('COMPUTE_SEARCH')

    def update_kill(self, player, current_map, dt):
        # insert the animation logic

        player.is_alive = False
    
    def update(self, player, current_map, dt):
        self.current_speed = self.base_speed
        current_time = pygame.time.get_ticks()

        print(self.state)

        if (self.can_see_entity(player, current_map) and geometry.euclidian_distance_entities(self, player) < self.kill_range):
            self.switch_state('KILL')

        elif (self.can_see_entity(player, current_map) and geometry.euclidian_distance_entities(self, player) < self.rush_range):
            self.switch_state('RUSH')
        
        elif (self.state != 'HISS' and self.state != 'CHASE' and self.state != 'COMPUTE_CHASE'
            and self.can_see_entity(player, current_map)):
            self.switch_state('HISS')
            
        if self.state == 'HISS':
            self.update_hiss(player, current_map, dt)

        if self.state == 'COMPUTE_CHASE':
            self.update_compute_chase(player, current_map, dt)

        if self.state == 'CHASE':
            self.update_chase(player, current_map, dt)

        if self.state == 'FINDING':
            self.update_finding(player, current_map, dt)

        if self.state == 'COMPUTE_PATROL':
            self.update_compute_patrol(current_map, dt)

        if self.state == 'PATROL':
            self.update_patrol(current_map, dt)

        if self.state == 'COMPUTE_SEARCH':
            self.update_compute_search(current_map, dt)
        
        if self.state == 'SEARCH':
            self.update_search(current_map, dt)

        if self.state == 'RUSH':
            self.update_rush(player, current_map, dt)

        if self.state == 'KILL':
            self.update_kill(player, current_map, dt)


        # additional states to implement : 'SEARCH' after unsuccessful chase, 'ROAM' which is a patrol but picks random close points, 'VENT', 'KILL', 'STANDBY'
        # also, 'CHASE' currently follows the player, but when losing LoS, should go to last seen position or slightly after