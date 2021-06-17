# -*- coding: utf-8 -*-

import numpy as np
import cv2 as cv
from math import degrees, cos, sin, sqrt, radians
from operator import attrgetter
from Error_Message import Error_Message
from Edge import Edge

class Matching_Tree(Error_Message):
    def __init__(self, local_ratio_tolerance = .5, local_angle_tolerance = 1.5, 
                    matching_distance_tolerance = 5, matching_angle_tolerance = 1.5) -> None:
        super().__init__()
        self._local_ratio_tolerance = local_ratio_tolerance
        self._local_angle_tolerance = local_angle_tolerance
        self._matching_distance_tolerance = matching_distance_tolerance
        self._matching_angle_tolerance = matching_angle_tolerance

        self._base_minutiaes = []
        self._input_minutiaes = []
        self._possible_base_common_minutiaes = []
        self._possible_base_spurious_minutiaes = []
        self._possible_input_common_minutiaes = []
        self._possible_input_spurious_minutiaes = []
        self._fingerprint_score = 100

        self._MINIMUM_ANGLE = 0
        self._MAXIMUM_ANGLE = 360
        

    def __find_possible_minutia_parent(self, local_info_base_minutiae, local_info_input_minutia):
        count = 0
        for base_tuple in local_info_base_minutiae:
            for input_tuple in local_info_input_minutia:
                ratio_base = base_tuple.get_ratio()
                ratio_input = input_tuple.get_ratio()
                if (abs(ratio_base - ratio_input) <= self._local_ratio_tolerance):
                    angle_base = base_tuple.get_angle()
                    angle_input = input_tuple.get_angle()
                    if (abs(angle_base - angle_input) <= self._local_angle_tolerance):
                        origin_minutiae_base = base_tuple.get_origin_minutiae_type()
                        origin_minutiae_input = input_tuple.get_origin_minutiae_type()
                        destination_minutiae_base = base_tuple.get_destination_minutiae_type()
                        destination_minutiae_input = input_tuple.get_destination_minutiae_type()
                        if ((origin_minutiae_base == origin_minutiae_input) and (destination_minutiae_base == destination_minutiae_input )):
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

    
    def __common_points(self):
        input_minutiaes_to_compare = [{'minutiae': input_minutia, 'found': False} for input_minutia in self._input_minutiaes]

        for base_minutiae in self._base_minutiaes:
            is_spurious = True
            for input_minutia in input_minutiaes_to_compare:
                if (input_minutia['found']):
                    continue
                else:
                    local_base_minutiaes = base_minutiae.get_tuple_fingerprint_list()
                    local_input_minutiaes = input_minutia['minutiae'].get_tuple_fingerprint_list()
                    ###############Debug#################################
                    # is_bifurcation = (base_minutiae.get_point_type() == 'b')
                    # if is_bifurcation:
                    #     print('b')

                    is_parent = self.__find_possible_minutia_parent(local_info_base_minutiae=local_base_minutiaes, local_info_input_minutia=local_input_minutiaes)
                    
                    if (is_parent):
                        if (base_minutiae.get_point_type() == input_minutia['minutiae'].get_point_type()):
                            input_minutia['found'] = True
                            self._possible_base_common_minutiaes.append(base_minutiae)
                            self._possible_input_common_minutiaes.append(input_minutia['minutiae'])
                            is_spurious = False
                            break
                        else:
                            continue
                    else:
                        continue

            if is_spurious:
                self._possible_base_spurious_minutiaes.append(base_minutiae)

        for input_minutia in input_minutiaes_to_compare:
            if not input_minutia['found']:
                self._possible_input_spurious_minutiaes.append(input_minutia['minutiae'])
            

    def __get_lists_of_characteristic_points(self, base_fingerprint, input_fingerprint):
        self._base_minutiaes = base_fingerprint.get_minutiae_list()
        self._input_minutiaes = input_fingerprint.get_minutiae_list()


    def __see_common_and_spurious_points(self):
        to_show = [
            {'type': 'Common base', 'list': self._possible_base_common_minutiaes},
            {'type': 'Spurious base', 'list': self._possible_base_spurious_minutiaes},
            {'type': 'Common input', 'list': self._possible_input_common_minutiaes},
            {'type': 'Spurious input', 'list': self._possible_input_spurious_minutiaes}
        ]
        
        for item in to_show:
            print('\n{} points: '.format(item['type']))
            
            for point in item['list']:
                print('\t', point.get_description())

            print('Possible {} points found: {}'.format(item['type'], len(item['list'])))


    def __are_void_possible_common_minutias_list(self):
        if (len(self._possible_base_common_minutiaes) <= 0) or (len(self._possible_input_common_minutiaes) <= 0):
            return self._DONT_MATCH_FINGERPRINT


    def __mark_characteristic_point(self, fingerprint, list_minutiaes, name='fingerprint'):   
        colors = {'e' : (150, 0, 0), 'b' : (0, 150, 0)}
        
        fingerprint_image = fingerprint.get_fingerprint_image()
        
        
        result= cv.cvtColor(fingerprint_image, cv.COLOR_GRAY2RGB)
            
        for characteristic_point in list_minutiaes:
            singularity = characteristic_point.get_point_type()
            j = characteristic_point.get_posy()
            i = characteristic_point.get_posx()

            cv.circle(result, (i,j), radius=2, color=colors[singularity], thickness=2)

        cv.imshow(name + '_Minutiaes', result)
        cv.waitKey(0)
        # cv.destroyAllWindows()

        # if self._save_result:
        #     cv.imwrite(self._address_image + 'minutiae_' +  self._name_fingerprint +'.bmp', (self._minutiae_map))
    

    def __show_description_of_minutiae_from_list(self, list):
        print('Description of minutiaes from list:')
        
        for characteristic_point in list:
            print('\t', characteristic_point.get_description())
    
    
    def __sort_possible_common_points(self):
        sorted_possibble_common_base_minutiaes = sorted(self._possible_base_common_minutiaes, key=attrgetter('posy', 'posx'), reverse=True)
        sorted_possibble_common_input_minutiaes = sorted(self._possible_input_common_minutiaes, key=attrgetter('posy', 'posx'), reverse=True)
        
        ###############Debug#################################
        # self.__show_description_of_minutiae_from_list(sorted_possibble_common_base_minutiaes)
        # self.__show_description_of_minutiae_from_list(sorted_possibble_common_input_minutiaes)

        return (sorted_possibble_common_base_minutiaes, sorted_possibble_common_input_minutiaes)


    
    def __compare_edges(self, base_edge, input_edge):
        quadrant_ok = base_edge.get_quadrant() == input_edge.get_quadrant()
        angle_ok = abs(base_edge.get_angle() - input_edge.get_angle()) <= self._matching_angle_tolerance
        length_ok = abs(base_edge.get_length() - input_edge.get_length()) <= self._matching_distance_tolerance

        if quadrant_ok and angle_ok and length_ok:
            return True

        return False

    
    def __search_start_of_tree(self, base_minutiaes, input_minutiaes):
        possible_base_minutiaes_tree = []
        possible_input_minutiaes_tree = []
        
        base_length = len(base_minutiaes)
        input_length = len (input_minutiaes)

        is_found = False

        for base_pos in range(base_length - 1):
            base_edge = Edge(base_minutiaes[base_pos], base_minutiaes[base_pos + 1])

            for input_pos in range(input_length - 1):
                input_edge = Edge(input_minutiaes[input_pos], input_minutiaes[input_pos + 1])

                if input_edge.get_length() > (base_edge.get_length() + self._matching_distance_tolerance):
                    continue
                
                if self.__compare_edges(base_edge, input_edge):
                    possible_base_minutiaes_tree = base_minutiaes[base_pos:]
                    possible_input_minutiaes_tree = input_minutiaes[input_pos:]
                    is_found = True
                    break

            if is_found:
                break

        return (possible_base_minutiaes_tree, possible_input_minutiaes_tree)
        






        
    
    def matching(self, base_fingerprint, input_fingerprint):
        
        self.__get_lists_of_characteristic_points(base_fingerprint=base_fingerprint, input_fingerprint=input_fingerprint)
        self.__common_points()
        self.__are_void_possible_common_minutias_list()
        
        ############################ Debug ######################################
        #base_fingerprint.show_characteristic_point_from_list(type_characteristic_point='minutia')
        #input_fingerprint.show_characteristic_point_from_list(type_characteristic_point='minutia')
        self.__see_common_and_spurious_points()
        
        sorted_possibble_common_base_minutiaes, sorted_possibble_common_input_minutiaes = self.__sort_possible_common_points()
        self.__mark_characteristic_point(base_fingerprint, sorted_possibble_common_base_minutiaes, 'base')
        self.__mark_characteristic_point(input_fingerprint, sorted_possibble_common_input_minutiaes, 'input')

        base_minutiaes_tree, input_minutiaes_tre = self.__search_start_of_tree(sorted_possibble_common_base_minutiaes, sorted_possibble_common_input_minutiaes)
        self.__mark_characteristic_point(base_fingerprint, sorted_possibble_common_base_minutiaes, 'base_tree')
        self.__mark_characteristic_point(input_fingerprint, sorted_possibble_common_input_minutiaes, 'input_tree')

        # result_matching = self.__match_fingerprint()
        return self._MATCH_FINGERPRINT
