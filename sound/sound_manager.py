import os, pygame

class SoundManager():
    def __init__(self):
        self.current_music = None
        self.mute = True
        self.sfx = {}
        self.init_player_sfx()
        self.init_alien_sfx()

    def init_player_sfx(self):
        # Define the base path where the sound files are located
        # Adjust 'assets/audio/sfx/player' based on your actual structure
        SFX_DIR = os.path.join('assets', 'audio', 'sfx', 'player')
        
        # Ensure the directory exists before proceeding
        if not os.path.isdir(SFX_DIR):
            print(f"Error: Sound directory not found at {SFX_DIR}")
            return

        # Iterate through every file in the directory
        for filename in os.listdir(SFX_DIR):
            # Check if the file is an audio file (e.g., .wav, .ogg, .mp3)
            if filename.lower().endswith(('.wav', '.ogg', '.mp3')):
                
                # 1. Create the full file path
                full_path = os.path.join(SFX_DIR, filename)
                
                # 2. Get the sound name without the extension (e.g., 'footstep_walk')
                sound_name = os.path.splitext(filename)[0]
                
                # 3. Load the sound using your existing SoundManager method (self.load_sfx)
                # You'll need to define self.sfx in your __init__
                if not hasattr(self, 'sfx'):
                    self.sfx = {} # Initialize cache if not done in __init__
                    
                self.sfx[sound_name] = pygame.mixer.Sound(full_path)
                print(f"Loaded SFX: {sound_name}")

    def init_alien_sfx(self):
        # Define the base path where the sound files are located
        # Adjust 'assets/audio/sfx/player' based on your actual structure
        SFX_DIR = os.path.join('assets', 'audio', 'sfx', 'alien')
        
        # Ensure the directory exists before proceeding
        if not os.path.isdir(SFX_DIR):
            print(f"Error: Sound directory not found at {SFX_DIR}")
            return

        # Iterate through every file in the directory
        for filename in os.listdir(SFX_DIR):
            # Check if the file is an audio file (e.g., .wav, .ogg, .mp3)
            if filename.lower().endswith(('.wav', '.ogg', '.mp3')):
                
                # 1. Create the full file path
                full_path = os.path.join(SFX_DIR, filename)
                
                # 2. Get the sound name without the extension (e.g., 'footstep_walk')
                sound_name = os.path.splitext(filename)[0]
                
                # 3. Load the sound using your existing SoundManager method (self.load_sfx)
                # You'll need to define self.sfx in your __init__
                if not hasattr(self, 'sfx'):
                    self.sfx = {} # Initialize cache if not done in __init__
                    
                self.sfx[sound_name] = pygame.mixer.Sound(full_path)
                print(f"Loaded SFX: {sound_name}")


    def play_music(self, music):
        self.current_music = pygame.mixer.music.load(f'assets/audio/music/{music}.mp3')
        pygame.mixer.music.play(loops=-1)

    def stop_music(self):
        pygame.mixer.music.stop()

    def stop_all_audio(self):
        self.stop_music()
        pygame.mixer.stop()

    def pause_all_audio(self):
        pygame.mixer.music.pause() 
        pygame.mixer.pause() 

    def resume_all_audio(self):
        pygame.mixer.music.unpause() 
        pygame.mixer.unpause()

    def play_sfx(self, sfx_name, volume=1.0):
        if self.mute:
            return
        if sfx_name in self.sfx:
            sound = self.sfx[sfx_name]
            sound.set_volume(volume)
            sound.play()

