# -*- coding: utf-8 -*-

import cv2 as cv
from Error_Message import Error_Message

class Matching_Core(Error_Message):
    def __init__(self, distance_tolerance = 1, minimum_cores = 2) -> None:
        super().__init__()
        self._distance_tolerance = distance_tolerance
        self._minimum_cores = minimum_cores

        self._base_cores = []
        self._input_cores = []
    
    
    def __compute_translation(self, base_core, input_core):
        base_pos_x = base_core.get_posx()
        base_pos_y = base_core.get_posy()
        input_pos_x = input_core.get_posx()
        input_pos_y = input_core.get_posy()

        trans_x = base_pos_x - input_pos_x
        trans_y = base_pos_y - input_pos_y

        return (trans_x, trans_y)
    
    
    def __set_dictionary_key(self, trans_x, trans_y):
        return (str(trans_x) + '-' + str(trans_y))


    def __obtain_possible_align_value(self):
        possibles_align_values = {}
        
        for input_core in self._input_cores:
            for base_core in self._base_cores:
                if base_core.get_point_type() == input_core.get_point_type():
                    trans_x, trans_y = self.__compute_translation(base_core, input_core)
                    key = self.__set_dictionary_key(trans_x, trans_y)
                    try:
                        possibles_align_values[key]
                    except KeyError:
                        possibles_align_values.update( {key : [trans_x, trans_y]} )

        return possibles_align_values


    
    def matching_core(self, base_fingerprint, input_fingerprint):
        self._base_cores = base_fingerprint.get_core_point_list()
        self._input_cores = input_fingerprint.get_core_point_list()

        if (self._base_cores < self._minimum_cores) or (self._input_cores < self._minimum_cores):
            return self._DONT_MATCH_FINGERPRINT

        possibles_align_values = self.__obtain_possible_align_value()
        