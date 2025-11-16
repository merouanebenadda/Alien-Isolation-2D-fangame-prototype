import pygame

class MenuRenderer():
    def __init__(self, screen):
        self.screen = screen
        self.size = 1920, 1080
        background = pygame.image.load('textures/main_menu/main_menu.jpeg')
        self.background = pygame.transform.scale(background, self.size)



    def render_menu(self):
        """Draws the main menu screen."""
        self.screen.blit(self.background, (0, 0))
        
        # Draw Title
        font = pygame.font.Font(None, 72)
        title_surface = font.render("STALKER", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.size[0] // 2, 200))
        self.screen.blit(title_surface, title_rect)

        # Draw Start Instructions
        font_small = pygame.font.Font(None, 36)
        start_surface = font_small.render("Press ENTER to Start", True, (180, 180, 180))
        start_rect = start_surface.get_rect(center=(self.size[0] // 2, self.size[1] - 100))
        self.screen.blit(start_surface, start_rect)