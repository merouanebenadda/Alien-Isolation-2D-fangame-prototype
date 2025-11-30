import pygame

class Director():
    def __init__(self):
        self.in_frontstage_timer = 0
        self.in_backstage_timer = 0
        self.in_backstage_duration = 30000
        self.aggression_level = 0  # Ranges from 0 to 100
        self.current_order = None


    def update(self, player, alien):
        now = pygame.time.get_ticks()

        if not alien.is_in_frontstage:
            if self.in_backstage_timer == 0:
                self.in_backstage_timer = now
            elif now - self.in_backstage_timer > self.in_backstage_duration and self.current_order != 'EXIT':
                self.current_order = 'EXIT'
                alien.switch_state('COMPUTE_NEAREST_VENT_EXIT')