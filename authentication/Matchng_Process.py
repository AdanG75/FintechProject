# -*- coding: utf-8 -*-

import numpy as np
import cv2 as cv
from math import degrees

class Matching_Process(object):
    def __init__(self, local_ratio_tolerance = .5, local_angle_tolerance = 1.5, matching_distance_tolerance = 1, matching_angle_tolerance = 1.5) -> None:
        super().__init__()
        self._local_ratio_tolerance = local_ratio_tolerance
        self._local_angle_tolerance = local_angle_tolerance
        self._matching_distance_tolerance = matching_distance_tolerance
        self._matching_angle_tolerance = matching_angle_tolerance

        self._base_minutiaes = []
        self._base_cores = []
        self._index_minutiaes = []
        self._index_cores = []
        self._possible_common_minutias =[]

    
    def matching(self, base_minutiaes_list, base_core_list, index_minutiaes_list, index_core_list):
        self._base_minutiaes = base_minutiaes_list.copy()
        self._base_cores = base_core_list.copy()
        self._index_minutiaes = index_minutiaes_list.copy()
        self._index_cores = index_core_list.copy()


    def __common_points(self):
        index_minutiaes_to_compare = [[index_minutia, False] for index_minutia in self._index_minutiaes]

        for base_minutiae in self._base_minutiaes:
            for index_minutia in index_minutiaes_to_compare:
                if (index_minutia[1]):
                    continue
                else:
                    local_base_minutiaes = base_minutiae.get_tuple_fingerprint_list()
                    local_index_minutiaes = index_minutia[0].get_tuple_fingerprint_list()
                    is_parent = self.__find_possible_minutia_parent(local_info_base_minutiae=local_base_minutiaes, local_info_index_minutia=local_index_minutiaes)
                    
                    if (is_parent):
                        index_minutia[1] = True
                        id_base_minutia = base_minutiae.get_minutiae_id()
                        self._possible_common_minutias.append([index_minutia[0], id_base_minutia])
                        break


    def __find_possible_minutia_parent(self, local_info_base_minutiae, local_info_index_minutia):
        count = 0
        for base_tuple in local_info_base_minutiae:
            for index_tuple in local_info_index_minutia:
                ratio_base = base_tuple.get_ratio()
                ratio_index = index_tuple.get_ratio()
                if (abs(ratio_base - ratio_index) <= self._local_ratio_tolerance):
                    angle_base = base_tuple.get_angle()
                    angle_index = index_tuple.get_angle()
                    if (abs(angle_base - angle_index) <= self._local_angle_tolerance):
                        origin_minutiae_base = base_tuple.get_origin_minutiae_type()
                        origin_minutiae_index = index_tuple.get_origin_minutiae_type()
                        destination_minutiae_base = base_tuple.get_destination_minutiae_type()
                        destination_minutiae_index = index_tuple.get_destination_minutiae_type()
                        if ((origin_minutiae_base == origin_minutiae_index) and (destination_minutiae_base == destination_minutiae_index )):
                            count += 1
                            break
                    else:
                        continue
                else:
                    continue
            
            if count >= 2:
                return True
                
        if count < 2:
            return False
        else:
            return True

