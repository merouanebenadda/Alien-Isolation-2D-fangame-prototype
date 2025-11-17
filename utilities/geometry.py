from numpy import arctan2
import math

def is_parallel(p1, p2, q1, q2):
    x1, y1 = p1
    x2, y2 = p2

    a1, b1 = q1
    a2, b2 = q2

    return abs((a2-a1)*(y2-y1) - (x2-x1)*(b2-b1)) < 1e-6

def intersects(s1, s2):
    eps = 1e-6

    p1, p2 = s1
    q1, q2 = s2

    x1, y1 = p1
    x2, y2 = p2

    a1, b1 = q1
    a2, b2 = q2

    if is_parallel(p1, p2, q1, q2):
        return False
    

    denominator = ((x1-x2)*(b1-b2) - (y1-y2)*(a1-a2))

    t_p =  ((y2-b2)*(a1-a2) + (a2-x2)*(b1-b2)) / denominator
    t_q = -((b2-y2)*(x1-x2) + (x2-a2)*(y1-y2)) / denominator

    if eps <= t_p <= 1-eps and eps <= t_q <= 1-eps:
        return True
    
    else:
        return False
    
def euclidian_distance(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2

    return math.sqrt((x1-x2)**2+(y1-y2)**2)

def euclidian_distance_entities(entity1, entity2):
    x1, y1 = entity1.x_pos, entity1.y_pos
    x2, y2 = entity2.x_pos, entity2.y_pos

    return math.sqrt((x1-x2)**2+(y1-y2)**2)

def angle(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2

    return (arctan2(y2-y1, x2-x1)*180/math.pi)%360 # in [0, 360)

def angle_entity(entity1, entity2):
    x1, y1 = entity1.x_pos, entity1.y_pos
    x2, y2 = entity2.x_pos, entity2.y_pos

    return (arctan2(y2-y1, x2-x1)*180/math.pi)%360 # in [0, 360)