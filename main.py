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
    player.move(is_pressed, current_map, dt)
    enemy.update(player, current_map, dt)

    screen.blit(current_map.background, (0, 0))
    debug.draw_mesh(screen, current_map, enemy, dt)

    screen.blit(player.texture, player.rect.topleft)
    screen.blit(enemy.texture, enemy.rect.topleft)

    
    
    pygame.display.flip()
    

    clock.tick(60)