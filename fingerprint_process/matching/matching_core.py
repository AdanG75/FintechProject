# -*- coding: utf-8 -*-

import numpy as np

from fingerprint_process.utils.error_message import ErrorMessage


class MatchingCore(ErrorMessage):
    def __init__(self, distance_tolerance=1, minimum_cores=2,
                 neighborhood_area=40) -> None:
        super().__init__()
        self._distance_tolerance = distance_tolerance
        self._minimum_cores = minimum_cores
        self._neighborhood_area = neighborhood_area

        self._base_cores = []
        self._input_cores = []
        self._base_minutiaes = []
        self._input_minutiaes = []

    def __compute_translation(self, base_core, input_core):
        base_pos_x = base_core.get_posx()
        base_pos_y = base_core.get_posy()
        input_pos_x = input_core.get_posx()
        input_pos_y = input_core.get_posy()

        trans_x = base_pos_x - input_pos_x
        trans_y = base_pos_y - input_pos_y

        return (trans_x, trans_y, base_pos_x, base_pos_y)

    def __set_dictionary_key(self, trans_x, trans_y):
        return (str(trans_x) + '-' + str(trans_y))

    def __obtain_possible_align_value(self):
        possibles_align_values = {}

        for input_core in self._input_cores:
            for base_core in self._base_cores:
                if base_core.get_point_type() == input_core.get_point_type():
                    trans_x, trans_y, base_pos_x, base_pos_y = self.__compute_translation(base_core, input_core)
                    key = self.__set_dictionary_key(trans_x, trans_y)
                    try:
                        possibles_align_values[key]
                    except KeyError:
                        possibles_align_values.update({key: (trans_x, trans_y, base_pos_x, base_pos_y)})

        return possibles_align_values

    def __check_match(self, map_tuple, base_point, tolerance):
        pos_x = base_point.get_posx()
        pos_y = base_point.get_posy()
        c_type = base_point.get_point_type()

        is_x_ok = abs(pos_x - map_tuple[0]) <= tolerance
        is_y_ok = abs(pos_y - map_tuple[1]) <= tolerance
        is_type_ok = c_type == map_tuple[2]

        return is_x_ok and is_y_ok and is_type_ok

    def __align_cores(self, possibles_align_values):
        map_input_cores = []
        align_values = []

        for translation in possibles_align_values.values():
            for input_core in self._input_cores:
                pos_x = (input_core.get_posx() + translation[0])
                pos_y = (input_core.get_posy() + translation[1])
                c_type = input_core.get_point_type()

                map_input_cores.append((pos_x, pos_y, c_type))

            count = 0
            for map_tuple in map_input_cores:
                for base_core in self._base_cores:
                    if self.__check_match(map_tuple, base_core, 0):
                        count += 1
                        break

            if count >= self._minimum_cores:
                align_values.append(translation)

            map_input_cores.clear()

        return align_values

    def __euclidean_distance(self, origin_y_pos, origin_x_pos, destination_y_pos, destination_x_pos):
        return np.sqrt((destination_y_pos - origin_y_pos) ** 2 + (destination_x_pos - origin_x_pos) ** 2)

    def __compute_tolerance(self, distance):
        return ((distance // self._neighborhood_area) + 1) * self._distance_tolerance

    def __are_match(self, score):
        minimum_score = max(len(self._base_minutiaes), len(self._input_minutiaes)) // 2

        return score >= minimum_score

    def __align_minutiaes(self, align_values):
        map_input_minutiaes = []

        for translation in align_values:
            for input_minutiae in self._input_minutiaes:
                pos_x = (input_minutiae.get_posx() + translation[0])
                pos_y = (input_minutiae.get_posy() + translation[1])
                c_type = input_minutiae.get_point_type()

                map_input_minutiaes.append((pos_x, pos_y, c_type))

            count = 0
            for map_tuple in map_input_minutiaes:
                for base_minutiae in self._base_minutiaes:
                    pos_x = base_minutiae.get_posx()
                    pos_y = base_minutiae.get_posy()
                    c_type = base_minutiae.get_point_type()
                    distance = self.__euclidean_distance(translation[3], translation[2], pos_y, pos_x)
                    tolerance = self.__compute_tolerance(distance)
                    if self.__check_match(map_tuple, base_minutiae, tolerance):
                        count += 1
                        break

            if self.__are_match(count):
                return self._MATCH_FINGERPRINT

        return self._DONT_MATCH_FINGERPRINT

    def matching(self, base_fingerprint, input_fingerprint):
        self._base_cores = base_fingerprint.get_core_point_list()
        self._input_cores = input_fingerprint.get_core_point_list()
        if (len(self._base_cores) < self._minimum_cores) or (len(self._input_cores) < self._minimum_cores):
            return self._DONT_MATCH_FINGERPRINT

        possibles_align_values = self.__obtain_possible_align_value()
        if len(possibles_align_values) <= 0:
            return self._DONT_MATCH_FINGERPRINT

        align_values = self.__align_cores(possibles_align_values)
        if len(align_values) <= 0:
            return self._DONT_MATCH_FINGERPRINT

        self._base_minutiaes = base_fingerprint.get_minutiae_list()
        self._input_minutiaes = input_fingerprint.get_minutiae_list()

        result = self.__align_minutiaes(align_values)

        return result
