import sys, pygame
from entities import Player, Enemy
from environment import Map
from utilities import debug

pygame.init()
screen = pygame.display.set_mode((1024, 1024))
pygame.display.set_caption("Stalker")
clock = pygame.time.Clock()
running = True

current_map_name = "map0"
current_map = Map(current_map_name)
screen = pygame.display.set_mode(current_map.size)

player = Player(current_map.player_spawn)

enemy = Enemy(current_map.enemy_spawn)


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    dt = clock.get_time()/1000 # time elapsed since last frame

    is_pressed = pygame.key.get_pressed()
    player.update(is_pressed, current_map, dt)
    enemy.update(player, current_map, dt)

    screen.blit(current_map.background, (0, 0))

    debug.draw_mesh(screen, current_map, player, enemy, dt)

    pygame.mouse.set_visible(False)

    screen.blit(player.texture, player.rect.topleft)
    screen.blit(enemy.texture, enemy.rect.topleft)
    screen.blit(player.crosshair_texture, player.crosshair_rect.topleft)
    
    light_surface = pygame.Surface(current_map.size, pygame.SRCALPHA)
    light_surface.fill((0, 0, 0)) # Black color
    light_surface.set_colorkey((0, 0, 0))
    for triangle in player.cast_rays(player.mouse_angle, player.fov_angle, current_map):
        pygame.draw.polygon(light_surface, (255, 255, 255, 100), triangle)
        
    fog_surface = pygame.Surface(current_map.size)
    fog_surface.fill((0, 0, 0)) # Black color
    fog_surface.set_alpha(255)
    fog_surface.blit(light_surface, (0, 0),  special_flags=pygame.BLEND_RGBA_SUB)
    fog_surface.set_alpha(225)
    screen.blit(fog_surface, (0, 0))

    screen.blit(light_surface, (0, 0))
    
    
    pygame.display.flip()
    

    clock.tick(60)