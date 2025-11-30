import sys, pygame
import gc
from entities import Player, Alien, Director
from environment import Map
from renderer import GameRenderer, MenuRenderer
from sound import SoundManager
import pickle

pygame.init()
resolution = (1920, 1080)
screen = pygame.display.set_mode(resolution, flags = pygame.FULLSCREEN)
pygame.display.set_caption("Alien : Isolation 2D (Fan Game)")
clock = pygame.time.Clock()
running = True
game_state = "MAIN_MENU"

sound_manager = SoundManager()

def initialize_new_game(screen):
    sound_manager.stop_music()
    current_map_name = "map4"
    map_path = f'maps/{current_map_name}/map.pkl'
    with open(map_path, 'rb') as f:
        current_map = pickle.load(f)

    current_map.load()

    renderer = GameRenderer(screen, current_map)

    player = Player(current_map.player_spawn)

    enemy = Alien(current_map.enemy_spawn)

    director = Director()

    return current_map, renderer, player, enemy, director

def initialize_main_menu():
    global game_state, renderer, screen, sound_manager

    sound_manager.stop_all_audio()

    renderer = MenuRenderer(screen)
    sound_manager.play_music("main_menu")
    game_state = 'MAIN_MENU'

def cleanup_game_objects():
    """Clears references to the heavy game objects."""
    global current_map, renderer, player, enemy, director
    
    current_map = None
    player = None
    enemy = None
    director = None
    
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
                current_map, renderer, player, alien, director = initialize_new_game(screen)

            if event.key == pygame.K_m:
                if sound_manager.mute:
                    sound_manager.resume_all_audio()
                else:
                    sound_manager.pause_all_audio()
                sound_manager.mute = not sound_manager.mute
                

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

        player.update(is_pressed, renderer.get_absolute_position(pygame.mouse.get_pos()), alien, current_map, sound_manager, dt)
        alien.update(player, current_map, sound_manager, dt)
        director.update(player, alien)

        renderer.render_game(player, alien, dt)

    
    pygame.display.flip()
    

    clock.tick(60)