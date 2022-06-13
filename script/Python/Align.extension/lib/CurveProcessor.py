import math
from collections import Iterable

def Flatten(x):
    if isinstance(x, Iterable):
        return [a for i in x for a in Flatten(i)]
    else:
        return [x]

def Clip(value, min, max):
    """
    Clip (limit) the values in an array.
    For example, if an interval of [0, 1] is specified, values smaller than 0 become 0, and values larger than 1 become 1.
    """
    return min if value < min else max if value > max else value

class ArgumentOutOfRangeException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class ArgumentException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class Intersect:
    def ByTwoVectorAndPoint(self, point1, vector1, point2, vector2):
        vector1 = vector1.Normalise()
        vector2 = vector2.Normalise()
        create = CreateEntity()
        stp2edp = create.VectorByTwoPoints(point1, point2)
        cross1 = stp2edp.CrossProduct(vector2)
        cross2 = vector1.CrossProduct(vector2)
        t = cross1 / cross2
        add_vector = vector1.Scale(t)
        intersect_point = add_vector.Add(point1)
        return intersect_point

class CreateEntity:
    def VectorByTwoPoints(self, point_first, point_second):
        dist_x = point_second.X - point_first.X
        dist_y = point_second.Y - point_first.Y
        vec = VectorEntity(dist_x, dist_y)
        return vec
        
    def ArcByThreePoints(self, startpoint, endpoint, midpoint):
        """
        Return a point using Three point
        Args
            (point)startpoint : Start Point of Arc
            (point)endpoint : End Point of Arc
            (point)midpoint : A point on Arc
        """
        ab_mid = PointEntity((startpoint.X+midpoint.X)/2 , (startpoint.Y+midpoint.Y)/2)
        bc_mid = PointEntity((endpoint.X+midpoint.X)/2 , (endpoint.Y+midpoint.Y)/2)
        #slope == 0 -> X Axis Parallel, Slope == zero divider -> Y Axis Parallel
        def Calculate_Vector_To_Centrepoint(edgepoint, middlepoint):
            ydiff = edgepoint.Y - middlepoint.Y
            xdiff = edgepoint.X - middlepoint.X
            if ydiff == 0:
                tocentre = VectorEntity(0, middlepoint.X)
            elif xdiff == 0:
                tocentre = VectorEntity(-middlepoint.Y, 0)
            else:
                slope = (edgepoint.Y - middlepoint.Y) / (edgepoint.X - middlepoint.X)
                perp_slope = -math.pow(slope,-1)
                y_intercept = middlepoint.Y - (perp_slope * middlepoint.X)
                tocentre = self.VectorByTwoPoints(middlepoint, PointEntity(0,y_intercept))
            return tocentre
        ab_vec = Calculate_Vector_To_Centrepoint(startpoint, midpoint)
        bc_vec = Calculate_Vector_To_Centrepoint(endpoint, midpoint)
        intersection = Intersect()
        centre_point = intersection.ByTwoVectorAndPoint(ab_mid, ab_vec, bc_mid, bc_vec)
        return ArcEntity(startpoint, endpoint, centre_point)

class PointEntity:
    """
    Create Point Instance by 2D Coordinates
    Args
        (float)x : x axis coordinate
        (float)y : y axis coordinate
    """
    def __init__(self, point_x = 0, point_y = 0):
        self.X = point_x
        self.Y = point_y

    def __call__(self):
        return (self.X,self.Y)

    def DistanceTo(self, point):
        xdist = self.X - point.X
        ydist = self.Y - point.Y
        distance = math.sqrt(math.pow(xdist,2) + math.pow(ydist,2))
        return distance

    def Origin(self):
        return PointEntity(0,0)

    def Rotate(self, origin, angle=0):
        """
        Rotate a point counterclockwise by a given angle around a given origin.
        The angle should be given in radians.
        """
        ox = origin.X
        oy = origin.Y
        px = self.X
        py = self.Y

        qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
        qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
        return PointEntity(qx, qy)
    
    def VectorTo(self, point):
        create = CreateEntity()
        return create.VectorByTwoPoints(self, point)

