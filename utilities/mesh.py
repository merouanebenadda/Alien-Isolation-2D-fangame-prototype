from .a_star import A_star
from .geometry import euclidian_distance
import pygame
import random as rd

class Mesh():
    def __init__(self, size, width, height, density):
        self.size = size
        self.width = width
        self.height = height
        self.density = density
        self.adjacency_map = {}

    def random_tile(self, enemy, range): # /!\ has to be optimized, especially for bigger maps
        inf, sup = range
        x, y = enemy.x_pos, enemy.y_pos

        n = len(self.adjacency_map)

        keys_list = list(self.adjacency_map.keys())

        rand_i, rand_j = keys_list[rd.randint(0, n-1)]
        rand_x, rand_y = self.position(rand_i, rand_j)

        while (not inf < euclidian_distance((x, y), (rand_x, rand_y)) < sup) or not self.adjacency_map[(rand_i, rand_j)]:
            rand_i, rand_j = keys_list[rd.randint(0, n-1)]
            rand_x, rand_y = self.position(rand_i, rand_j)

        return rand_x, rand_y

    def nearest_node(self, pos):
        """
        Converts the entity's continuous pixel position (x_pos, y_pos) 
        into discrete grid coordinates (i, j).
        """
        # Calculate the grid column (i) and row (j) using integer division
        # This gives the floor of the division, which is the correct tile index.
        pos_x, pos_y = pos
        
        i = int(pos_x // self.density)
        j = int(pos_y // self.density)

        # Critical Safety: Clamp the indices to the mesh boundaries (0 to width/height - 1)
        # This prevents crashes if an entity somehow moves slightly off the map edge.
        i = max(0, min(i, self.width - 1))
        j = max(0, min(j, self.height - 1))
        
        return (i, j)
    
    def position(self, i, j):
        """
        Returns the center of the tile of indices (i, j)
        """
        density = self.density
        return (density*i + density//2, density*j + density//2)
    
    def closest_accessible_tile(self, i, j=None):
        """
        Return the nearest tile (i,j) with a non-empty adjacency list within Manhattan distance <= 2.
        Stop searching further along any direction as soon as a wall (tile with empty/no adjacency) is encountered.
        Accepts either closest_accessible_tile((i, j)) or closest_accessible_tile(i, j).
        """
        if j is None and isinstance(i, tuple):
            i, j = i

        # If the current tile is already accessible, return it.
        if self.adjacency_map.get((i, j)):
            return (i, j)

        max_dist = 3
        # 8 directions (cardinal + diagonals)
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        blocked_dirs = set()

        # Check increasing distance; for each direction stop that ray when a wall is hit.
        for step in range(1, max_dist + 1):
            for idx, (dx, dy) in enumerate(directions):
                if idx in blocked_dirs:
                    continue

                ni = i + dx * step
                nj = j + dy * step

                if not (0 <= ni < self.width and 0 <= nj < self.height):
                    # Out of bounds acts like a wall for this direction.
                    blocked_dirs.add(idx)
                    continue

                neighbors = self.adjacency_map.get((ni, nj))
                if neighbors == None: # means neighbor contains a wall. Hit a wall: stop exploring further along this direction.
                    blocked_dirs.add(idx)
                elif neighbors:
                    return (ni, nj)
                    

        return None
        
    def compute_path(self, entity1, pos):
        start = self.nearest_node((entity1.x_pos, entity1.y_pos))
        end = self.nearest_node(pos)
        is_on_unaccessible_tile = False

        if not self.adjacency_map[start]:
            is_on_unaccessible_tile = True
            start = self.closest_accessible_tile(start)

        if not self.adjacency_map[end]:
            end = self.closest_accessible_tile(end)

        path = A_star(start, end, self)
        if path != None: 
            return is_on_unaccessible_tile, list(map(lambda node: self.position(node[0], node[1]), path))
        else:
            return is_on_unaccessible_tile, None
        
    def rect(self, i, j, density_opt=None):
        density = self.density if density_opt == None else density_opt
        edge_tolerance = self.edge_tolerance
        i = max(0, i*density - edge_tolerance)
        j = max(0, j*density - edge_tolerance)
        return pygame.Rect(i, j, density + 2*edge_tolerance, density+ 2*edge_tolerance)
    

class NavMesh(Mesh):
    def __init__(self, size, width, height, density, edge_tolerance):
        super().__init__(size, width, height, density)
        self.edge_tolerance = edge_tolerance

class VentMesh(Mesh):
    def __init__(self, size, width, height, density, edge_tolerance):
        super().__init__(size, width, height, density, edge_tolerance)