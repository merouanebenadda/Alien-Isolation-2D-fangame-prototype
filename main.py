import sys, pygame
import gc
from entities import Player, Enemy
from environment import Map
from renderer import GameRenderer, MenuRenderer
from sound import SoundManager

pygame.init()
resolution = (1920, 1080)
screen = pygame.display.set_mode(resolution, flags = pygame.FULLSCREEN)
pygame.display.set_caption("Stalker")
clock = pygame.time.Clock()
running = True
game_state = "MAIN_MENU"

sound_manager = SoundManager()

# current_map_name = "map0"
# current_map = Map(current_map_name)
# screen = pygame.display.set_mode(current_map.size)

# renderer = Renderer(screen, current_map)

# player = Player(current_map.player_spawn)

# enemy = Enemy(current_map.enemy_spawn)

def initialize_new_game(screen):
    sound_manager.stop_music()
    current_map_name = "map0"
    current_map = Map(current_map_name, screen)

    renderer = GameRenderer(screen, current_map)

    player = Player(current_map.player_spawn)

    enemy = Enemy(current_map.enemy_spawn)

    return current_map, renderer, player, enemy

def initialize_main_menu():
    global game_state, renderer, screen

    renderer = MenuRenderer(screen)
    sound_manager.play_music("main_menu")
    game_state = 'MAIN_MENU'

def cleanup_game_objects():
    """Clears references to the heavy game objects."""
    global current_map, renderer, player, enemy
    
    current_map = None
    player = None
    enemy = None
    
    renderer = None 
    
    gc.collect()

initialize_main_menu()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                game_state = "GAME_RUNNING"
                current_map, renderer, player, enemy = initialize_new_game(screen)
                

            if game_state == 'GAME_RUNNING':
                if event.key == pygame.K_f:
                    renderer.dark_mode = not renderer.dark_mode
                if event.key == pygame.K_v:
                    renderer.debug_mode = not renderer.debug_mode
                if event.key == pygame.K_ESCAPE:
                    cleanup_game_objects()
                    initialize_main_menu()

            elif game_state == 'MAIN_MENU':
                if event.key == pygame.K_ESCAPE:
                    running = False


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