class VectorEntity:
    """
    Create Vector Instance by 2D Coordinates
    Args
        (float)x : x axis coordinate
        (float)y : y axis coordinate
    """
    def __init__(self, vector_x = 0, vector_y = 0):
        self.X = vector_x
        self.Y = vector_y
        self.Length = math.sqrt(math.pow(self.X,2)+math.pow(self.Y,2))
    
    def __call__(self):
        return (self.X,self.Y)
    
    def Normalise(self):
        norm = self.Length
        vec_normalised = VectorEntity(self.X / norm, self.Y / norm)
        return vec_normalised

    def Add(self, point):
        newpoint = PointEntity(point.X+self.X, point.Y+self.Y)
        return newpoint

    def CrossProduct(self, vector):
        cross_product = (self.X * vector.Y) - (self.Y * vector.X)
        return cross_product
    
    def DotProduct(self, vector):
        dot_product = sum([i*j for (i, j) in zip(self(), vector())])
        return dot_product

    def Scale(self, factor):
        scale_vector = VectorEntity(self.X * factor, self.Y * factor)
        return scale_vector
    
    def AngleTo(self, vector, isdegree=False):
        """
        Returns the angle(Radian) between this vector and the input vector.
        Set bool to True if the output is to be Degree, else Radian
        """
        v1_u = self.Normalise()
        v2_u = vector.Normalise()
        dot = Clip(v1_u.DotProduct(v2_u),-1,1)
        angle = math.acos(dot)
        return angle if not isdegree else math.degrees(angle)
    
    def Reverse(self):
        return VectorEntity(self.X * -1, self.Y * -1)
    
class LineEntity:
    def __init__(self, startpoint, endpoint):
        self.StartPoint = startpoint
        self.EndPoint = endpoint
        self.Length = math.sqrt(
            math.pow(
                self.StartPoint.X-self.EndPoint.X,2)+
                math.pow(self.StartPoint.Y-self.EndPoint.Y,2)
            )
        self.Direction = VectorEntity(endpoint.X - startpoint.X, endpoint.Y - startpoint.Y)

    def __call__(self):
        return [self.StartPoint, self.EndPoint]

    def GetEndPoint(self, condition):
        if condition == 0:
            return self.StartPoint
        elif condition == 1:
            return self.EndPoint
        elif condition == -1:
            return self.__call__()
        else:
            raise ArgumentException("{} is not valid argument.".format(condition))
        
    def GetPointAtSegmentLength(self, segmentlength):
        try:
            if segmentlength > self.Length:
                raise ArgumentOutOfRangeException("Length {} is Out of Line Length (length <= {})".format(segmentlength, self.Length))
        except ArgumentOutOfRangeException as e:
            return "Error : {}".format(e)
        ratio = segmentlength / self.Length
        xt = ratio * (self.EndPoint.X - self.StartPoint.X)
        yt = ratio * (self.EndPoint.Y - self.StartPoint.Y)
        return PointEntity(self.StartPoint.X + xt, self.StartPoint.Y + yt)
    
    def GetNormalAtSegmentLength(self):
        cross = VectorEntity(self.Direction.Y * -1, self.Direction.X * 1).Normalise()
        return cross

class ArcEntity:
    def __init__(self, startpoint, endpoint, centrepoint):
        self.StartPoint = startpoint
        self.EndPoint = endpoint
        self.CentrePoint = centrepoint
        self.Radius = centrepoint.DistanceTo(startpoint)
        create = CreateEntity()
        self.__CTR2STRT = create.VectorByTwoPoints(centrepoint, startpoint)
        self.__CTR2END = create.VectorByTwoPoints(centrepoint, endpoint)
        self.Angle = self.__CTR2STRT.AngleTo(self.__CTR2END)
        self.Length = self.Radius * self.Angle
        self.__IsClockwise = False if self.__CTR2STRT.CrossProduct(self.__CTR2END) > 0 else True
        
    def PointAtSegmentLength(self, segmentlength):
        try:
            if segmentlength > self.Length:
                raise ArgumentOutOfRangeException("Length {} is Out of Arc Length (length <= {})".format(segmentlength, self.Length))
        except ArgumentOutOfRangeException as e:
            return "Error : {}".format(e)
        rad = math.radians((180*segmentlength)/(math.pi*self.Radius))
        dir_rad = -rad if self.__IsClockwise else rad
        point = self.StartPoint.Rotate(self.CentrePoint, dir_rad)
        return point
    
    def NormalAtSegmentLength(self, segmentlength):
        point = self.PointAtSegmentLength(segmentlength)
        normal = point.VectorTo(self.CentrePoint).Normalise()
        return normal
    
    def TangentAtSegmentLength(self, segmentlength):
        norm = self.NormalAtSegmentLength(segmentlength)
        cross = VectorEntity(-norm.Y*1 - 0*0, 0*0 + norm.X*1).Normalise()
        return cross

class PolyCurveEntity:
    def __init__(self, curveset):
        self.IsContinuous(curveset)
    
    def IsContinuous(self, curveset):
        curveset
