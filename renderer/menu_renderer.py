import pygame
from numpy import sin

class MenuRenderer():
    def __init__(self, screen):
        self.screen = screen
        self.size = 1920, 1080
        background = pygame.image.load('textures/main_menu/main_menu.jpeg')
        self.background = pygame.transform.scale(background, self.size)



    def render_menu(self):
        now = pygame.time.get_ticks()
        BLINK_SPEED = 0.003
        """Draws the main menu screen."""
        self.screen.blit(self.background, (0, 0))
        
        # Draw Title
        font = pygame.font.Font(None, 72)
        title_surface = font.render("Alien : Isolation 2D (Fangame)", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.size[0] *3/4, 200))
        self.screen.blit(title_surface, title_rect)

        # Draw Start Instructions
        font_small = pygame.font.Font(None, 36)
        blink_delta = 50*sin(now*BLINK_SPEED)
        color = (180+blink_delta, 180+blink_delta, 180+blink_delta)
        start_surface = font_small.render("Press ENTER to Start", True, color)
        start_rect = start_surface.get_rect(center=(self.size[0] // 2, self.size[1] - 100))
        self.screen.blit(start_surface, start_rect)