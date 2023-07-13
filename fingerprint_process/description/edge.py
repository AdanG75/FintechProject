import enum
import numpy as np
from math import atan, degrees

from fingerprint_process.utils.error_message import ErrorMessage


class Edge(ErrorMessage):

    def __init__(self, origin_minutiae, destination_minutiae, angle_tolerance=0.01) -> None:
        super().__init__()
        self.__origin_minutiae = origin_minutiae
        self.__destination_minutiae = destination_minutiae

        self.__origin_y_pos = 0
        self.__origin_x_pos = 0
        self.__destination_y_pos = 0
        self.__destination_x_pos = 0

        self.__obtain_pisition_of_minutiaes()

        self.__lenght = self.__obtain_length()
        self.__quadrant = self.__obtain_quadrant()
        self.__ratio = 1
        self.__angle = 0
        self.obtain_angle(None)

        self.__angle_tolerance = angle_tolerance

    class Quadrant(enum.Enum):
        FIRST_QUADRANT = 1
        SECOND_QUADRANT = 2
        THIRD_QUADRANT = 3
        FOURTH_QUADRANT = 4

    def __obtain_pisition_of_minutiaes(self):
        self.__origin_y_pos = self.__origin_minutiae.get_posy()
        self.__origin_x_pos = self.__origin_minutiae.get_posx()
        self.__destination_y_pos = self.__destination_minutiae.get_posy()
        self.__destination_x_pos = self.__destination_minutiae.get_posx()

    def __euclidean_distance(self, origin_y_pos, origin_x_pos, destination_y_pos, destination_x_pos):
        return np.sqrt((destination_y_pos - origin_y_pos) ** 2 + (destination_x_pos - origin_x_pos) ** 2)

    def __obtain_length(self):
        return round(self.__euclidean_distance(self.__origin_y_pos, self.__origin_x_pos, self.__destination_y_pos,
                                               self.__destination_x_pos), 2)

    def __obtain_quadrant(self):

        is_up = self.__origin_y_pos >= self.__destination_y_pos
        is_right = self.__origin_x_pos < self.__destination_x_pos

        if is_up:
            if is_right:
                return self.Quadrant.FIRST_QUADRANT

            return self.Quadrant.SECOND_QUADRANT

        else:
            if is_right:
                return self.Quadrant.FOURTH_QUADRANT

            return self.Quadrant.THIRD_QUADRANT

    def get_length(self):
        return self.__lenght

    def get_quadrant(self):
        return self.__quadrant

    def get_origin_position(self):
        return (self.__origin_x_pos, self.__origin_y_pos)

    def get_destination_position(self):
        return (self.__destination_x_pos, self.__destination_y_pos)

    def obtain_ratio(self, before_edge):
        if before_edge is None:
            self.__ratio = 1
        else:
            self.__ratio = round(max(self.get_length(), before_edge.get_length()) /
                                 min(self.get_length(), before_edge.get_length()), 2)

    def __compute_slope(self, first_point, second_point):
        x1, y1 = first_point
        x2, y2 = second_point

        if (x1 == x2):
            return (0, True)
        else:
            return ((y2 - y1) / (x2 - x1), False)

    def __compute_minimum_angle(self, first_slope, second_slope):
        value_first_slope = first_slope[0]
        logic_first_slope = first_slope[1]
        value_second_slope = second_slope[0]
        logic_second_slope = second_slope[1]

        if (logic_first_slope != logic_second_slope) and (value_first_slope == value_second_slope == 0):
            return 90

        if ((value_first_slope * value_second_slope) == (-1)):
            return 90
        else:
            angle = abs(degrees(
                atan((value_second_slope - value_first_slope) / (1 + (value_first_slope * value_second_slope)))))

        return min(angle, 180 - angle)

    def obtain_angle(self, before_edge):
        if before_edge is None:
            point_2_x, point_2_y = self.get_origin_position()
            point_3_x, point_3_y = self.get_destination_position()
            point_1_x, point_1_y = point_3_x + 1, point_2_y
        else:
            point_1_x, point_1_y = before_edge.get_origin_position()
            point_2_x, point_2_y = before_edge.get_destination_position()
            point_3_x, point_3_y = self.get_destination_position()

        slope_one = self.__compute_slope((point_1_x, point_1_y), (point_2_x, point_2_y))
        slope_two = self.__compute_slope((point_2_x, point_2_y), (point_3_x, point_3_y))

        self.__angle = round(self.__compute_minimum_angle(slope_one, slope_two), 2)

    def get_ratio(self):
        return self.__ratio

    def get_angle(self):
        return self.__angle

    def get_edge_description(self):
        return (self.__origin_x_pos, self.__origin_y_pos, self.__destination_x_pos, self.__destination_y_pos,
                self.__lenght, self.__quadrant, self.__ratio, self.__angle)


# if __name__ == '__main__':
#     first_minutiae = Minutiae(posy=150, posx=90, angle=0.0, point_type='e')
#     second_minutiae = Minutiae(posy=120, posx=90, angle=0.0, point_type='e')
#     third_minutiae = Minutiae(posy=120, posx=10, angle=0.0, point_type='e')
#     fourth_minutiae = Minutiae(posy=100, posx=200, angle=0.0, point_type='e')
#     fifth_minutiae = Minutiae(posy=55, posx=127, angle=0.0, point_type='e')
#     sixth_minutiae = Minutiae(posy=9, posx=1, angle=0.0, point_type='e')
#     seventh_minutiae = Minutiae(posy=5, posx=5, angle=0.0, point_type='e')
#     eigth_minutiae = Minutiae(posy=1, posx=1, angle=0.0, point_type='e')
#
#     edge_1 = Edge(first_minutiae, second_minutiae)
#     edge_2 = Edge(second_minutiae, third_minutiae)
#     # edge_3 = Edge(third_minutiae, first_minutiae)
#     edge_3 = Edge(third_minutiae, fourth_minutiae)
#     edge_4 = Edge(fourth_minutiae, fifth_minutiae)
#     edge_5 = Edge(fifth_minutiae, sixth_minutiae)
#     edge_6 = Edge(sixth_minutiae, seventh_minutiae)
#     edge_7 = Edge(seventh_minutiae, eigth_minutiae)
#
#     # edge_1.obtain_ratio(None)
#     # edge_2.obtain_ratio(edge_1)
#     # edge_3.obtain_ratio(edge_2)
#     # edge_4.obtain_ratio(edge_3)
#     # edge_5.obtain_ratio(edge_4)
#     # edge_6.obtain_ratio(edge_5)
#     # edge_7.obtain_ratio(edge_6)
#
#     # edge_1.obtain_angle(None)
#     # edge_2.obtain_angle(edge_1)
#     # edge_3.obtain_angle(edge_2)
#     # edge_4.obtain_angle(edge_3)
#     # edge_5.obtain_angle(edge_4)
#     # edge_6.obtain_angle(edge_5)
#     # edge_7.obtain_angle(edge_6)
#
#     print(edge_1.get_edge_description())
#     print(edge_2.get_edge_description())
#     print(edge_3.get_edge_description())
#     print(edge_4.get_edge_description())
#     print(edge_5.get_edge_description())
#     print(edge_6.get_edge_description())
#     print(edge_7.get_edge_description())
#
#     # print(edge_1.Quadrant)
