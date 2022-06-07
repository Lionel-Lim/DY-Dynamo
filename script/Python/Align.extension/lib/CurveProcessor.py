import math


class ArcEntity:
    def __self__(self, center_point:list, radius:float):
        self.__ctrpoint__ = center_point
        self.__radius__ = radius
        
    def Arc_PointAtSegmentLength(self, length:float):
        # center_point format is [X,Y]
        angle = math.radians((180*length)/(math.pi*self.__radius__))
        dist_x = self.__radius__ * math.cos(angle)
        dist_y = self.__radius__ * math.sin(angle)
        point_x = self.__ctrpoint__[0] + dist_x
        point_y = self.__ctrpoint__[1] + dist_y
        return point_x, point_y
    def Line_PointAt(self, start_point:list, direction)