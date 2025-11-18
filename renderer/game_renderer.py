import pygame
from .game_camera import GameCamera


class GameRenderer():
    def __init__(self, screen, current_map):
        self.screen = screen
        self.map = current_map
        self.dark_mode = False
        self.debug_mode = False
        self.camera = GameCamera()

    # To be updated
    # def render_dark_mode(self, player, alien):
    #     light_surface = pygame.Surface(self.map.size, pygame.SRCALPHA)
    #     light_surface.fill((0, 0, 0)) # Black color
    #     light_surface.set_colorkey((0, 0, 0))
    #     for triangle in player.cast_rays(player.look_orientation, player.fov, self.map):
    #         pygame.draw.polygon(light_surface, (255, 255, 255, 90), triangle)
            
    #     fog_surface = pygame.Surface(self.map.size)
    #     fog_surface.fill((0, 0, 0)) # Black color
    #     fog_surface.set_alpha(255)
    #     fog_surface.blit(light_surface, (0, 0),  special_flags=pygame.BLEND_RGBA_SUB)
    #     fog_surface.set_alpha(200)
    #     self.screen.blit(fog_surface, (0, 0))

    #     self.screen.blit(light_surface, (0, 0))

    def get_absolute_position(self, x, y=None):
        if y == None:
            x, y = x

        return x + self.camera.offset_x, y + self.camera.offset_y

    def get_screen_position(self, x, y=None):
        """
        Returns the screen position of a given set of absolute coordinates
        """

        if y == None:
            x, y = x

        return x-self.camera.offset_x, y-self.camera.offset_y

    def get_screen_position_entity(self, entity):
        """
        This method takes absolute coordinates and translates them into screen coordinates or returns None if position is off_screen
        """
        render_pos_x, render_pos_y = entity.x_pos, entity.y_pos
        render_pos_x, render_pos_y = render_pos_x-self.camera.offset_x, render_pos_y-self.camera.offset_y

        return render_pos_x, render_pos_y



    def render_fov(self, entity):
        right_ray, left_ray = tuple(map(self.get_screen_position, entity.fov_rays(self.map)))
        entity_pos = self.get_screen_position_entity(entity)

        pygame.draw.aaline(self.screen, (150,150,150), entity_pos, right_ray)
        pygame.draw.aaline(self.screen, (150,150,150), entity_pos, left_ray)


    def render_game(self, player, alien, dt):
        font = pygame.font.Font(None, 40)
        self.screen.fill((0, 0, 0))
        self.camera.target_entity = player

        pygame.mouse.set_visible(False)

        if self.debug_mode:
            self.render_debug(player, alien, dt)

        self.camera.update()

        self.render_walls()
        self.render_player(player)
        self.render_crosshair(player)
        self.render_fov(player)

        if player.entity_in_fov(alien, self.map):
            self.render_entity(alien)
            self.render_fov(alien)

        if player.motion_tracker.detects_alien:
            self.screen.blit(player.motion_tracker.texture, player.motion_tracker.rect)

        if self.debug_mode:
            self.render_entity(alien)
            self.render_fov(alien)

        if dt != 0:
            fps = str(int(1/dt))
            fps_surface = font.render(fps, True, (0, 255, 0))
            self.screen.blit(fps_surface, (0, 0))

    def render_walls(self):
        for wall in self.map.walls:
            if wall.rect.colliderect(self.camera.rect):
                x, y = wall.rect.topleft
                width, height = wall.rect.width, wall.rect.height
                wall_rect = pygame.Rect(x-self.camera.offset_x, y-self.camera.offset_y, width, height)
                pygame.draw.rect(self.screen, (255, 0, 0), wall_rect)

    def render_player(self, player):
        render_pos_x, render_pos_y = self.camera.resolution
        sx, sy = player.size
        render_pos_x, render_pos_y = render_pos_x/2-sx/2, render_pos_y/2-sy/2
        self.screen.blit(player.texture, (render_pos_x, render_pos_y))

    def render_crosshair(self, player):
        render_pos_x, render_pos_y = player.crosshair_x_pos, player.crosshair_y_pos
        sx, sy = player.crosshair_size
        render_pos_x, render_pos_y = render_pos_x-self.camera.offset_x - sx/2, render_pos_y-self.camera.offset_y - sy/2
        self.screen.blit(player.crosshair_texture, (render_pos_x, render_pos_y))

    def render_entity(self, entity):
        render_pos_x, render_pos_y = entity.x_pos, entity.y_pos
        sx, sy = entity.size
        render_pos_x, render_pos_y = render_pos_x-self.camera.offset_x - sx/2, render_pos_y-self.camera.offset_y - sy/2
        self.screen.blit(entity.texture, (render_pos_x, render_pos_y))

    def render_debug(self, player, alien, dt):
        # Draw walls
        font = pygame.font.Font(None, 40)
        current_map = self.map
        screen = self.screen
        self.render_walls()

        # Draw mesh grid
        mesh_width, mesh_height = current_map.nav_mesh.width, current_map.nav_mesh.height
        density = current_map.nav_mesh.density
        for i in range(mesh_width):
            for j in range(mesh_height):
                eps = current_map.nav_mesh.edge_tolerance
                r = pygame.Rect(i * density, j * density, density, density)
                x_screen, y_screen = self.get_screen_position(i * density, j * density)
                r_screen = pygame.Rect(x_screen, y_screen, density, density)
                r_inf = pygame.Rect(i * density-eps, j * density-eps, density+2*eps, density+2*eps)
                # Check collision
                collides = r_inf.collidelist(current_map.walls) != -1
                color = (255, 50, 50) if collides else (50, 255, 50)
                pygame.draw.rect(screen, color, r_screen, 1)

        path = alien.current_path
        if path:
            for k in range(len(path) - 1):
                p1 = path[k]
                p2 = path[k + 1]
                pygame.draw.line(
                    screen,
                    (0, 150, 255),
                    self.get_screen_position(p1[0], p1[1]),
                    self.get_screen_position(p2[0], p2[1]),
                    3
                )

        state = alien.state
        state_surface = font.render(state, True, (255, 0, 0))
        screen.blit(state_surface, (1700, 1040))

        # To be updated
        # if self.dark_mode:
        #     # Debug: highlight triangle corners in cyan
        #     for triangle in player.cast_rays(player.look_orientation, player.fov, current_map):
        #         for vertex in triangle:  # triangle is (pos, corner1, corner2)
        #             pygame.draw.circle(screen, (0, 255, 255), (int(vertex[0]), int(vertex[1])), 3)



