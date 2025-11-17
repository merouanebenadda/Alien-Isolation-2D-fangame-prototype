import pygame
from math import cos, sin, exp, radians
from utilities.geometry import angle, euclidian_distance_entities

class MotionTracker():
    def __init__(self):
        self.min_range = 0
        self.max_range = 750
        self.fov = 90
        
        self.TRACKER_SIZE = (320, 480)
        surface = pygame.image.load(f'assets/textures/items/motion_tracker/motion_tracker.jpg').convert_alpha()
        self.motion_tracker_background = pygame.transform.scale(surface, self.TRACKER_SIZE)

        self.DOT_SIZE = (20, 20)
        surface = pygame.image.load((f'assets/textures/items/motion_tracker/dot.png')).convert_alpha()
        self.dot_texture = pygame.transform.scale(surface, self.DOT_SIZE)
        self.dot_pos = None
        self.blink_decay = 1000
        self.blink_speed = 750
        self.last_beep_time = 0

        self.display_size = 300, 240
        self.display_pos = 10, 46


        self.texture = self.motion_tracker_background # we'll blit the dot on this

        self.detects_alien = False

        self.texture = self.motion_tracker_background.copy()
        self.rect = self.texture.get_rect()

        self.rect.bottomleft = (0, 1080)

        self.last_refresh = 0
        self.refresh_rate = 50


        


    def update(self, player, alien, current_map, sound_manager):
        now = pygame.time.get_ticks()
        if now-self.last_refresh < self.refresh_rate:
            return

        self.texture.blit(self.motion_tracker_background, (0, 0))
        self.alien_location = None

        player_pos = player.x_pos, player.y_pos
        alien_pos = alien.x_pos, alien.y_pos

        look_orientation = player.look_orientation
        alien_angle = angle(player_pos, alien_pos)

        distance = euclidian_distance_entities(player, alien)

        if self.in_fov(alien_angle, look_orientation) and distance  < self.max_range:
            if not self.detects_alien:
                self.last_beep_time = now

            delta = radians(alien_angle-look_orientation)
            self.dot_pos = (distance/self.max_range*self.display_size[0]*sin(delta) + self.TRACKER_SIZE[0]/2,
                            -distance/self.max_range*self.display_size[0]*cos(delta) + self.display_size[1] + self.display_pos[1])
            intensity = int(255*exp(-(now%self.blink_decay)/self.blink_speed))
            self.dot_texture.set_alpha(intensity)
            self.texture.blit(self.dot_texture, (self.dot_pos))
            self.detects_alien = True
            self.last_refresh = now
            if now - self.last_beep_time > self.blink_decay or intensity > 240:
                self.last_beep_time = now
                sound_manager.play_sfx('motion_tracker_beep', volume=0.1)
            # self.blink_interval = max(50, 600*distance/self.max_range)
        else:
            self.detects_alien = False


    def in_fov(self, angle, orientation):
        eps = 0
        delta = (angle - orientation + 180) % 360 - 180
        return abs(delta) <= self.fov/2 + eps