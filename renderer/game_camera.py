import pygame

class GameCamera():
    def __init__(self):
        self.resolution = 1920, 1080

        # The offset determines the position of the top left corner of the camera on the map
        self.offset_x = 0
        self.offset_y = 0

        self.width = 1920
        self.height = 1080

        self.target_entity = None

        self.rect = pygame.rect.Rect(self.offset_x, self.offset_y, self.width, self.height)


    
    def update(self):
        x_pos, y_pos = self.target_entity.x_pos, self.target_entity.y_pos

        self.offset_x = x_pos-self.width/2
        self.offset_y = y_pos-self.height/2

        self.rect = pygame.rect.Rect(self.offset_x, self.offset_y, self.width, self.height)
