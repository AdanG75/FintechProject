# -*- coding: utf-8 -*-

import numpy as np
from math import sqrt

from fingerprint_process.utils.error_message import ErrorMessage


class MatchingProcess(ErrorMessage):
    def __init__(
            self,
            local_ratio_tolerance=.5,
            local_angle_tolerance=1.5,
            matching_distance_tolerance=1,
            matching_angle_tolerance=1.5,
            area_tolerance=60,
            minimun_fingerprint_score=2,
            minimum_core_score=2
    ) -> None:
        super().__init__()
        self._local_ratio_tolerance = local_ratio_tolerance
        self._local_angle_tolerance = local_angle_tolerance
        self._matching_distance_tolerance = matching_distance_tolerance
        self._matching_angle_tolerance = matching_angle_tolerance
        self._area_tolerance = area_tolerance

        self._base_minutiaes = []
        self._base_cores = []
        self._index_minutiaes = []
        self._index_cores = []
        self._possible_common_minutias = []
        self._aligned_base_minutiaes = []

        self._MINIMUM_ANGLE = 0
        self._MAXIMUM_ANGLE = 360
        self._MINIMUM_CORE_SCORE = minimum_core_score
        self._FINGERPRINT_SCORE = minimun_fingerprint_score

    def matching(self, base_fingerprint, index_fingerprint):

        self.__get_lists_of_characteristic_points(base_fingerprint=base_fingerprint,
                                                  index_fingerprint=index_fingerprint)
        self.__common_points()
        self.__are_void_possible_common_minutias_list()

        ############################ Debug ######################################
        base_fingerprint.show_characteristic_point_from_list(type_characteristic_point='minutia')
        base_fingerprint.show_characteristic_point_from_list(type_characteristic_point='core')
        index_fingerprint.show_characteristic_point_from_list(type_characteristic_point='minutia')
        index_fingerprint.show_characteristic_point_from_list(type_characteristic_point='core')
        self.__see_common_points()

        result_matching = self.__match_fingerprint()
        return result_matching

    def __get_lists_of_characteristic_points(self, base_fingerprint, index_fingerprint):
        self._base_cores = base_fingerprint.get_core_point_list()
        self._base_minutiaes = base_fingerprint.get_minutiae_list()
        self._index_cores = index_fingerprint.get_core_point_list()
        self._index_minutiaes = index_fingerprint.get_minutiae_list()

    def __see_common_points(self):
        for common_point in self._possible_common_minutias:
            print(common_point[0].get_description(), common_point[1])

        print(len(self._possible_common_minutias))

    def __are_void_possible_common_minutias_list(self):
        if len(self._possible_common_minutias) <= 0:
            return self._DONT_MATCH_FINGERPRINT

    def __common_points(self):
        index_minutiaes_to_compare = [[index_minutia, False] for index_minutia in self._index_minutiaes]

        for base_minutiae in self._base_minutiaes:
            for index_minutia in index_minutiaes_to_compare:
                if (index_minutia[1]):
                    continue
                else:
                    local_base_minutiaes = base_minutiae.get_tuple_fingerprint_list()
                    local_index_minutiaes = index_minutia[0].get_tuple_fingerprint_list()
                    is_parent = self.__find_possible_minutia_parent(local_info_base_minutiae=local_base_minutiaes,
                                                                    local_info_index_minutia=local_index_minutiaes)

                    if (is_parent):
                        if (base_minutiae.get_point_type() == index_minutia[0].get_point_type()):
                            index_minutia[1] = True
                            id_base_minutia = base_minutiae.get_minutiae_id()
                            self._possible_common_minutias.append([index_minutia[0], id_base_minutia])
                            break
                        else:
                            continue

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
                        if ((origin_minutiae_base == origin_minutiae_index) and (
                                destination_minutiae_base == destination_minutiae_index)):
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
            fingerprint_score = 0
            for common_minutiae in self._possible_common_minutias:
                minutiae_found = self.__find_minutiae_to_align(common_minutiae=common_minutiae)
                validation = self.__validate_minutiae_to_align(minutiae_found=minutiae_found)
                if validation:
                    alignment_matrix = self.__create_alignment_matrix(common_minutiae=common_minutiae,
                                                                      minutiae_found=minutiae_found)
                    (aligned_base_minutiaes, translation_x, translation_y,
                     angle_translation) = self.__align_fingerprints(alignment_matrix, common_minutiae, minutiae_found)
                    base_id = minutiae_found.get_minutiae_id()
                    reference_minutiae = self.__set_reference_point(base_id=base_id,
                                                                    aligned_base_minutiaes=aligned_base_minutiaes)

                    ############################ Debug ######################################
                    print(reference_minutiae)
                    print(common_minutiae[0].get_description())

                    fingerprint_score = self.__match_score(reference_minutiae=reference_minutiae,
                                                           aligned_base_minutiaes=aligned_base_minutiaes,
                                                           alignment_matrix=alignment_matrix,
                                                           translation_x=translation_x, translation_y=translation_y,
                                                           angle_translation=angle_translation)
                else:
                    continue

                if fingerprint_score >= self._FINGERPRINT_SCORE:
                    return self._MATCH_FINGERPRINT

        return self._DONT_MATCH_FINGERPRINT

    def __match_score(self, reference_minutiae, aligned_base_minutiaes, alignment_matrix, translation_x, translation_y,
                      angle_translation):
        ref_pos_y = reference_minutiae[1]
        ref_pos_x = reference_minutiae[2]
        match_fingerprint_score = 0
        correspondence_score = 0

        for aligned_base_minutiae in aligned_base_minutiaes:
            correspondence_score += self.__correspondence_point(aligned_base_point=aligned_base_minutiae,
                                                                ref_pos_y=ref_pos_y, ref_pos_x=ref_pos_x,
                                                                point_type='minutiae', origin='index')

        match_result = self.__check_score(score=correspondence_score)

        if match_result:
            match_fingerprint_score += 1

            correspondence_core = self.__match_core_score(alignment_matrix, translation_x, translation_y,
                                                          angle_translation, ref_pos_y, ref_pos_x)

            if correspondence_core:
                match_fingerprint_score += 1

        if match_fingerprint_score >= self._FINGERPRINT_SCORE:
            return match_fingerprint_score

        ############################ Debug ######################################
        print(match_fingerprint_score)

        return match_fingerprint_score

    def __match_core_score(self, alignment_matrix, translation_x, translation_y, angle_translation, ref_pos_y,
                           ref_pos_x):
        correspondence_core = 0
        match_core_result = False
        void_core_lists = self.__is_it_void_core_list()

        if (not void_core_lists):
            aligned_base_cores = self.__align_base_points(aligment_matrix=alignment_matrix, translation_x=translation_x,
                                                          translation_y=translation_y,
                                                          angle_translation=angle_translation, point_type='core',
                                                          origin='base')

            for core_point in aligned_base_cores:
                correspondence_core += self.__correspondence_point(aligned_base_point=core_point, ref_pos_y=ref_pos_y,
                                                                   ref_pos_x=ref_pos_x,
                                                                   point_type='core', origin='index')

            match_core_result = self.__check_core_score(correspondence_core=correspondence_core)

        return match_core_result

    def __check_core_score(self, correspondence_core):
        if correspondence_core >= self._MINIMUM_CORE_SCORE:
            return True
        else:
            return False

    def __correspondence_point(self, aligned_base_point, ref_pos_y, ref_pos_x, point_type, origin):

        pos_y = aligned_base_point[1]
        pos_x = aligned_base_point[2]
        euclidian_distance = self.__euclidian_distance(pos_y=pos_y, ref_pos_y=ref_pos_y, pos_x=pos_x,
                                                       ref_pos_x=ref_pos_x)
        (distance_tolerance, angle_tolerance) = self.__set_value_tolerance_for_region(
            euclidian_distance=euclidian_distance)
        is_correspondence = self.__find_correspondence_point(aligned_base_point=aligned_base_point,
                                                             distance_tolerance=distance_tolerance,
                                                             angle_tolerance=angle_tolerance, point_type=point_type,
                                                             origin=origin)

        if is_correspondence:
            return 1
        else:
            return 0

    def __is_it_void_core_list(self):
        void_index_core_list = (len(self._index_cores) <= 0)
        void_base_core_list = (len(self._base_cores) <= 0)

        if (void_base_core_list or void_index_core_list):
            return True
        else:
            return False

    def __check_score(self, score):
        minimum_score = (min(len(self._base_minutiaes), len(self._index_minutiaes)) / 2)
        if score >= minimum_score:
            return True
        else:
            return False

    def __find_correspondence_point(self, aligned_base_point, distance_tolerance, angle_tolerance, point_type, origin):
        # score = 0
        point_list = self.__select_point_type(point_type=point_type, origin=origin)
        ref_pos_y = aligned_base_point[1]
        ref_pos_x = aligned_base_point[2]

        for index_point in point_list:
            pos_y = index_point.get_posy()
            pos_x = index_point.get_posx()
            # its_inside_area = self.__check_distance_between_minutiaes(pos_y=pos_y, ref_pos_y=ref_pos_y, pos_x=pos_x, ref_pos_x=ref_pos_x, distance_tolerance=distance_tolerance)
            # if its_inside_area:
            euclidian_distance_between_minutiaes = self.__euclidian_distance(pos_y=pos_y, ref_pos_y=ref_pos_y,
                                                                             pos_x=pos_x, ref_pos_x=ref_pos_x)
            if (euclidian_distance_between_minutiaes <= distance_tolerance):
                ############################ Debug ######################################
                print('X-Y correspondance')

                same_minutiae = self.__is_it_the_same_minutiae(index_minutia=index_point,
                                                               aligned_base_minutiae=aligned_base_point,
                                                               angle_tolerance=angle_tolerance)
                if same_minutiae:
                    # score += 1
                    return True
                else:
                    continue
            else:
                continue
                # else:
            #     continue

        return False

    def __is_it_the_same_minutiae(self, index_minutia, aligned_base_minutiae, angle_tolerance):
        # index_angle = index_minutia.get_angle()
        # base_angle = aligned_base_minutiae[3]
        # correspondence_angle = self.__check_correspondence_angle(index_angle=index_angle, base_angle=base_angle, angle_tolerance=angle_tolerance)
        # if correspondence_angle:
        #     index_type = index_minutia.get_point_type()
        #     base_type = aligned_base_minutiae[4]
        #     if (index_type == base_type):
        #         return True
        # else:
        #     return False

        # Only checked figerprint's type
        index_type = index_minutia.get_point_type()
        base_type = aligned_base_minutiae[4]

        if (index_type == base_type):
            return True

        return False

    def __check_correspondence_angle(self, index_angle, base_angle, angle_tolerance):
        subtraction_between_angles = abs(index_angle - base_angle)
        less_than_angle_tolerance = (
                    min(subtraction_between_angles, (360 - subtraction_between_angles)) <= angle_tolerance)

        return less_than_angle_tolerance

    def __check_distance_between_minutiaes(self, pos_y, ref_pos_y, pos_x, ref_pos_x, distance_tolerance):
        less_than_distance_tolerance_in_y = (abs(pos_y - ref_pos_y) <= distance_tolerance)
        less_than_distance_tolerance_in_x = (abs(pos_x - ref_pos_x) <= distance_tolerance)

        return (less_than_distance_tolerance_in_y and less_than_distance_tolerance_in_x)

    def __euclidian_distance(self, pos_y, ref_pos_y, pos_x, ref_pos_x):
        euclidian_distance = sqrt(pow((pos_y - ref_pos_y), 2) + pow((pos_x - ref_pos_x), 2))

        return euclidian_distance

    def __set_value_tolerance_for_region(self, euclidian_distance):
        distance_tolerance = ((1 + (euclidian_distance // self._area_tolerance)) * self._matching_distance_tolerance)
        angle_tolerance = ((1 + (euclidian_distance // self._area_tolerance)) * self._matching_angle_tolerance)

        return (distance_tolerance, angle_tolerance)

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

    def __create_alignment_matrix(self, common_minutiae, minutiae_found):
        # theta = radians(common_minutiae[0].get_angle() - minutiae_found.get_angle())

        ############################ Debug ######################################
        # print(theta)

        # alignment_matrix = np.matrix([[cos(theta), (-1)*sin(theta)],
        #                     [sin(theta), cos(theta)]])

        # return alignment_matrix

        # returned default alignment_matrix
        return np.matrix([[1, 1], [1, 1]])

    def __align_fingerprints(self, alignment_matrix, common_minutiae, minutiae_found):
        (base_id, pos_y, pos_x, base_angle, base_type) = minutiae_found.get_description()

        rotate_position = self.__compute_rotate_position(alignment_matrix=alignment_matrix, pos_y=pos_y, pos_x=pos_x)

        (translation_x, translation_y) = self.__compute_translation(rotate_position=rotate_position,
                                                                    common_minutiae=common_minutiae)
        angle_translation = self.__compute_angle_translation(base_angle=base_angle, common_minutiae=common_minutiae)
        aligned_base_minutiaes = self.__align_base_points(aligment_matrix=alignment_matrix, translation_x=translation_x,
                                                          translation_y=translation_y,
                                                          angle_translation=angle_translation,
                                                          point_type='minutiae', origin='base')
        return (aligned_base_minutiaes, translation_x, translation_y, angle_translation)

    def __set_reference_point(self, base_id, aligned_base_minutiaes):
        for aligned_base_minutiae in aligned_base_minutiaes:
            if aligned_base_minutiae[0] == base_id:
                return aligned_base_minutiae

    def __align_base_points(self, aligment_matrix, translation_x, translation_y, angle_translation, point_type, origin):
        aligned_base_points = []
        translation_matrix = self.__ubication_as_matrix(pos_x=translation_x, pos_y=translation_y)
        point_list = self.__select_point_type(point_type=point_type, origin=origin)

        for base_point in point_list:
            (base_id, pos_y, pos_x, base_angle, base_type) = base_point.get_description()
            rotate_position = self.__compute_rotate_position(alignment_matrix=aligment_matrix, pos_y=pos_y, pos_x=pos_x)
            displaced_position = self.__compute_displaced_minutiae(rotate_position=rotate_position,
                                                                   translation_matrix=translation_matrix)
            displaced_angle = self.__compute_displaced_angle_minutiae(base_angle=base_angle,
                                                                      angle_translation=angle_translation)
            aligned_base_points.append(
                [base_id, displaced_position[1][0], displaced_position[0][0], displaced_angle, base_type])

        return aligned_base_points

    def __select_point_type(self, point_type, origin):
        if origin == 'base':
            if point_type == 'minutiae':
                point_list = self._base_minutiaes.copy()
            elif point_type == 'core':
                point_list = self._base_cores.copy()
            else:
                point_list = self._base_minutiaes.copy()
        elif origin == 'index':
            if point_type == 'minutiae':
                point_list = self._index_minutiaes.copy()
            elif point_type == 'core':
                point_list = self._index_cores.copy()
            else:
                point_list = self._index_minutiaes.copy()
        else:
            point_list = self._index_cores.copy()

        return point_list

    def __compute_displaced_minutiae(self, rotate_position, translation_matrix):
        return (rotate_position + translation_matrix).round()

    def __compute_displaced_angle_minutiae(self, base_angle, angle_translation):
        # displaced_angle = (base_angle + angle_translation)
        # checked_displaced_angle = self.__check_angle(angle_translation=displaced_angle)

        # return checked_displaced_angle

        # returned base_angje without translation
        return base_angle

    def __compute_rotate_position(self, alignment_matrix, pos_y, pos_x):
        original_position = self.__ubication_as_matrix(pos_y=pos_y, pos_x=pos_x)
        # rotate_position = np.matmul(alignment_matrix, original_position)

        ############################ Debug ######################################
        # print(f'Original position {original_position}')
        # print(f'Rotate position {rotate_position}')

        # return rotate_position

        # returned pisition without rotatement
        return original_position

    def __ubication_as_matrix(self, pos_y, pos_x):
        return np.matrix([[pos_x], [pos_y]])

    def __compute_translation(self, rotate_position, common_minutiae):
        dimention = len(rotate_position.shape)
        integer_rotate_position = self.__integer_position(dimention, rotate_position)
        # (index_id, index_pos_y, index_pos_x, index_angle, index_type) = common_minutiae[0].get_description()
        index_pos_y = common_minutiae[0].get_posy()
        index_pos_x = common_minutiae[0].get_posx()

        if (len(integer_rotate_position.shape) < 2):
            translation_x = index_pos_x - integer_rotate_position[0]
            translation_y = index_pos_y - integer_rotate_position[1]
        else:
            translation_x = index_pos_x - integer_rotate_position[0][0]
            translation_y = index_pos_y - integer_rotate_position[1][0]

        ############################ Debug ######################################
        print('X: {}, Y: {}'.format(translation_x, translation_y))

        return (translation_x, translation_y)

    def __compute_angle_translation(self, base_angle, common_minutiae):
        index_angle = common_minutiae[0].get_angle()
        angle_translation = index_angle - base_angle

        checked_angle_translation = self.__check_angle(angle_translation=angle_translation)

        return checked_angle_translation

    def __check_angle(self, angle_translation):
        if angle_translation < self._MINIMUM_ANGLE:
            while (angle_translation < self._MINIMUM_ANGLE):
                angle_translation = self._MAXIMUM_ANGLE + angle_translation
        elif angle_translation > self._MAXIMUM_ANGLE:
            while (angle_translation > self._MAXIMUM_ANGLE):
                angle_translation = angle_translation - self._MAXIMUM_ANGLE
        else:
            return angle_translation

        return round(angle_translation, 2)

    def __integer_position(self, dimention, rotate_position):
        integer_rotate_position = np.zeros(shape=(rotate_position.shape), dtype='int16')
        pos_column = 0
        if (dimention >= 2):
            pos_row = 0
            for row in rotate_position:
                for value in row:
                    integer_rotate_position[pos_row][pos_column] = value.round()
                    pos_column += 1

                pos_row += 1
                pos_column = 0
        else:
            for value in rotate_position:
                integer_rotate_position[pos_column] = value.round()
                pos_column += 1

        return integer_rotate_position

