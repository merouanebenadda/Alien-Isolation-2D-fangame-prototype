"""

Notes : 
- I set corner_tolerance to 0 so the enemy does not get stuck in corners during testing
"""

from .entity import Entity
from .player import Player
from utilities.mesh import Mesh
from utilities.geometry import euclidian_distance, euclidian_distance_entities, angle, angle_entity
import pygame
import math
from random import gauss, randint
import sys

class Alien(Entity):
    def __init__(self, x, y=None):
        if y == None: x, y = x
        super().__init__(x, y)
        
        # --- Appearance and Collision ---
        self.size = (25, 25)
        self.rect = pygame.rect.Rect(0, 0, self.size[0], self.size[1])

        self.body_size = (25, 25)
        self.body_surface = pygame.image.load('assets/textures/alien/red_dot.png').convert_alpha()
        self.body_texture_original = pygame.transform.scale(self.body_surface, self.body_size)
        self.body_texture = self.body_texture_original
        self.body_rect = self.body_texture.get_rect()
        self.rect.center = (x, y)

        self.head_size = (36, 10)
        self.head_pivot = (15, 5)
        # self.head_surface = pygame.image.load('assets/textures/alien/head.png').convert_alpha()
        # self.head_texture_original = pygame.transform.scale(self.head_surface, self.head_size)
        # self.head_texture = self.head_texture_original
        # self.head_rect = self.head_texture.get_rect()

        
        # --- Movement and State ---
        self.current_speed = 0
        self.base_speed = 1
        self.search_speed = 2
        self.sprint_speed = 4
        self.rush_speed = 9
        self.state = 'COMPUTE_VENT_PATROL' # 'RUSH', 'FIND', 'PATROL', 'HISS', 'SEARCH'
        self.rush_threshold = 64
        self.previous_state = None

        self.heading_orientation = 0 # where the alien is heading to
        self.orientation = 0 # the actual orientation of the alien
        self.look_to = 0 # where the alien should look
        self.look_orientation = 0 # where he actually looks
        self.fov = 90

        self.direction_vector_x = 0
        self.direction_vector_y = 0

        self.body_angular_velocity = 0 #in degrees per second
        self.body_angular_acceleration = 10000 # in degrees/s^2

        self.look_angular_velocity = 0 #in degrees per second
        self.look_angular_acceleration = 50000 # in degrees/s^2

        self.is_in_frontstage = False
        
        # --- Pathfinding and Navigation ---
        self.current_path = None # list of (x, y) positions
        self.next_position = None
        self.current_objective = None
        self.is_on_unaccessible_tile = None
        self.rush_range = 100
        self.kill_range = self.size[0]
        self.patrol_range = (500, 1e9)
        self.search_range = (40, 250)
        
        # --- Timing and Refresh ---
        self.last_path_computation_time = 0
        self.path_computation_refresh = 1000 # in ms
        self.hiss_timer = 0
        self.hiss_duration = 3000
        self.patrol_look_around_timer = 0
        self.patrol_look_around_duration = 0
        self.patrol_look_around_mean = 2000
        self.patrol_look_around_std_dev = 750
        self.chase_timer = 0
        self.chase_duration = 10000
        self.search_timer = 0
        self.search_duration = 25000
        self.look_around_timer = 0
        self.look_around_duration = 0
        self.look_around_turn_timer = 0
        self.look_around_mean = 6000
        self.look_around_std_dev = 2000
        self.look_around_turn_delay = 0
        self.look_around_turn_delay_mean = 1500
        self.look_around_turn_delay_std_dev = 750
        self.last_time_seen = 0
        self.follow_after_lost_sight_duration = 5000

        # Audio logic

        self.is_walking = False
        self.is_running = False


        self.last_step_time = 0
        self.walk_step_delay = 700
        self.run_step_delay = 400

    def update_textures(self):
        self.body_texture = pygame.transform.rotate(self.body_texture_original, -self.orientation)
        # self.head_texture = pygame.transform.rotate(self.head_texture_original, -self.look_orientation)

    def update_look_orientation(self, player, current_map, dt):
        now = pygame.time.get_ticks()
        ANGULAR_VELOCITY_CAP = 10800

        goal_orientation = self.look_to
        if self.state == 'PATROL' and now - self.patrol_look_around_timer > self.patrol_look_around_duration:
            goal_orientation = self.orientation
        if self.entity_in_fov(player, current_map):
            self.look_to = angle_entity(self, player)
        elif self.state in ['CHASE', 'SEARCH']:
            goal_orientation = self.heading_orientation

        angle_diff = goal_orientation - self.look_orientation
        angle_diff = (angle_diff + 540)%360 - 180 # normalize the difference to (-180, 180]

        if abs(angle_diff) < 1e-1:
            self.look_angular_velocity = 0

        self.look_angular_velocity += self.look_angular_acceleration*dt
        self.look_angular_velocity = min(self.look_angular_velocity, ANGULAR_VELOCITY_CAP)
        max_step = self.look_angular_velocity*dt

        if abs(angle_diff) > max_step:
            if angle_diff > 0:
                turn = max_step
            else:
                turn = -max_step
        else:
            turn = angle_diff

        self.look_orientation = (self.look_orientation+turn)%360

    def update_orientation(self, player, current_map, dt):
        now = pygame.time.get_ticks()
        ANGULAR_VELOCITY_CAP = 180

        goal_orientation = self.heading_orientation

        angle_diff = goal_orientation - self.orientation
        angle_diff = (angle_diff + 540)%360 - 180 # normalize the difference to (-180, 180]

        if abs(angle_diff) < 1e-1:
            self.body_angular_velocity = 0

        if self.entity_in_fov(player, current_map):
            self.heading_orientation = angle_entity(self, player)

        self.body_angular_velocity += self.body_angular_acceleration*dt
        self.body_angular_velocity = min(self.body_angular_velocity, ANGULAR_VELOCITY_CAP)
        max_step = self.body_angular_velocity*dt

        if abs(angle_diff) > max_step:
            if angle_diff > 0:
                turn = max_step
            else:
                turn = -max_step
        else:
            turn = angle_diff

        self.orientation = (self.orientation+turn)%360

    def switch_state(self, state, sound_manager=None):
        now = pygame.time.get_ticks()
        self.previous_state = self.state

        if state in ['COMPUTE_CHASE', 'COMPUTE_SEARCH', 'COMPUTE_PATROL', 'HISS'] and self.previous_state != 'LOOK_AROUND':
            self.hiss_timer = now
            self.search_timer = now

        if state == 'COMPUTE_CHASE' and self.previous_state != 'CHASE':
            self.chase_timer = now
            
        if state == 'LOOK_AROUND':
            self.look_angular_velocity = 0
            self.look_around_duration = gauss(self.look_around_mean, self.look_around_std_dev)
            self.look_around_timer = now

        if state == 'KILL':
            sound_manager.play_sfx('kill')

        if state == 'HISS':
            sound_manager.play_sfx('hiss')

        if state == 'ENTER_VENT' or state == 'EXIT_VENT':
            self.is_in_frontstage = not self.is_in_frontstage

        self.state = state

    def rush(self, player, current_map, dt):
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
        corner_tolerance = 0 #current_map.nav_mesh.density*2*math.sqrt(2) # allows the enemy to cur corners if next way point is under this distance

        if not self.current_path and euclidian_distance((self.x_pos, self.y_pos), self.next_position) < self.size[0]//2:
            raise ValueError
        
        if self.is_on_unaccessible_tile:
            while self.current_path and (self.can_see_point(self.current_path[-1], current_map) 
                                        and euclidian_distance((self.x_pos, self.y_pos), self.current_path[-1]) < corner_tolerance):
                self.next_position = self.current_path.pop()
        else:
            while self.current_path and ((self.can_see_point(self.current_path[-1], current_map) 
                                          and euclidian_distance((self.x_pos, self.y_pos), self.current_path[-1]) < corner_tolerance) 
                                         or (self.can_go_to_point(self.current_path[-1], current_map) 
                                    and euclidian_distance((self.x_pos, self.y_pos), self.current_path[-1]) < 500)):
                self.next_position = self.current_path.pop()
        
        if self.current_path and euclidian_distance((self.x_pos, self.y_pos), self.next_position) < self.size[0]//2:
            self.next_position = self.current_path.pop()

        super().go_to(self.next_position, current_map, dt)

    def follow_vent_path(self, current_map, dt):
        if (euclidian_distance((self.x_pos, self.y_pos), self.current_objective) < self.size[0]//2):
            raise ValueError
        if self.current_path and euclidian_distance((self.x_pos, self.y_pos), self.next_position) < self.size[0]//2:
            self.next_position = self.current_path.pop()
        super().go_to(self.next_position, current_map, dt)

    def update_hiss(self, player, current_map, dt):
        if not self.entity_in_fov(player, current_map):
            self.switch_state('COMPUTE_CHASE')
        if pygame.time.get_ticks() - self.hiss_timer > self.hiss_duration:
            self.switch_state('COMPUTE_CHASE')

    def update_rush(self, player, current_map, dt):
        self.current_speed = self.rush_speed
        if self.entity_in_fov(player, current_map):
            self.rush(player, current_map, dt)
        else:
            self.switch_state('COMPUTE_SEARCH')

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
        now = pygame.time.get_ticks()
        self.current_speed = self.sprint_speed
        if self.entity_in_fov(player, current_map) and now - self.last_path_computation_time > self.path_computation_refresh:
            self.switch_state('COMPUTE_CHASE')

        if self.entity_in_fov(player, current_map):
            try:
                self.follow_path(current_map, dt)
            except ValueError:
                self.switch_state('COMPUTE_CHASE')
        elif now - self.last_time_seen < self.follow_after_lost_sight_duration:
            try:
                self.follow_path(current_map, dt)
            except ValueError:
                self.switch_state('COMPUTE_CHASE')
        elif now - self.chase_timer < self.chase_duration:
            try:
                self.follow_path(current_map, dt)
            except ValueError:
                self.switch_state('COMPUTE_CHASE')
        else:
            if now - self.chase_timer > self.chase_duration:
                self.switch_state('COMPUTE_SEARCH')

    def update_compute_patrol(self, current_map, dt):
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
        now = pygame.time.get_ticks()
        self.current_speed = self.base_speed
        if now-self.patrol_look_around_timer > self.patrol_look_around_duration:
            self.patrol_look_around_duration = gauss(self.patrol_look_around_mean, self.patrol_look_around_std_dev)
            self.patrol_look_around_timer = now
            self.look_to = self.heading_orientation +  int(gauss(0, 30))
        try:
            self.follow_path(current_map, dt)
        except ValueError:
            self.switch_state('LOOK_AROUND')

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
        self.current_speed = self.search_speed
        if pygame.time.get_ticks() - self.search_timer > self.search_duration:
            self.switch_state('COMPUTE_PATROL')
        else:    
            try:
                self.follow_path(current_map, dt)
            except ValueError:
                self.switch_state('LOOK_AROUND')

    def update_compute_vent_patrol(self, current_map, dt):
        random_point = current_map.vents_mesh.random_point()
        if random_point == None:
            self.last_path_computation_time = pygame.time.get_ticks()
            return
        rand_x, rand_y = current_map.vents_mesh.random_point()

        path = current_map.vents_mesh.compute_path(self, (rand_x, rand_y))
        
        if path:
            self.current_path = path
            self.next_position = self.current_path.pop()
            self.current_objective = (rand_x, rand_y)
            self.switch_state('VENT_PATROL')
        else:
            self.last_path_computation_time = pygame.time.get_ticks()
            pass

    def update_vent_patrol(self, current_map, dt):
        now = pygame.time.get_ticks()
        self.current_speed = self.base_speed
        try:
            self.follow_vent_path(current_map, dt)
        except ValueError:
            self.switch_state('COMPUTE_VENT_PATROL')

    def update_compute_nearest_vent_entry(self, current_map, dt):
        nearest_entry = current_map.vents_mesh.get_closest_vent_access((self.x_pos, self.y_pos))
        x, y = nearest_entry

        _, path = current_map.nav_mesh.compute_path(self, (x, y))
        
        if path:
            self.current_path = path
            self.next_position = self.current_path.pop()
            self.current_objective = (x, y)
            self.switch_state('GO_TO_NEAREST_VENT_ENTRY')
        else:
            self.last_path_computation_time = pygame.time.get_ticks()
            pass

    def update_go_to_nearest_vent_entry(self, current_map, dt):
        now = pygame.time.get_ticks()
        self.current_speed = self.base_speed
        try:
            self.follow_path(current_map, dt)
        except ValueError:
            self.switch_state('ENTER_VENT')

    def update_enter_vent(self, sound_manager):
        # Animation logic to be added
        sound_manager.play_sfx('enter_vent')
        self.switch_state('COMPUTE_VENT_PATROL')

    def update_compute_nearest_vent_exit(self, current_map, dt):
        nearest_exit = current_map.vents_mesh.get_closest_vent_access((self.x_pos, self.y_pos))
        x, y = nearest_exit

        path = current_map.vents_mesh.compute_path(self, (x, y))
        
        if path:
            self.current_path = path
            self.next_position = self.current_path.pop()
            self.current_objective = (x, y)
            self.switch_state('GO_TO_NEAREST_VENT_EXIT')
        else:
            self.last_path_computation_time = pygame.time.get_ticks()
            pass

    def update_go_to_nearest_vent_exit(self, current_map, dt):
        now = pygame.time.get_ticks()
        self.current_speed = self.base_speed
        try:
            self.follow_vent_path(current_map, dt)
        except ValueError:
            self.switch_state('EXIT_VENT')

    def update_exit_vent(self, sound_manager):
        # Animation logic to be added

        sound_manager.play_sfx('exit_vent')
        self.switch_state('COMPUTE_PATROL')

    def update_look_around(self):
        now = pygame.time.get_ticks()
        if now - self.look_around_turn_timer > self.look_around_duration:
            self.look_around_turn_timer = now
            self.look_around_turn_duration = gauss(self.look_around_turn_delay_mean, self.look_around_turn_delay_std_dev)
            self.look_to = randint(0, 359)
            self.heading_orientation = self.look_to

        if now-self.look_around_timer > self.look_around_duration:
            prev_state = self.previous_state
            self.previous_state = 'LOOK_AROUND'
            self.switch_state('COMPUTE_' + prev_state)

    def update_kill(self, player, current_map, dt):
        # insert the animation logic

        player.is_alive = False
    
    def update(self, player, current_map, sound_manager, dt):
        old_x = self.x_pos
        old_y = self.y_pos

        self.current_speed = self.base_speed
        current_time = pygame.time.get_ticks()

        self.update_orientation(player, current_map, dt)
        self.update_look_orientation(player, current_map, dt)

        #self.update_textures()

        if self.state == 'SEARCH' and self.entity_in_fov(player, current_map):
            self.switch_state('CHASE', sound_manager)

        elif (self.state != 'KILL' and 
            self.entity_in_fov(player, current_map) and euclidian_distance_entities(self, player) < self.kill_range):
            self.switch_state('KILL', sound_manager)

        elif (self.state != 'KILL' and self.entity_in_fov(player, current_map) and euclidian_distance_entities(self, player) < self.rush_range):
            self.switch_state('RUSH')
        
        elif (self.state != 'KILL' and self.state != 'HISS' and self.state != 'CHASE' and self.state != 'COMPUTE_CHASE'
            and self.entity_in_fov(player, current_map)):
            self.switch_state('HISS', sound_manager)
            
        if self.state == 'HISS':
            self.update_hiss(player, current_map, dt)

        if self.state == 'COMPUTE_CHASE':
            self.update_compute_chase(player, current_map, dt)

        if self.state == 'CHASE':
            self.update_chase(player, current_map, dt)

        if self.state == 'COMPUTE_PATROL':
            self.update_compute_patrol(current_map, dt)

        if self.state == 'PATROL':
            self.update_patrol(current_map, dt)

        if self.state == 'COMPUTE_SEARCH':
            self.update_compute_search(current_map, dt)
        
        if self.state == 'SEARCH':
            self.update_search(current_map, dt)

        if self.state == 'LOOK_AROUND':
            self.update_look_around()

        if self.state == 'RUSH':
            self.update_rush(player, current_map, dt)

        if self.state == 'COMPUTE_VENT_PATROL':
            self.update_compute_vent_patrol(current_map, dt)

        if self.state == 'VENT_PATROL':
            self.update_vent_patrol(current_map, dt)

        if self.state == 'ENTER_VENT':
            self.update_enter_vent(sound_manager)

        if self.state == 'COMPUTE_NEAREST_VENT_ENTRY':
            self.update_compute_nearest_vent_entry(current_map, dt)

        if self.state == 'GO_TO_NEAREST_VENT_ENTRY':
            self.update_go_to_nearest_vent_entry(current_map, dt)

        if self.state == 'EXIT_VENT':
            self.update_exit_vent(sound_manager)

        if self.state == 'COMPUTE_NEAREST_VENT_EXIT':
            self.update_compute_nearest_vent_exit(current_map, dt)

        if self.state == 'GO_TO_NEAREST_VENT_EXIT':
            self.update_go_to_nearest_vent_exit(current_map, dt)

        if self.state == 'KILL':
            self.update_kill(player, current_map, dt)

        # SOUND LOGIC
        
        if (abs(self.x_pos - old_x) > 0.5 or abs(self.y_pos - old_y) > 0.5):
            attenuation = 90 * (euclidian_distance_entities(self, player) + 1e-6)**-1
            
            if self.current_speed >= self.sprint_speed:
                delay = self.run_step_delay
                sfx_name = 'alien_step'
            elif self.current_speed == self.base_speed:
                delay = self.walk_step_delay
                sfx_name = 'alien_step'
            else:
                return # Not moving
            
            if current_time - self.last_step_time > delay:
                sound_manager.play_sfx(sfx_name, attenuation)
                self.last_step_time = current_time


        # additional states to implement : 'SEARCH' after unsuccessful chase, 'ROAM' which is a patrol but picks random close points, 'VENT', 'KILL', 'STANDBY'
        # also, 'CHASE' currently follows the player, but when losing LoS, should go to last seen position or slightly after