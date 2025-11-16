import sys, pygame
from entities import Player, Enemy
from environment import Map
from renderer import GameRenderer, MenuRenderer

pygame.init()
resolution = (1920, 1080)
screen = pygame.display.set_mode(resolution, flags = pygame.FULLSCREEN)
pygame.display.set_caption("Stalker")
clock = pygame.time.Clock()
running = True
game_state = "MAIN_MENU"

renderer = MenuRenderer(screen)

# current_map_name = "map0"
# current_map = Map(current_map_name)
# screen = pygame.display.set_mode(current_map.size)

# renderer = Renderer(screen, current_map)

# player = Player(current_map.player_spawn)

# enemy = Enemy(current_map.enemy_spawn)

def initialize_new_game(screen):
    current_map_name = "map0"
    current_map = Map(current_map_name, screen)

    renderer = GameRenderer(screen, current_map)

    player = Player(current_map.player_spawn)

    enemy = Enemy(current_map.enemy_spawn)

    return current_map, renderer, player, enemy


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                game_state = "GAME_RUNNING"
                current_map, renderer, player, enemy = initialize_new_game(screen)
            if event.key == pygame.K_ESCAPE:
                running = False
            if game_state == 'GAME_RUNNING':
                if event.key == pygame.K_f:
                    renderer.dark_mode = not renderer.dark_mode
                if event.key == pygame.K_v:
                    renderer.debug_mode = not renderer.debug_mode

    dt = clock.get_time()/1000 # time elapsed since last frame

    if game_state == 'MAIN_MENU':
        renderer.render_menu()

    if game_state == 'GAME_RUNNING':
        is_pressed = pygame.key.get_pressed()

        player.update(is_pressed, current_map, dt)
        enemy.update(player, current_map, dt)
        
        renderer.render_game(player, enemy, dt)
    
    
    pygame.display.flip()
    

    clock.tick(60)