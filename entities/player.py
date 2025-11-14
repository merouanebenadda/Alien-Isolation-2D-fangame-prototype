from .entity import Entity
import pygame
import math

class Player(Entity):
    def __init__(self, x, y=None):
        if y == None: x, y = x
        super().__init__(x, y)
        self.MAX_STAMINA = 300
        self.base_speed = 2
        self.sprint_speed = 4
        self.current_speed = self.base_speed
        self.stamina = self.MAX_STAMINA
        

        PLAYER_SIZE = (25, 25)
        player_surface = pygame.image.load('textures/player/blue_dot.png').convert_alpha()
        self.texture = pygame.transform.scale(player_surface, PLAYER_SIZE)
        self.rect = self.texture.get_rect()
        self.rect.center = (x, y)

    def move(self, is_pressed, current_map, dt):
        old_x = self.x_pos
        old_y = self.y_pos

        movement_vector_x= 0
        movement_vector_y= 0

        self.current_speed = self.base_speed

        if is_pressed[pygame.K_LSHIFT] and self.stamina > 0:
            self.current_speed = self.sprint_speed
            self.stamina = max(self.stamina - 3, 0)

        if not is_pressed[pygame.K_LSHIFT] and self.stamina < self.MAX_STAMINA:
            self.stamina = min(self.stamina + 1, 300)

        if is_pressed[pygame.K_UP]:
            movement_vector_y -= self.current_speed
        
        if is_pressed[pygame.K_DOWN]:
            movement_vector_y += self.current_speed
        
        if is_pressed[pygame.K_RIGHT]:
            movement_vector_x += self.current_speed
        
        if is_pressed[pygame.K_LEFT]:
            movement_vector_x -= self.current_speed
            
        norm = math.sqrt(movement_vector_x**2 + movement_vector_y**2)

        if norm != 0:
            super().move(movement_vector_x, movement_vector_y, norm, old_x, old_y, current_map, dt)