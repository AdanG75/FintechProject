# -*- coding: utf-8 -*-
from math import ceil, floor
import uuid
import numpy as np
from Minutia import Minutiae

class Local_Area(object):
    def __init__(self, list_minutiaes, max_distance = 1500, number_neighbordings = 5) -> None:
        super().__init__()
        self._list_minutiaes = list_minutiaes
        self._max_distance = max_distance
        self._number_neighbordings = number_neighbordings

    def __nearest_minutiaes(self):
        nearest_distances = [self._max_distance for _ in range(self._number_neighbordings)]
        length_list = len(self._list_minutiaes)
        if length_list > self._number_neighbordings:
            begin = 0
            end = (self._number_neighbordings - 1)
            neighbording_minutiaes = [self._list_minutiaes[index] for index in range(self._number_neighbordings)]

            for reference in range(length_list):
                minutiae = self._list_minutiaes[reference]
                j = minutiae.get_posy()
                i = minutiae.get_posx()

                for index in range(length_list):
                    if (index != reference):
                        neighbording_minutia = self._list_minutiaes[index]
                        j2 = neighbording_minutia.get_posy()
                        i2 = neighbording_minutia.get_posx()
                        
                        distance = round(self.__euclidian_distance(j, j2, i, i2), 2)

                        (distance_flag, position) = self.__get_nearby_points(nearest_distances, distance, begin, end, 'equal')
                        if distance_flag:
                            nearest_distances[position] = distance
                            neighbording_minutiaes[position] = neighbording_minutia
                    else:
                        continue
        
        return neighbording_minutiaes

    def __euclidian_distance(self, j1, j2, i1, i2):
        return (np.sqrt(np.power((j2 - j1), 2) + np.power((i2 - i1), 2)))

    def __get_nearby_points(self, distance_list, distance, begin, end, movement='equal'):
        if movement == 'up':
            middle = ceil((begin + end) / 2)
            if middle == end:
                if distance >= distance_list[middle]:
                    return (False, 0)
                else:
                    return (True, middle)
        else:
            middle = floor((begin + end) / 2)
            if middle == begin:
                if distance >= distance_list[middle]:
                    return (True, end)
                else:
                    return (True, middle) 
        
        if distance > distance_list[middle]:
            return self.__get_nearby_points(distance_list, distance, middle, end, movement='up')
        else:
            return self.__get_nearby_points(distance_list, distance, begin, middle, movement='down')

            
    def get_local_structure(self):
        neighbording_minutiaes = self.__nearest_minutiaes()
        pass

    