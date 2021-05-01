# -*- coding: utf-8 -*-

import numpy as np
import cv2 as cv
from math import degrees, cos, sin
from numpy.core.defchararray import index

from numpy.core.fromnumeric import shape

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

        self.__common_points()


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
                else:
                    continue
            
            if count >= 2:
                return True
                
        if count < 2:
            return False
        else:
            return True

    
    def __match_fingerprint(self):
        if len(self._possible_common_minutias) <= 0:
            return False
        else:
            for common_minutiae in self._possible_common_minutias:
                minutiae_found = self.__find_minutiae_to_align(common_minutiae=common_minutiae)
                validation = self.__validate_minutiae_to_align(minutiae_found=minutiae_found)
                if validation:
                    alignment_matrix = self.__create_alignment_matrix(common_minutiae=common_minutiae)

                else:
                    continue

    
    def __find_minutiae_to_align(self, common_minutiae):
        for base_minutiae in self._base_minutiaes:
            if (common_minutiae[1] == base_minutiae.get_minutiae_id()):
                return base_minutiae
        
        return False

    
    def __validate_minutiae_to_align(self, minutiae_found):
        if minutiae_found == False:
            return False
        else:
            return True


    def __create_alignment_matrix(self, common_minutiae):
        theta = common_minutiae.get_angle()
        alignment_matrix = np.matrix([[degrees(cos(theta)), degrees((-1)*sin(theta))],
                            [degrees(sin(theta)), degrees(cos(theta))]])
        
        return alignment_matrix

    
    def __align_fingerprints(self, alignment_matrix, common_minutiae, minutiae_found):
        (base_id, pos_y, pos_x, base_angle, base_type) = minutiae_found.get_short_descrption()
        original_position =np.matrix([[pos_x],
                                    [pos_y]])

        rotate_position = np.matmul(alignment_matrix, original_position)
        (translation_x, translation_y) = self.__compute_translation(rotate_position=rotate_position, common_minutiae=common_minutiae)

    
    def __compute_translation(self, rotate_position, common_minutiae):
        dimention = len(rotate_position.shape)
        integer_rotate_position = self.__integer_position(dimention, rotate_position)
        # (index_id, index_pos_y, index_pos_x, index_angle, index_type) = common_minutiae[0].get_short_descrption()
        index_pos_y = common_minutiae[0].get_posy()
        index_pos_x = common_minutiae[0].get_posx()
        
        if (len(integer_rotate_position.shape) < 2):
            translation_x = index_pos_x - integer_rotate_position[0]
            translation_y = index_pos_y - integer_rotate_position[1]
        else:
            translation_x = index_pos_x - integer_rotate_position[0][0]
            translation_y = index_pos_y - integer_rotate_position[1][0]

        return (translation_x, translation_y)

        


    def __integer_position(self, dimention, rotate_position):
        integer_rotate_position = np.zeros(shape=(rotate_position.shape), dtype='int16')
        pos_column = 0
        if (dimention >= 2):
            pos_row = 0
            for row in rotate_position:
                for value in row:
                    integer_rotate_position[pos_row][pos_column] = round(value)
                    pos_column +=1
                
                pos_row += 1
                pos_column = 0
        else:
            for value in rotate_position:
                integer_rotate_position[pos_column] = round(value)
                pos_column +=1

        return integer_rotate_position

