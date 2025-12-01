import pygame

class Director():
    def __init__(self, player_instance, alien_instance, current_map):
        self.player = player_instance
        self.alien = alien_instance
        self.current_map = current_map

        self.in_frontstage_timer = 0
        self.in_backstage_timer = 0
        self.in_backstage_duration = 30000
        self.aggression_level = 0  # Ranges from 0 to 100
        self.current_order = None

        self.vent_entry_threshold = 10 # Aggression level to enter vents
        self.vent_exit_threshold = 50  # Aggression level to exit vents

        self.hint_cooldown = 90000  # Time between hints in milliseconds
        self.last_hint_time = 0

        self.player_hint_range = (50, 250)  # Range for hint positions

    def update_aggression_level(self, now):
        if self.alien.is_in_frontstage:
            if not self.alien.entity_in_fov(self.player, self.current_map):
                self.aggression_level = max(0, self.aggression_level - 0.01)
            if self.alien.entity_in_fov(self.player, self.current_map):
                self.aggression_level = 100

        else:
            self.aggression_level = min(100, self.aggression_level + 0.02)

    def update(self):
        now = pygame.time.get_ticks()

        self.update_aggression_level(now)

        if self.current_order == "ENTER_BACKSTAGE" and not self.alien.is_in_frontstage:
            self.current_order = None
        
        elif self.current_order == "EXIT_BACKSTAGE" and self.alien.is_in_frontstage:
            self.current_order = None

        if self.alien.is_in_frontstage and self.current_order != "ENTER_BACKSTAGE":
            if self.aggression_level < self.vent_entry_threshold:
                self.current_order = "ENTER_BACKSTAGE"
                self.alien.switch_state('COMPUTE_NEAREST_VENT_ENTRY')
            elif now - self.last_hint_time > self.hint_cooldown and self.alien.state == 'PATROL':
                self.last_hint_time = now
                random_hint_position = self.current_map.nav_mesh.random_tile(self.player, self.player_hint_range)
                self.alien.switch_state('COMPUTE_PATROL', objective= random_hint_position)

        elif self.current_order != "EXIT_BACKSTAGE" and self.aggression_level > self.vent_exit_threshold:
            self.current_order = "EXIT_BACKSTAGE"
            self.alien.switch_state('COMPUTE_NEAREST_VENT_EXIT')