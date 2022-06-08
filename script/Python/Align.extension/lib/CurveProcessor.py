import math

class ArgumentOutOfRangeException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class PointEntity:
    """
    Create Point Instance by 2D Coordinates
    Args
        (float)x : x axis coordinate
        (float)y : y axis coordinate
    """
    def __init__(self, point_x = 0, point_y = 0):
        self.x = point_x
        self.y = point_y

    def __call__(self):
        return [self.x,self.y]

class VectorEntity:
    def __init__(self, vector_x = 0, vector_y = 0):
        self.x = vector_x
        self.y = vector_y
    
    def __call__(self):
        return [self.x,self.y]
    
    def Normalise(self):
        norm = math.sqrt(math.pow(self.x,2)+math.pow(self.y,2))
        vec_normalised = VectorEntity(self.x / norm, self.y / norm)
        return vec_normalised

    def Add(self, point):
        newpoint = PointEntity(point.x+self.x, point.y+self.y)
        return newpoint


class CreateEntity:
    def Vector_ByTwoPoints(self, point_first, point_second):
        dist_x = point_second.x - point_first.x
        dist_y = point_second.y - point_first.y
        vec = VectorEntity(dist_x, dist_y)
        return vec
        
    def VectorByThreePoints(self, point_1, point_2, point_3):
        """
        Return a point using Three point
        Args
            (point)end0 : One of End Point
            (point)end1 : One of End Point
            (point)pointOnArc : Any Point on Arc
        """
        a = point_1
        b = point_2
        c = point_3
        ab_mid = PointEntity((a.x+c.x)/2 , (a.y+c.y)/2)
        bc_mid = PointEntity((b.x+c.x)/2 , (b.y+c.y)/2)
        ab_slope = (a.y - c.y) / (a.x - c.x)
        bc_slope = (b.y - c.y) / (b.x - c.x)
        ab_slope_perp = -math.pow(ab_slope, -1)
        bc_slope_perp = -math.pow(bc_slope,-1)
        ab_yintercept = ab_mid.y - (ab_slope_perp * ab_mid.x)
        bc_yintercept = bc_mid.y - (bc_slope_perp * bc_mid.x)
        ab_vec = self.Vector_ByTwoPoints(ab_mid, PointEntity(0,ab_yintercept))
        bc_vec = self.Vector_ByTwoPoints(bc_mid, PointEntity(0,bc_yintercept))
        its = Intersect()
        centre_point = its.ByTwoVectorAndPoint(ab_mid, ab_vec, bc_mid, bc_vec)
        return centre_point

class ArcEntity:
    def __init__(self, center_point, radius):
        self.ctrpoint = center_point
        self.radius = radius
        
    def PointAtSegmentLength(self, segmentlength):
        rad = math.radians((180*segmentlength)/(math.pi*self.radius))
        try:
            if rad > 1:
                raise ArgumentOutOfRangeException("Length {} is Out of Arc Length".format(segmentlength))
            dist_x = self.radius * math.cos(rad)
            dist_y = self.radius * math.sin(rad)
            point_x = self.ctrpoint.x + dist_x
            point_y = self.ctrpoint.y + dist_y
            return PointEntity(point_x, point_y)
        except ArgumentOutOfRangeException as e:
            return "Error : {}".format(e)
    # def Line_PointAt(self, start_point, direction)

class Intersect:
    def ByTwoVectorAndPoint(self, point1, vector1, point2, vector2):
        dx = point2.x - point1.x
        dy = point2.y - point2.x
        det = (vector2.x * vector1.y) - (vector2.y * vector1.x)
        u = ((dy * vector2.x) - (dx * vector2.y)) / det
        v = ((dy * vector1.x) - (dx * vector1.y)) / det
        if u < 0 and v < 0 :
            return False, u, v
        m0 = vector1.y / vector1.x
        m1 = vector2.y / vector2.x
        b0 = point1.y - (m0 * point1.x)
        b1 = point2.y - (m1 * point2.x)
        x = (b1 - b0) / (m0 - m1)
        y = (m0 * x) + b0
        return PointEntity(x,y)
