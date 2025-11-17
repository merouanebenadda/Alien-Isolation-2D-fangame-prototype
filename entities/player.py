from .entity import Entity
from items import MotionTracker
from numpy import arctan2
import pygame
import math


class Player(Entity):
    def __init__(self, x, y=None):
        if y == None: x, y = x
        super().__init__(x, y)
        self.MAX_STAMINA = 300
        self.base_speed = 2
        self.sprint_speed = 5
        self.current_speed = self.base_speed
        self.stamina = self.MAX_STAMINA
        self.is_alive = True
        

        PLAYER_SIZE = (25, 25)
        player_surface = pygame.image.load('assets/textures/player/blue_dot.png').convert_alpha()
        self.texture = pygame.transform.scale(player_surface, PLAYER_SIZE)
        self.rect = self.texture.get_rect()
        self.rect.center = (x, y)

        CROSSHAIR_SIZE = (7, 7)
        self.crosshair_x_pos = x
        self.crosshair_y_pos = y
        crosshair_surface = pygame.image.load('assets/textures/player/crosshair.png')
        self.crosshair_texture = pygame.transform.scale(crosshair_surface, CROSSHAIR_SIZE)
        self.crosshair_rect = self.crosshair_texture.get_rect()
        self.crosshair_rect.center = (x, y)

        self.orientation = 0
        self.fov = 90

        self.motion_tracker = MotionTracker()
        self.motion_tracker_out = False

        # Audio logic

        self.is_walking = False
        self.is_running = False


        self.last_step_time = 0
        self.walk_step_delay = 700
        self.run_step_delay = 400


        

    def update(self, is_pressed, alien, current_map, sound_manager, dt):
        now = pygame.time.get_ticks()

        old_x = self.x_pos
        old_y = self.y_pos

        movement_vector_x= 0
        movement_vector_y= 0

        self.current_speed = self.base_speed

        self.is_walking = False
        self.is_running = False

        mouse_pos =  pygame.mouse.get_pos()
        self.crosshair_x_pos, self.crosshair_y_pos = mouse_pos
        self.crosshair_rect.center = mouse_pos

        x_m, y_m = mouse_pos
        x, y = self.x_pos, self.y_pos

        self.orientation = (arctan2(y_m-y, x_m-x)*180/math.pi)%360 # in [0, 360)

        self.motion_tracker.update(self, alien, current_map, sound_manager)


        if not self.is_alive:
            return

        if is_pressed[pygame.K_LSHIFT]:# and self.stamina > 0:
            self.current_speed = self.sprint_speed
            self.stamina = max(self.stamina - 3, 0)

        if not is_pressed[pygame.K_LSHIFT] and self.stamina < self.MAX_STAMINA:
            self.stamina = min(self.stamina + 1, 300)

        if is_pressed[pygame.K_UP] or is_pressed[pygame.K_z]:
            movement_vector_y -= self.current_speed
        
        if is_pressed[pygame.K_DOWN] or is_pressed[pygame.K_s]:
            movement_vector_y += self.current_speed
        
        if is_pressed[pygame.K_RIGHT] or is_pressed[pygame.K_d]:
            movement_vector_x += self.current_speed
        
        if is_pressed[pygame.K_LEFT] or is_pressed[pygame.K_q]:
            movement_vector_x -= self.current_speed
            
        norm = math.sqrt(movement_vector_x**2 + movement_vector_y**2)

        if norm != 0:
            self.is_running = self.current_speed == self.sprint_speed
            self.is_walking = self.current_speed == self.base_speed
            if self.is_walking and now-self.last_step_time > self.walk_step_delay:
                self.last_step_time = now
                sound_manager.play_sfx('step')
            elif self.is_running and now-self.last_step_time > self.run_step_delay:
                self.last_step_time = now
                sound_manager.play_sfx('step')
            super().move(movement_vector_x, movement_vector_y, norm, old_x, old_y, current_map, dt)