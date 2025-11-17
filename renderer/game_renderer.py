import pygame


class GameRenderer():
    def __init__(self, screen, current_map):
        self.screen = screen
        self.map = current_map
        self.dark_mode = False
        self.debug_mode = False

    def render_dark_mode(self, player, alien):
        light_surface = pygame.Surface(self.map.size, pygame.SRCALPHA)
        light_surface.fill((0, 0, 0)) # Black color
        light_surface.set_colorkey((0, 0, 0))
        for triangle in player.cast_rays(player.orientation, player.fov, self.map):
            pygame.draw.polygon(light_surface, (255, 255, 255, 90), triangle)
            
        fog_surface = pygame.Surface(self.map.size)
        fog_surface.fill((0, 0, 0)) # Black color
        fog_surface.set_alpha(255)
        fog_surface.blit(light_surface, (0, 0),  special_flags=pygame.BLEND_RGBA_SUB)
        fog_surface.set_alpha(200)
        self.screen.blit(fog_surface, (0, 0))

        self.screen.blit(light_surface, (0, 0))

    def render_fov(self, player):
        right_ray, left_ray = player.fov_rays(self.map)
        player_pos = player.x_pos, player.y_pos

        pygame.draw.aaline(self.screen, (150,150,150), player_pos, right_ray)
        pygame.draw.aaline(self.screen, (150,150,150), player_pos, left_ray)


    def render_game(self, player, alien, dt):
        self.screen.blit(self.map.background, (0, 0))

        pygame.mouse.set_visible(False)

        self.screen.blit(player.texture, player.rect.topleft)
        self.screen.blit(player.crosshair_texture, player.crosshair_rect.topleft)
        if player.in_fov_entity(alien, self.map):
            self.screen.blit(alien.texture, alien.rect.topleft)
        if player.motion_tracker.detects_alien:
            self.screen.blit(player.motion_tracker.texture, player.motion_tracker.rect)
        
        if self.dark_mode:
            self.render_dark_mode(player, alien)

        else:
            self.render_fov(player)

        if self.debug_mode:
            self.draw_debug(player, alien, dt)

    def draw_debug(self, player, alien, dt):
        # Draw walls
        font = pygame.font.Font(None, 40)
        current_map = self.map
        screen = self.screen
        for w in current_map.walls:
            pygame.draw.rect(screen, (255, 0, 0), w)

        # Draw mesh grid
        mesh_width, mesh_height = current_map.nav_mesh.width, current_map.nav_mesh.height
        density = current_map.nav_mesh.density
        for i in range(mesh_width):
            for j in range(mesh_height):
                eps = current_map.nav_mesh.edge_tolerance
                r = pygame.Rect(i * density, j * density, density, density)
                r_inf = pygame.Rect(i * density-eps, j * density-eps, density+2*eps, density+2*eps)
                # Check collision
                collides = r_inf.collidelist(current_map.walls) != -1
                color = (255, 50, 50) if collides else (50, 255, 50)
                pygame.draw.rect(screen, color, r, 1)

        path = alien.current_path
        if path:
            for k in range(len(path) - 1):
                p1 = path[k]
                p2 = path[k + 1]
                pygame.draw.line(
                    screen,
                    (0, 150, 255),
                    (p1[0], p1[1]),
                    (p2[0], p2[1]),
                    3
                )

        state = alien.state
        state_surface = font.render(state, True, (255, 0, 0))
        screen.blit(state_surface, (1700, 1040))


        if self.dark_mode:
            # Debug: highlight triangle corners in cyan
            for triangle in player.cast_rays(player.mouse_angle, player.fov_angle, current_map):
                for vertex in triangle:  # triangle is (pos, corner1, corner2)
                    pygame.draw.circle(screen, (0, 255, 255), (int(vertex[0]), int(vertex[1])), 3)


        if dt != 0:
            fps = str(int(1/dt))
            fps_surface = font.render(fps, True, (0, 255, 0))
            screen.blit(fps_surface, (0, 0))

