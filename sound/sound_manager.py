import pygame

class SoundManager():
    def __init__(self):
        self.current_music = None

    def play_music(self, music):
        self.music = pygame.mixer.music.load(f'assets/audio/music/{music}.mp3')
        pygame.mixer.music.play(loops=-1)

    def stop_music(self):
        pygame.mixer.music.stop()