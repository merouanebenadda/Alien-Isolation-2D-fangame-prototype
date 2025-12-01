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

    def random_tile(self, entity, range): # /!\ has to be optimized, especially for bigger maps
        inf, sup = range
        x, y = entity.x_pos, entity.y_pos

        n = len(self.adjacency_map)

        keys_list = list(self.adjacency_map.keys())

        rand_i, rand_j = keys_list[rd.randint(0, n-1)]
        rand_x, rand_y = self.position(rand_i, rand_j)

        while (not inf < euclidian_distance((x, y), (rand_x, rand_y)) < sup) or not self.adjacency_map[(rand_i, rand_j)]:
            rand_i, rand_j = keys_list[rd.randint(0, n-1)]
            rand_x, rand_y = self.position(rand_i, rand_j)

        return rand_x, rand_y

    def nearest_node(self, pos_x, pos_y=None):
        """
        Converts the entity's continuous pixel position (x_pos, y_pos) 
        into discrete grid coordinates (i, j).
        """
        # Calculate the grid column (i) and row (j) using integer division
        # This gives the floor of the division, which is the correct tile index.
        if pos_y==None:
            pos_x, pos_y = pos_x
        
        i = int(pos_x // self.density)
        j = int(pos_y // self.density)

        # Critical Safety: Clamp the indices to the mesh boundaries (0 to width/height - 1)
        # This prevents crashes if an entity somehow moves slightly off the map edge.
        i = max(0, min(i, self.width - 1))
        j = max(0, min(j, self.height - 1))
        
        return (i, j)
    
    def position(self, i, j=None):
        """
        Returns the center of the tile of indices (i, j)
        """
        if j == None:
            i, j = i
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

class VentMesh(Mesh):
    def __init__(self, size, width, height, density):
        super().__init__(size, width, height, density)
        self.nodes = {} # keys: coordinates of nodes, values: list of connected nodes (i, j)
        self.exits = [] # list of (i, j) positions of vent access points

    def compute_path(self, entity1, point):
        """
        Computes a path from the entity's current position to the target point using A* on the vent mesh.
        Returns a list of continuous (x, y) positions representing the path, starting with the target point.
        """
        path_start = self.get_closest_vent_node(self.nearest_node(entity1.x_pos, entity1.y_pos))
        path_end = self.get_closest_vent_node(self.nearest_node(point))

        path = A_star(path_start, path_end, self)
        if path != None: 
            return [point] + list(map(lambda node: self.position(node[0], node[1]), path))
        else:
            return None
        
    def get_closest_vent_node(self, i, j=None):
        """
        Finds the nearest valid vent node (key in adjacency_map) to the given 
        grid index (i, j).
        """
        if j == None:
            i, j = i

        if not self.adjacency_map:
            return None
        
        current_best_node = None
        min_dist_sq = float('inf')

        start_node = (i, j)
        
        # Iterate over all defined vent nodes
        for node in self.adjacency_map.keys():
            # Calculate squared Euclidean distance in grid space
            dist_sq = (node[0] - start_node[0])**2 + (node[1] - start_node[1])**2
            
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                current_best_node = node
                
        return current_best_node

    def get_closest_vent_access(self, pos_x, pos_y=None):
        """
        Finds the nearest vent exit point to the given continuous position (pos_x, pos_y) returned as (x, y).
        """
        if pos_y == None:
            pos_x, pos_y = pos_x

        if not self.exits:
            return None
        
        current_best_exit = None
        min_dist_sq = float('inf')

        # Iterate over all defined vent exits
        for exit_point in self.exits:
            # Calculate squared Euclidean distance
            exit_point = self.position(exit_point)
            dist_sq = (exit_point[0] - pos_x)**2 + (exit_point[1] - pos_y)**2
            
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                current_best_exit = exit_point
                
        return (current_best_exit)

    def random_point(self):
        """Returns a random coordinate (x, y) situated exactly on a vent line."""
        if not self.adjacency_map:
            return None

        # 1. Pick a random starting node
        node_start = rd.choice(list(self.adjacency_map.keys()))
        
        # 2. Pick a random connected neighbor
        if not self.adjacency_map[node_start]:
            return self.position(*node_start) # It's a dead end, stay at node
            
        node_end, _ = rd.choice(self.adjacency_map[node_start])

        # 3. Interpolate
        start_pos = self.position(*node_start)
        end_pos = self.position(*node_end)
        
        t = rd.uniform(0, 1) # Random factor
        
        rx = start_pos[0] + t * (end_pos[0] - start_pos[0])
        ry = start_pos[1] + t * (end_pos[1] - start_pos[1])
        
        return rx, ry