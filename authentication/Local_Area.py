# -*- coding: utf-8 -*-
import uuid
import numpy as np
from Minutia import Minutiae

class Local_Area(object):
    def __init__(self, list_minutiaes, max_distance = 1500, number_neibordhoods = 5) -> None:
        super().__init__()
        self._list_minutiaes = list_minutiaes
        self._max_distance = max_distance
        self._number_neighbordhoods = number_neibordhoods

    def __nearest_minutiaes(self):
        nearest_distance = [self._max_distance for _ in range(self._number_neighbordhoods)]
        length_list = len(self._list_minutiaes)
        if length_list > self._number_neighbordhoods:
            neighbording_minutiaes = [self._list_minutiaes[index] for index in range(self._number_neighbordhoods)]
            for reference in range(length_list):
                minutiae = self._list_minutiaes[reference]
                j = minutiae.get_posy()
                i = minutiae.get_posx()

                
                for index in range(self._number_neighbordhoods):
                    if (index != reference):
                        neighbording_minutia = self._list_minutiaes[index]
                        j2 = neighbording_minutia.get_posy()
                        i2 = neighbording_minutia.get_posx()
                        
                        distance = round(self.__euclidian_distance(j, j2, i, i2), 2)
                        if nearest_distance[index] > distance:
                            neighbording_minutiaes[index] = minutiae







    def __euclidian_distance(self, j1, j2, i1, i2):
        return (np.sqrt(np.power((j2 - j1), 2) + np.power((i2 - i1), 2)))
            
    def get_local_structure(self):
        pass

    