# -*- coding: utf-8 -*-
from math import ceil, floor, factorial, atan, degrees
import uuid
import numpy as np
from Minutia import Minutiae
from Tuple_Fingerprint import Tuple_Fingerprint
from Error_Message import Error_Message

class Local_Area(Error_Message):
    def __init__(self, max_distance = 1500, number_neighbordings = 5, angles_tolerance = 0.01) -> None:
        super().__init__()
        self._max_distance = max_distance
        self._number_neighbordings = number_neighbordings
        self._angles_tolerance = angles_tolerance

        self._begin = 0
        self._end = (self._number_neighbordings - 1)
        self._tuple_length = self.__tuple_length()

        self._list_minutiaes = []


    def __nearest_minutiaes(self, length_list, reference = 0):
        #nearest_distances = [self._max_distance for _ in range(self._number_neighbordings)]
        neighbording_minutiaes = [[self._list_minutiaes[index], self._max_distance] for index in range(self._number_neighbordings)]

        minutiae = self._list_minutiaes[reference]
        j = minutiae.get_posy()
        i = minutiae.get_posx()

        for index in range(length_list):
            if (index != reference):
                neighbording_minutia = self._list_minutiaes[index]
                j2 = neighbording_minutia.get_posy()
                i2 = neighbording_minutia.get_posx()
                
                distance = round(self.__euclidian_distance(j, j2, i, i2), 2)

                if self._number_neighbordings > 15:
                    (distance_flag, position) = self.__get_nearby_points(neighbording_minutiaes, distance, self._begin, self._end, 'equal')
                else:
                    (distance_flag, position) = self.__simple_nearby_points(neighbording_minutiaes, distance)

                if distance_flag:
                    #nearest_distances[position] = distance
                    neighbording_minutiaes[position][0] = neighbording_minutia
                    neighbording_minutiaes[position][1] = distance
            else:
                continue
        
        return neighbording_minutiaes


    def __euclidian_distance(self, j1, j2, i1, i2):
        return (np.sqrt(np.power((j2 - j1), 2) + np.power((i2 - i1), 2)))

    def __get_nearby_points(self, neighbording_list, distance, begin, end, movement='equal'):
        if movement == 'up':
            middle = ceil((begin + end) / 2)
            if middle == end:
                if distance >= neighbording_list[middle][1]:
                    return (False, 0)
                else:
                    return (True, middle)
        else:
            middle = floor((begin + end) / 2)
            if middle == begin:
                if distance >= neighbording_list[middle][1]:
                    return (True, end)
                else:
                    return (True, middle) 
        
        if distance > neighbording_list[middle][1]:
            return self.__get_nearby_points(neighbording_list, distance, middle, end, movement='up')
        else:
            return self.__get_nearby_points(neighbording_list, distance, begin, middle, movement='down')

    def __simple_nearby_points(self, neighbording_list, distance):
        if neighbording_list[self._end][1] < distance:
            return (False, 0)
        else:
            for index in range((self._end)):
                if neighbording_list[index][1] > distance:
                    return (True, index)
                    
            return (True, self._end)


    def __ratios_and_angles(self, neighbording_minutiaes, minutiae_reference):
        ratios_and_angles = [[0, 0, 'x', 'x'] for _ in range(self._tuple_length)]
        begin = (self._begin + 1)
        end = (self._end + 1)
        reference = 0
        RATIO_POSITION = 0
        ANGLE_POSITION = 1
        y_position = 0
        while(reference < (self._tuple_length - 1)):
            for second in range(begin, end, 1) :
                ratios_and_angles[y_position][RATIO_POSITION] = self.__get_ratio(reference, second, neighbording_minutiaes)
                ratios_and_angles[y_position][ANGLE_POSITION:] = self.__angles_minutiaes(minutiae_reference, neighbording_minutiaes, first=reference, second=second)
                y_position += 1
            reference += 1
            begin += 1 

        return ratios_and_angles


    def __get_ratio(self, reference, second, neighbording_minutiaes):
        ratio = round((max(neighbording_minutiaes[reference][1], neighbording_minutiaes[second][1])) / (min(neighbording_minutiaes[reference][1], neighbording_minutiaes[second][1])), 2)
        return ratio


    def __angles_minutiaes(self, minutiae_reference, neighbording_minutiaes, first, second):
            m = [0, 0, 0]
            angles = [[0, False], [0, False], [0, False]]
            j = minutiae_reference.get_posy()
            i = minutiae_reference.get_posx()

            first_minutiae = neighbording_minutiaes[first][0]
            j1 = first_minutiae.get_posy()
            i1 = first_minutiae.get_posx()
            minutiae_type1 = first_minutiae.get_point_type()

            second_minutiae = neighbording_minutiaes[second][0]
            j2 = second_minutiae.get_posy()
            i2 = second_minutiae.get_posx()
            minutiae_type2 = second_minutiae.get_point_type()

            points_triangle = ((j,i), (j1, i1), (j2, j1))
            number_slopes = len(m)
            begin = (self._begin + 1)
            reference = 0
            y_position = 0
            while (reference < (number_slopes - 1)):
                for position in range(begin, number_slopes, 1):
                    m[y_position] = self.__straight_slope(y1=points_triangle[reference][0], x1=points_triangle[reference][1], y2=points_triangle[position][0], x2=points_triangle[position][1])
                    y_position += 1
                reference += 1
                begin += 1 

            begin = (self._begin + 1)
            reference = 0
            y_position = 0
            while (reference < (number_slopes - 1)):
                for position in range(begin, number_slopes, 1):
                    angles[y_position][:] = self.__get_angle(m1=m[reference], m2=m[position])
                    y_position += 1
                reference += 1
                begin += 1 

            checked_angle = self.__check_angles(angles)
            return (checked_angle, minutiae_type1, minutiae_type2)



    def __straight_slope(self, y1, x1, y2, x2):
        if (x1 == x2):
            return 0
        else:
            return ((y2 - y1)/(x2 - x1))

    def __get_angle(self, m1, m2):
        if ((m1 * m2) == (-1)):
            return (90, True)
        else:
            return (abs(degrees(atan((m2 - m1)/(1 + (m1 * m2))))), False)

    def __check_angles(self, angles):
        sum_angles = 0
        possible_error = 0
        for position in range(len(angles)):
            sum_angles += angles[position][0]
            if angles[position][1] == True:
                possible_error = position

        if ((sum_angles < (180 - self._angles_tolerance)) or (sum_angles > (180 + self._angles_tolerance))):
            angles[possible_error][0] = (180 - (sum_angles - angles[possible_error][0]))

        checked_angle = round(angles[0][0], 2)

        return checked_angle


    def __tuple_length(self):
        return (factorial(self._number_neighbordings) // (factorial(2) * factorial(self._number_neighbordings - 2)))

    def __tuple_list(self, minutiae_reference, ratios_and_angles):
        # return [[0,0,0,0,0] for _ in range(self._tuple_length)]
        tuple_fingerprint_list = []
        minutiae_id = minutiae_reference.get_minutiae_id()
        for _ in range(self._tuple_length):
            (parameter_ratio, parameter_angle, parameter_type_first_minutiae, parameter_type_second_minutiae) = ratios_and_angles[_]
            my_tuple_fingerprint = Tuple_Fingerprint(minutiae_id, parameter_ratio, parameter_angle, parameter_type_first_minutiae, parameter_type_second_minutiae)
            tuple_fingerprint_list.append(my_tuple_fingerprint)

        return tuple_fingerprint_list

            
    def get_local_structure(self, list_minutiaes):
        self._list_minutiaes = list_minutiaes
        length_list = len(self._list_minutiaes)
        if length_list > self._number_neighbordings:
            for reference in range(length_list):
                minutiae_reference = self._list_minutiaes[reference]
                neighbording_minutiaes = self.__nearest_minutiaes(length_list, reference)
                ratios_and_angles = self.__ratios_and_angles(neighbording_minutiaes, minutiae_reference)
                tuple_fingerprint_list = self.__tuple_list(minutiae_reference, ratios_and_angles)
                minutiae_reference.set_tuple_fingerprint_list(tuple_fingerprint_list)

            return self._FINGERPRINT_OK
        else:
            return self._FEW_MINUTIAES
        

    