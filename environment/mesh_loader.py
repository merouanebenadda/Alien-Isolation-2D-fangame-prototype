import pygame
from math import sqrt
from utilities.mesh import NavMesh, VentMesh


def generate(size, walls, density, edge_tolerance):
    map_width, map_height = size

    mesh_width = map_width//density
    mesh_height = map_height//density

    mesh_size = mesh_width*mesh_height

    mesh = NavMesh(mesh_size, mesh_width, mesh_height, density, edge_tolerance)
    mesh.adjacency_map = {(i, j): [] for i in range(mesh_width) for j in range(mesh_height)}

    for i in range(mesh_width):
        for j in range(mesh_height):
            current_rect = mesh.rect(i, j)
            
            if mesh.rect(i, j, 0).collidelist(walls) != -1:
                mesh.adjacency_map[(i, j)] = None
                continue

            if current_rect.collidelist(walls) != -1:
                continue
            
            # Cardinal directions (weight = 1)
            
            if i > 0 and mesh.rect(i-1, j).collidelist(walls) == -1:
                mesh.adjacency_map[(i, j)].append(((i-1, j), 1))
            if i < mesh_width-1 and mesh.rect(i+1, j).collidelist(walls) == -1:
                mesh.adjacency_map[(i, j)].append(((i+1, j), 1))
            if j > 0 and mesh.rect(i, j-1).collidelist(walls) == -1:
                mesh.adjacency_map[(i, j)].append(((i, j-1), 1))
            if j < mesh_height-1 and mesh.rect(i, j+1).collidelist(walls) == -1:
                mesh.adjacency_map[(i, j)].append(((i, j+1), 1))
            
            # Diagonals (weight = sqrt(2))
            # 1. UP-LEFT
            if (i > 0 and j > 0 and 
                mesh.rect(i-1, j-1).collidelist(walls) == -1 and  # Destination clear
                mesh.rect(i-1, j).collidelist(walls) == -1 and   # Corner 1 (Left) clear
                mesh.rect(i, j-1).collidelist(walls) == -1):     # Corner 2 (Up) clear
                    
                mesh.adjacency_map[(i, j)].append(((i-1, j-1), sqrt(2)))
            # 2. UP-RIGHT
            if (i < mesh_width-1 and j > 0 and 
                mesh.rect(i+1, j-1).collidelist(walls) == -1 and  # Destination clear
                mesh.rect(i+1, j).collidelist(walls) == -1 and   # Corner 1 (Right) clear
                mesh.rect(i, j-1).collidelist(walls) == -1):     # Corner 2 (Up) clear
                    
                mesh.adjacency_map[(i, j)].append(((i+1, j-1), sqrt(2)))
            # 3. DOWN-LEFT
            if (i > 0 and j < mesh_height-1 and 
                mesh.rect(i-1, j+1).collidelist(walls) == -1 and  # Destination clear
                mesh.rect(i-1, j).collidelist(walls) == -1 and   # Corner 1 (Left) clear
                mesh.rect(i, j+1).collidelist(walls) == -1):     # Corner 2 (Down) clear
                    
                mesh.adjacency_map[(i, j)].append(((i-1, j+1), sqrt(2)))
            # 4. DOWN-RIGHT
            if (i < mesh_width-1 and j < mesh_height-1 and 
                mesh.rect(i+1, j+1).collidelist(walls) == -1 and  # Destination clear
                mesh.rect(i+1, j).collidelist(walls) == -1 and   # Corner 1 (Right) clear
                mesh.rect(i, j+1).collidelist(walls) == -1):     # Corner 2 (Down) clear
                    
                mesh.adjacency_map[(i, j)].append(((i+1, j+1), sqrt(2)))

    return mesh