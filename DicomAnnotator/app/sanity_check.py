import numpy as np
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

# check anti-clockwise of some points in order, in image coord system
def checkAntiClockwise(points):
    point = points[-1]
    sum = 0
    for p in points:
        sum += (p[0] - point[0])*(p[1] + point[1])
        point = p

    # image coords is a left hand coord system
    return sum > 0

# get the intersection point of p[0], p[2] and p[1], p[3]
# if no intersection points, then return (None, None)
def _get_intersection(points):
    # if two vertical lines
    if points[0][0] == points[2][0] and points[1][0] == points[3][0]:
        return (None, None)
    # if one of two lines is vertical
    if points[0][0] == points[2][0]:
        k2 = (points[1][1] - points[3][1])/(points[1][0] - points[3][0]) 
        b2 = points[1][1] - k2*points[1][0]
        y = k2*points[0][0]+b2
        return (points[0][0], y)

    if points[1][0] == points[3][0]:
        k1 = (points[0][1] - points[2][1])/(points[0][0] - points[2][0]) 
        b1 = points[0][1] - k1*points[0][0]
        y = k1*points[1][0]+b1
        return (points[1][0], y)

    k1 = (points[0][1] - points[2][1])/(points[0][0] - points[2][0]) 
    k2 = (points[1][1] - points[3][1])/(points[1][0] - points[3][0]) 
    if k1 == k2:
        return (None, None)
    b1 = points[0][1] - k1*points[0][0]
    b2 = points[1][1] - k2*points[1][0]
    A1 = -k1
    B1 = 1
    C1 = -b1
    A2 = -k2
    B2 = 1
    C2 = -b2
    x = (B1*C2-B2*C1)/(A1*B2-A2*B1)
    y = (C1*A2-C2*A1)/(A1*B2-A2*B1)
    return (x,y)

# check if one point is the interior point of a quadrilateral whose corners
# are points[0], [1], [2], [3] in order
def _checkInterior(point, points):
    if point == (None, None):
        return False
    polygon = Polygon(points)
    return polygon.contains(Point(point))
    # ys = []
    # xs = []
    # for coord in points:
    #     xs.append(coord[0])
    #     ys.append(coord[1])
    # xmax = max(xs)
    # xmin = min(xs)
    # ymax = max(ys)
    # ymin = min(ys)
    
    # x = points[0]
    # y = points[1]

    # if x > xmax or x < xmin or y > ymax or y < ymin:
    #     return False
    # xmax_idx = xs.index(xmax)
    # xmin_idx = xs.index(xmin)
    # y_xmax = ys[xmax_idx]
    # y_xmin = ys[xmin_idx]

    # if y > y_xmax:
    #     ymax_idx = ys.index(ymax)
    #     x0 = xs[ymax_idx]
    #     y0 = ymax
    # else:
    #     ymin_idx = ys.index(ymin)
    #     x0 = xs[ymin_idx]
    #     y0 = ymin
    # if x0 != xmax:
    #     kmax = (y0-y_xmax)/(x0-xmax)
    #     bmax = y_xmax - kmax*xmax
    #     x_edge_max = (y - bmax)/kmax
    # else:
    #     x_edge_max = x0

    # if y > y_xmin:
    #     ymax_idx = ys.index(ymax)
    #     x0 = xs[ymax_idx]
    #     y0 = ymax
    # else:
    #     ymin_idx = ys.index(ymin)
    #     x0 = xs[ymin_idx]
    #     y0 = ymin
    # if x0 != xmin:
    #     kmin = (y0-y_xmim)/(x0-xmim)
    #     bmin= y_xmin- kmin*xmin
    #     x_edge_min = (y - bmin)/kmin
    # else:
    #     x_edge_min = x0

    # return x < x_edge_max and x > x_edge_min




# check if the diagonal intersection is the interior point
def checkDiagIntersection(points):
    intersect = _get_intersection(points)
    if intersect == (None,None):
        return False

    return _checkInterior(intersect, points)


# sanity check
# 1. check anticlockwise
# 2. check diagal intersection is the interior point
def sanity_check(points):
    return checkAntiClockwise(points) and checkDiagIntersection(points)
