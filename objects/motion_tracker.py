import pygame

class MotionTracker():
    def __init__(self):
        self.min_range = 0
        self.max_range = 200
        self.texture = pygame.image.load().convert_alpha()