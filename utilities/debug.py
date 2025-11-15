import pygame

def draw_mesh(screen, current_map, player, enemy, dt):
    # Draw walls
    font = pygame.font.Font(None, 40)
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

    path = enemy.current_path
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

    # Debug: highlight triangle corners in cyan
    for triangle in player.cast_rays(player.mouse_angle, player.fov_angle, current_map):
        for vertex in triangle:  # triangle is (pos, corner1, corner2)
            pygame.draw.circle(screen, (0, 255, 255), (int(vertex[0]), int(vertex[1])), 3)


    if dt != 0:
        fps = str(int(1/dt))
        fps_surface = font.render(fps, True, (0, 255, 0))
        screen.blit(fps_surface, (0, 0))