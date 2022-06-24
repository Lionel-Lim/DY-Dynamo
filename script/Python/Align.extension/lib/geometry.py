import math
from collections import Iterable

def Flatten(x):
    if isinstance(x, Iterable):
        return [a for i in x for a in Flatten(i)]
    else:
        return [x]

def Accumulate(list):
    total = 0
    for x in list:
        total += x
        yield total

def Clip(value, min, max):
    """
    Clip (limit) the values in an array.
    For example, if an interval of [0, 1] is specified, values smaller than 0 become 0, and values larger than 1 become 1.
    """
    return min if value < min else max if value > max else value

def IsClose(val1, val2, tolerance=0.000001):
    if abs(val1-val2) <= tolerance:
        return True
    else:
        return False

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
        """
        Project two rays from Points to Vector directions and Find a point.
        """
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

    def ByTwoLines(self, line1, line2):
        """
        Find a point at intersection of two lines
        return 0 : Lines are parallel.
        return 1 : Lines are same.
        return -1 : There is no intersection.
        """
        def discr(p1, p2, p3):
            return (p3.Y - p1.Y) * (p2.X - p1.X) > (p2.Y - p1.Y) * (p3.X - p1.X)
        a, b, c, d = line1.StartPoint, line1.EndPoint, line2.StartPoint, line2.EndPoint
        slope1, slope2 = line1.Slope, line2.Slope
        yint1, yint2 = line1.YIntcept, line2.YIntcept
        px = (yint2 - yint1) / (slope1 - slope2)
        py = (slope1 * px) + yint1
        if slope1 == slope2:
            if yint1 == yint2:
                return 1
            return 0
        elif not(discr(a, c, d) != discr(b, c, d) and discr(a, b, c) != discr(a, b, d)):
            return -1
        else:
            return PointEntity(px, py)

    def ByArcAndLine(self, arc, line, full_line=False, tangent_tol=1e-9):
        """ 
        Find the points at which a Arc intersects a line-segment.  This can happen at 0, 1, or 2 points.
        Args:
            Arc : ArcEntity
            Line : LineEntity
            param full_line: True to find intersections along full line - not just in the segment.  False will just return intersections within the segment.
            param tangent_tol: Numerical tolerance at which we decide the intersections are close enough to consider it a tangent
            return [Point Entity] : A list of length 0, 1, or 2, where each element is a point at which the circle intercepts a line segment.
            return -1 : There is no intersection.

        Note: We follow: http://mathworld.wolfram.com/Circle-LineIntersection.html
        """
        create = CreateEntity()
        circle_centre, circle_radius = arc.CentrePoint, arc.Radius
        pt1, pt2 = line.StartPoint, line.EndPoint
        p1x, p1y = pt1.X, pt1.Y
        p2x, p2y = pt2.X, pt2.Y
        cx, cy = circle_centre.X, circle_centre.Y
        x1, y1 = p1x - cx, p1y - cy
        x2, y2 = p2x - cx, p2y - cy
        dx, dy = x2 - x1, y2 - y1
        dr = math.pow((math.pow(dx, 2) + math.pow(dy, 2)), 0.5)
        big_d = (x1 * y2) - (x2 * y1)
        discriminant = (math.pow(circle_radius, 2) * math.pow(dr, 2)) - math.pow(big_d, 2)
        # return discriminant
        if discriminant < 0:  # No intersection between circle and line
            return [-1]
        else:  # There may be 0, 1, or 2 intersections with the segment
            intersections_all = [
                (cx + (big_d * dy + sign * (-1 if dy < 0 else 1) * dx * math.pow(discriminant, 0.5)) / math.pow(dr, 2),
                cy + (-big_d * dx + sign * abs(dy) * math.pow(discriminant, .5)) / math.pow(dr, 2))
                for sign in ((1, -1) if dy < 0 else (-1, 1))]  # This makes sure the order along the segment is correct
            if not full_line:  # If only considering the segment, filter out intersections that do not fall within the segment
                fraction_along_segment = [(xi - p1x) / dx if abs(dx) > abs(dy) else (yi - p1y) / dy for xi, yi in intersections_all]
                intersections_all = [pt for pt, frac in zip(intersections_all, fraction_along_segment) if 0 <= frac <= 1]
            if len(intersections_all) == 2 and abs(discriminant) <= tangent_tol:  # If line is tangent to circle, return just one point (as both intersections have same location)
                intersections_all = [intersections_all[0]]
            intersection_points = [PointEntity(fig[0], fig[1]) for fig in intersections_all]
            intersection_vectors = [create.VectorByTwoPoints(arc.CentrePoint, pt) for pt in intersection_points]
            cen2start = create.VectorByTwoPoints(arc.CentrePoint, arc.StartPoint)
            angle = [cen2start.AngleTo(vec, True) for vec in intersection_vectors]
            result = []
            # return angle, math.degrees(arc.Angle)
            if len(intersections_all)==0:
                return [-1]
            while angle:
                compare = angle.pop()
                point = intersection_points.pop()
                clockwise = -1 if arc.Angle < 0 else 1
                if (0 <= compare * clockwise <= math.degrees(arc.Angle) * clockwise):
                    result.append(point)
                else:
                    result.append(-1)
            return result

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
        self.Slope = self.Y / self.X
    
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
        Degree [0, 360]
        """
        ref = self.Normalise()
        measure = vector.Normalise()
        dot = ref.DotProduct(measure)
        cross = ref.CrossProduct(measure)
        radian = -math.atan2(cross, dot)
        return radian if not isdegree else math.degrees(radian)
        #Only Between [0:180]
        # v1_u = self.Normalise()
        # v2_u = vector.Normalise()
        # dot = Clip(v1_u.DotProduct(v2_u),-1,1)
        # angle = math.acos(dot)
        # return angle if not isdegree else math.degrees(angle)
    
    def Reverse(self):
        return VectorEntity(self.X * -1, self.Y * -1)
    
class LineEntity:
    def __init__(self, startpoint, endpoint):
        self.StartPoint = startpoint
        self.EndPoint = endpoint
        self.Length = startpoint.DistanceTo(endpoint)
        self.Direction = VectorEntity(endpoint.X - startpoint.X, endpoint.Y - startpoint.Y)
        self.Slope = (endpoint.Y - startpoint.Y) / (endpoint.X - startpoint.X)
        self.YIntcept = -(self.Slope * startpoint.X) + startpoint.Y
        self.Type = "Line"

    def __call__(self):
        return [self.StartPoint, self.EndPoint]
    
    def Reversed(self):
        return LineEntity(self.EndPoint, self.StartPoint)

    def IsInside(self, point):
        create = CreateEntity()
        direction = create.VectorByTwoPoints(self.StartPoint, point)
        return IsClose(direction.Slope, self.Slope) and direction.Length <= self.Length

    def GetEndPoint(self, condition):
        if condition == 0:
            return self.StartPoint
        elif condition == 1:
            return self.EndPoint
        elif condition == -1:
            return self.__call__()
        else:
            raise ArgumentException("{} is not valid argument.".format(condition))
        
    def PointAtSegmentLength(self, segmentlength):
        try:
            if segmentlength > self.Length:
                raise ArgumentOutOfRangeException("Length {} is Out of Line Length (length <= {})".format(segmentlength, self.Length))
        except ArgumentOutOfRangeException as e:
            return "Error : {}".format(e)
        ratio = segmentlength / self.Length
        xt = ratio * (self.EndPoint.X - self.StartPoint.X)
        yt = ratio * (self.EndPoint.Y - self.StartPoint.Y)
        return PointEntity(self.StartPoint.X + xt, self.StartPoint.Y + yt)

    def SegmentLengthAtPoint(self, point):
        return self.StartPoint.DistanceTo(point)
    
    def GetNormal(self):
        cross = VectorEntity(self.Direction.Y * 1, self.Direction.X * -1).Normalise()
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
        self.Length = self.Radius * abs(self.Angle)
        self.__IsClockwise = False if self.__CTR2STRT.CrossProduct(self.__CTR2END) > 0 else True
        self.Type = "Arc"
    
    def __call__(self):
        return [self.StartPoint, self.EndPoint]

    def Reversed(self):
        return ArcEntity(self.EndPoint, self.StartPoint, self.CentrePoint)
    
    def IsInside(self, point):
        create = CreateEntity()
        at_radius = IsClose(self.CentrePoint.DistanceTo(point), self.Radius)
        angle = self.__CTR2STRT.AngleTo(create.VectorByTwoPoints(self.CentrePoint, point))
        dir = 1 if self.__IsClockwise else -1
        if (0 <= angle * dir <= self.Angle * dir) and at_radius:
            return True
        else:
            return False
        
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
    
    def SegmentLengthAtPoint(self, point):
        create = CreateEntity()
        angle = self.__CTR2STRT.AngleTo(create.VectorByTwoPoints(self.CentrePoint, point))
        segmentlength = abs((math.pi * self.Radius * math.degrees(angle)) / 180)
        return segmentlength
    
    def NormalAtSegmentLength(self, segmentlength):
        point = self.PointAtSegmentLength(segmentlength)
        normal = point.VectorTo(self.CentrePoint).Normalise()
        return normal
    
    def TangentAtSegmentLength(self, segmentlength):
        norm = self.NormalAtSegmentLength(segmentlength)
        cross = VectorEntity(-norm.Y*1 - 0*0, 0*0 + norm.X*1).Normalise()
        return cross

class PolyCurveEntity:
    def __init__(self, curveset, tolerance=0.001):
        self.Curves = curveset
        self.Tolerance = tolerance
        self.IsValid = self.IsContinuous(curveset, tolerance)
        self.Length = sum([crv.Length for crv in self.Curves])
    
    def IsContinuous(self, curveset, tolerance=0.001):
        dist = []
        crvs = list(curveset)
        for index in range(len(crvs)):
            if index == len(crvs)-1:
                return True
            dist.append(crvs[index].EndPoint.DistanceTo(crvs[index+1].StartPoint))
            if dist[index] >= tolerance:
                return False
        
    def PointAtSegmentLength(self, segmentlength):
        acc = list(Accumulate([crv.Length for crv in self.Curves]))
        acc.insert(0, 0)
        for index in range(len(acc)):
            try:
                if segmentlength > self.Length:
                    raise ArgumentOutOfRangeException("Length {} is Out of Polycurve Length (length <= {})".format(segmentlength, self.Length))
            except ArgumentOutOfRangeException as e:
                return "Error : {}".format(e)
            if acc[index] <= segmentlength < acc[index+1]:
                return self.Curves[index].PointAtSegmentLength(segmentlength-acc[index])
    
    def SegmentLengthAtPoint(self, point):
        acc = list(Accumulate([crv.Length for crv in self.Curves]))
        acc.insert(0, 0)
        for index, crv in enumerate(self.Curves):
            if crv.IsInside(point):
                return acc[index] + crv.SegmentLengthAtPoint(point), acc
        return False
    
    def NormalAtSegmentLength(self, segmentlength):
        acc = list(Accumulate([crv.Length for crv in self.Curves]))
        acc.insert(0, 0)
        for index in range(len(acc)):
            try:
                if segmentlength > self.Length:
                    raise ArgumentOutOfRangeException("Length {} is Out of Polycurve Length (length <= {})".format(segmentlength, self.Length))
            except ArgumentOutOfRangeException as e:
                return "Error : {}".format(e)
            if acc[index] <= segmentlength < acc[index+1]:
                if self.Curves[index].Type == "Line":
                    return self.Curves[index].GetNormal()
                else:
                    return self.Curves[index].NormalAtSegmentLength(segmentlength-acc[index])

    def IntersectWith(self, line):
        intersect_point = []
        result = []
        intersect = Intersect()
        for crv in self.Curves:
            if crv.Type == "Line":
                val = intersect.ByTwoLines(crv, line)
            elif crv.Type == "Arc":
                val = intersect.ByArcAndLine(crv, line)
            else:
                False
            intersect_point.append(val)
        intersect_point = Flatten(intersect_point)
        for elem in intersect_point:
            if elem.__class__.__name__ == "PointEntity":
                result.append(elem)
        return result