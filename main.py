import sys, pygame
from entities import Player, Enemy
from environment import Map
from renderer import Renderer

pygame.init()
screen = pygame.display.set_mode((1024, 1024))
pygame.display.set_caption("Stalker")
clock = pygame.time.Clock()
running = True

current_map_name = "map0"
current_map = Map(current_map_name)
screen = pygame.display.set_mode(current_map.size)

renderer = Renderer(screen, current_map)

player = Player(current_map.player_spawn)

enemy = Enemy(current_map.enemy_spawn)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                renderer.dark_mode = not renderer.dark_mode
            if event.key == pygame.K_v:
                renderer.debug_mode = not renderer.debug_mode

    dt = clock.get_time()/1000 # time elapsed since last frame

    
    is_pressed = pygame.key.get_pressed()

    
    player.update(is_pressed, current_map, dt)
    enemy.update(player, current_map, dt)

    
    renderer.render(player, enemy, dt)
    
    
    pygame.display.flip()
    

    clock.tick(60)