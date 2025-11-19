import os, pygame

class SoundManager():
    def __init__(self):
        self.current_music = None
        self.mute = False
        self.sfx = {}
        self.init_sfx()

    def init_sfx(self):
        # Define the base path for all SFX files (e.g., assets/audio/sfx)
        SFX_BASE_DIR = os.path.join('assets', 'audio', 'sfx')
        
        if not os.path.isdir(SFX_BASE_DIR):
            print(f"Error: Base sound directory not found at {SFX_BASE_DIR}")
            return

        # os.walk traverses the entire directory tree (root, dirs, files)
        for root, dirs, files in os.walk(SFX_BASE_DIR):
            
            # 'files' is a list of file names in the current 'root' directory
            for filename in files:
                
                # Check if the file is an audio file
                if filename.lower().endswith(('.wav', '.ogg', '.mp3')):
                    
                    # 1. Create the full file path (e.g., assets/audio/sfx/alien/hiss.wav)
                    full_path = os.path.join(root, filename)
                    
                    # 2. Get the sound name without the extension (e.g., 'hiss')
                    sound_name = os.path.splitext(filename)[0]
                    
                    # 3. Load and cache the sound
                    # NOTE: Since the names might repeat (e.g., 'step' in player and alien folders),
                    # you might want to prepend the folder name for uniqueness:
                    # sound_name = os.path.basename(root) + '_' + sound_name
                    
                    try:
                        self.sfx[sound_name] = pygame.mixer.Sound(full_path)
                        print(f"Loaded SFX: {sound_name}")
                    except pygame.error as e:
                        print(f"Failed to load {filename}: {e}")


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

