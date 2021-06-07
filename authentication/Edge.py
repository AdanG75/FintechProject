import enum
import numpy as np

class Edge(object):
    
    def __init__(self, origin_minutiae, destination_minutiae) -> None:
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
        self.__angle = 0.0


    class Quadrant(enum.Enum):
        FIRST_QUADRANT = 1
        SECOND_QUADRANT = 2
        THIRD_QUADRANT = 3
        FOURTH_QUADRANT = 4


    def __euclidean_distance(self, origin_y_pos, origin_x_pos, destination_y_pos, destination_x_pos):
        return np.sqrt((destination_y_pos - origin_y_pos) ** 2 + (destination_x_pos - origin_x_pos) ** 2)


    def __obtain_pisition_of_minutiaes(self):
        self.__origin_y_pos = self.__origin_minutiae.get_posy()
        self.__origin_x_pos = self.__origin_minutiae.get_posx()
        self.__destination_y_pos = self.__destination_minutiae.get_posy()
        self.__destination_x_pos = self.__destination_minutiae.get_posx()


    def __obtain_length(self):
        return self.__euclidean_distance(self, self.__origin_y_pos, self.__origin_x_pos, self.__destination_y_pos, self.__destination_x_pos)


    def __obtain_quadrant(self):

        is_up = self.__origin_y_pos >= self.__destination_y_pos
        is_right = self.__origin_x_pos < self.__destination_x_pos

        if is_up:
            if is_right:
                return Quadrant.FIRST_QUADRANT

            return Quadrant.SECOND_QUADRANT
        
        else:
            if is_right:
                return Quadrant.FOURTH_QUADRANT

            return Quadrant.THIRD_QUADRANT

    
    def get_length(self):
        return self.__lenght


    def get_quadrant(self):
        return self.__quadrant


    def get_origin_position(self):
        return (self.__origin_x_pos, self.__origin_y_pos)

    
    def get_destination_position(self):
        return (self.__destination_x_pos, self.__destination_y_pos)


    def obtain_ratio(self, this_edge, before_edge):
        if before_edge is None:
            self.__ratio = 1

        self.__ratio = round(max(this_edge.get_length(), before_edge.get_length) / 
                            min(this_edge.get_length(), before_edge.get_length), 2)


    def obtain_angle(self, this_edge, before_edge):

        if before_edge is None:
            point_2_x, point_2_y = this_edge.get_origin_position()
            point_3_x, point_3_y = this_edge.get_destination_position()
            point_1_x, point_1_y = point_3_x, point_2_y
        else:
            point_1_x, point_1_y = before_edge.get_origin_position()
            point_2_x, point_2_y = before_edge.get_destination_position()
            point_3_x, point_3_y = this_edge.get_destination_position() 
            
        pass

    
