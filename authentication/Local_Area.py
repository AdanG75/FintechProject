# -*- coding: utf-8 -*-
from math import ceil, floor, factorial
import uuid
import numpy as np
from Minutia import Minutiae

class Local_Area(object):
    def __init__(self, list_minutiaes, max_distance = 1500, number_neighbordings = 5) -> None:
        super().__init__()
        self._list_minutiaes = list_minutiaes
        self._max_distance = max_distance
        self._number_neighbordings = number_neighbordings

        self._begin = 0
        self._end = (self._number_neighbordings - 1)
        self._tuple_length = self.__tuple_length()
        
        self._OK_TUPLE = 0
        self._FEW_MINUTIAES = 2

    def __nearest_minutiaes(self, length_list, reference = 0):
        #nearest_distances = [self._max_distance for _ in range(self._number_neighbordings)]
        neighbording_minutiaes = [(self._list_minutiaes[index], self._max_distance) for index in range(self._number_neighbordings)]

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
                    neighbording_minutiaes[position] = (neighbording_minutia, distance)
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

    def __ratios_minutiaes(self, neighbording_minutiaes):
        ratios = [0 for _ in range(self._tuple_length)]
        begin = (self._begin + 1)
        end = (self._end + 1)
        reference = 0
        ratio_position = 0
        while(reference < (self._tuple_length - 1)):
            for second in range(begin, end, 1) :
                ratios[ratio_position] = ((max(neighbording_minutiaes[reference][1], neighbording_minutiaes[second][1])) / (min(neighbording_minutiaes[reference][1], neighbording_minutiaes[second][1])))
                ratio_position += 1
            reference += 1
            begin += 1 

        return ratios

    def __angles_minutiaes(self):
        pass

    def __tuple_length(self):
        factorial(self._number_neighbordings) // (factorial(2) * factorial(self._number_neighbordings - 2))

    def __tuple_list(self):
        return [[0,0,0,0,0] for _ in range(self._tuple_length)]

            
    def get_local_structure(self):
        length_list = len(self._list_minutiaes)
        if length_list > self._number_neighbordings:
            tuple_list = self.__tuple_list()
            for reference in range(length_list):
                neighbording_minutiaes = self.__nearest_minutiaes(length_list, reference)
                ratios = self.__ratios_minutiaes(neighbording_minutiaes)
                angles = self.__angles_minutiaes()
        else:
            return self._FEW_MINUTIAES
        

    