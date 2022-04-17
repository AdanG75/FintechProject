# -*- coding: utf-8 -*-

import cv2 as cv
from operator import attrgetter

from fingerprint_process.description.edge import Edge
from fingerprint_process.description.local_area import LocalArea
from fingerprint_process.utils.error_message import ErrorMessage


class MatchingTree(ErrorMessage):
    def __init__(self, local_ratio_tolerance=.5, local_angle_tolerance=1.5,
                 matching_distance_tolerance=5, matching_angle_tolerance=1.5,
                 matching_ratio_tolerance=.5, ) -> None:
        super().__init__()
        self._local_ratio_tolerance = local_ratio_tolerance
        self._local_angle_tolerance = local_angle_tolerance
        self._matching_distance_tolerance = matching_distance_tolerance
        self._matching_angle_tolerance = matching_angle_tolerance
        self._matching_ratio_tolerance = matching_ratio_tolerance

        self._base_minutiaes = []
        self._input_minutiaes = []
        self._possible_base_common_minutiaes = []
        self._possible_base_spurious_minutiaes = []
        self._possible_input_common_minutiaes = []
        self._possible_input_spurious_minutiaes = []

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
                        if ((origin_minutiae_base == origin_minutiae_input) and (
                                destination_minutiae_base == destination_minutiae_input)):
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
        input_minutiaes_to_compare = [{'minutiae': input_minutia, 'found': False} for input_minutia in
                                      self._input_minutiaes]

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

                    is_parent = self.__find_possible_minutia_parent(local_info_base_minutiae=local_base_minutiaes,
                                                                    local_info_input_minutia=local_input_minutiaes)

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
        colors = {'e': (150, 0, 0), 'b': (0, 150, 0)}

        fingerprint_image = fingerprint.get_fingerprint_image()

        result = cv.cvtColor(fingerprint_image, cv.COLOR_GRAY2RGB)

        for characteristic_point in list_minutiaes:
            singularity = characteristic_point.get_point_type()
            j = characteristic_point.get_posy()
            i = characteristic_point.get_posx()

            cv.circle(result, (i, j), radius=2, color=colors[singularity], thickness=2)

        cv.imshow(name + '_Minutiaes', result)
        cv.waitKey(0)
        # cv.destroyAllWindows()

        # if self._save_result:
        #     cv.imwrite(self._address_image + 'minutiae_' +  self._name_fingerprint +'.bmp', (self._minutiae_map))

    def __show_all_possible_trees(self, all_possible_trees, base_fingerprint, input_fingerprint):
        print('Possible trees found: ', len(all_possible_trees))
        count = 0
        for tree in all_possible_trees:
            self.__mark_characteristic_point(base_fingerprint, tree['base'], 'base_tree_' + str(count))
            self.__mark_characteristic_point(input_fingerprint, tree['input'], 'input_tree_' + str(count))
            count += 1

        cv.destroyAllWindows()

    def __show_description_of_minutiae_from_list(self, list):
        print('Description of minutiaes from list:')

        for characteristic_point in list:
            print('\t', characteristic_point.get_description())

    def __sort_possible_common_points(self):
        sorted_possibble_common_base_minutiaes = sorted(self._possible_base_common_minutiaes,
                                                        key=attrgetter('posy', 'posx'), reverse=True)
        sorted_possibble_common_input_minutiaes = sorted(self._possible_input_common_minutiaes,
                                                         key=attrgetter('posy', 'posx'), reverse=True)

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

    def __create_input_edge(self, input_minutiaes, input_pos, base_edge):
        possible_input_minutiaes_tree = []
        length_input_minutiaes = len(input_minutiaes)
        next_destination_pos = 1
        is_found = False

        while not is_found:
            input_edge = Edge(input_minutiaes[input_pos], input_minutiaes[input_pos + next_destination_pos])
            if input_edge.get_length() > (base_edge.get_length() + self._matching_distance_tolerance):
                is_found = False
                break

            if self.__compare_edges(base_edge, input_edge):
                is_found = True
                break

            next_destination_pos += 1
            if input_pos + next_destination_pos >= length_input_minutiaes:
                is_found = False
                break

        if is_found:
            possible_input_minutiaes_tree.append(input_minutiaes[input_pos])
            possible_input_minutiaes_tree += input_minutiaes[(input_pos + next_destination_pos):]

        return (is_found, possible_input_minutiaes_tree, input_pos + next_destination_pos)

    def __search_start_of_tree(self, base_minutiaes, input_minutiaes):
        possible_base_minutiaes_tree = []
        possible_input_minutiaes_tree = []
        all_posible_trees = []

        base_length = len(base_minutiaes)
        input_length = len(input_minutiaes)

        is_found = False

        for base_pos in range(base_length - 1):
            base_edge = Edge(base_minutiaes[base_pos], base_minutiaes[base_pos + 1])

            for input_pos in range(input_length - 1):
                is_found, possible_input_minutiaes_tree, pos_dest = self.__create_input_edge(input_minutiaes, input_pos,
                                                                                             base_edge)
                if is_found:
                    break

            if is_found:
                possible_base_minutiaes_tree = base_minutiaes[base_pos:]
                possible_input_spurious = input_minutiaes[:input_pos]

                ref = input_pos + 1
                while (ref < pos_dest):
                    possible_input_spurious.append(input_minutiaes[ref])

                    ref += 1

                ########################### Debug ###############################################################
                # print('\n\tPosible base Minutiaes: ', len(base_minutiaes))
                # print('\tPosible common base Minutiaes: ', len(possible_base_minutiaes_tree))
                # print('\tPosible spurious base Minutiaes: ', len(base_minutiaes[:base_pos]))
                # print('\n\tPosible input Minutiaes: ', len(input_minutiaes))
                # print('\tPosible common input Minutiaes: ', len(possible_input_minutiaes_tree))
                # print('\tPosible spurious input Minutiaes: ', len(possible_input_spurious))

                all_posible_trees.append({'base': possible_base_minutiaes_tree, 'input': possible_input_minutiaes_tree,
                                          'spu_b': base_minutiaes[:base_pos], 'spu_i': possible_input_spurious})

        return all_posible_trees

    def __set_full_edge(self, first_tree, pos, edge, type_edge):
        try:
            before_edge = first_tree[pos][type_edge][-1]
        except IndexError:
            before_edge = None

        edge.obtain_ratio(before_edge)
        edge.obtain_angle(before_edge)

        return edge

    def __create_edge(self, tree, first_tree, pos, ori_base, ori_input, dest_base, dest_input):
        try:
            base_edge = Edge(tree['base'][ori_base], tree['base'][dest_base])
        except:
            raise IndexError

        try:
            input_edge = Edge(tree['input'][ori_input], tree['input'][dest_input])
        except:
            raise IndexError

        base_edge = self.__set_full_edge(first_tree, pos, base_edge, 'edge_base')
        input_edge = self.__set_full_edge(first_tree, pos, input_edge, 'edge_input')

        return (base_edge, input_edge)

    def __is_edges_equals(self, base_edge, input_edge):
        quadrant_ok = base_edge.get_quadrant() == input_edge.get_quadrant()
        angle_ok = abs(base_edge.get_angle() - input_edge.get_angle()) <= self._matching_angle_tolerance
        ratio_ok = abs(base_edge.get_ratio() - input_edge.get_ratio()) <= self._matching_ratio_tolerance

        if quadrant_ok and angle_ok and ratio_ok:
            return True

        return False

    def __set_edge_into_tree(self, tree, first_tree, pos, ori_base, ori_input, dest_base, dest_input, base_edge,
                             input_edge, mode='middle'):

        if mode == 'initial':
            first_tree[pos]['base'].append(tree['base'][ori_base])
            first_tree[pos]['input'].append(tree['input'][ori_input])

        first_tree[pos]['base'].append(tree['base'][dest_base])
        first_tree[pos]['input'].append(tree['input'][dest_input])
        first_tree[pos]['edge_base'].append(base_edge)
        first_tree[pos]['edge_input'].append(input_edge)

    def __compare_edges_tree(self, tree, step_ori_base, step_ori_input, step_dest_base, step_dest_input, first_tree,
                             pos):
        base_add = 0
        input_add = 0
        for num in range(3):
            if num == 1:
                base_add = 1
                input_add = 0

            if num == 2:
                base_add = 0
                input_add = 1

            try:
                base_edge, input_edge = self.__create_edge(tree, first_tree, pos, step_ori_base, step_ori_input,
                                                           (step_dest_base + base_add), (step_dest_input + input_add))
            except IndexError:
                continue

            if self.__is_edges_equals(base_edge, input_edge):

                self.__set_edge_into_tree(tree, first_tree, pos, step_ori_base, step_ori_input,
                                          (step_dest_base + base_add), (step_dest_input + input_add), base_edge,
                                          input_edge)

                new_ori_base = step_dest_base + base_add
                new_ori_input = step_dest_input + input_add

                if num == 1:
                    first_tree[pos]['spu_b'].append(tree['base'][step_dest_base])

                if num == 2:
                    first_tree[pos]['spu_i'].append(tree['input'][step_dest_input])

                return (new_ori_base, new_ori_input, new_ori_base + 1, new_ori_input + 1)

        first_tree[pos]['spu_b'].append(tree['base'][step_dest_base])
        first_tree[pos]['spu_i'].append(tree['input'][step_dest_input])

        return (step_ori_base, step_ori_input, step_dest_base + 1, step_dest_input + 1)

    def __obtain_first_trees(self, all_possible_trees):
        first_tree = [{'base': [], 'input': [], 'spu_b': [], 'spu_i': [], 'edge_base': [], 'edge_input': []} for _ in
                      range(len(all_possible_trees))]

        pos = 0
        for tree in all_possible_trees:
            base_length = len(tree['base'])
            input_length = len(tree['input'])

            base_edge, input_edge = self.__create_edge(tree, first_tree, pos, 0, 0, 1, 1)
            self.__set_edge_into_tree(tree, first_tree, pos, 0, 0, 1, 1, base_edge, input_edge, mode='initial')

            first_tree[pos]['spu_b'] = tree['spu_b']
            first_tree[pos]['spu_i'] = tree['spu_i']

            ########################### Debug ###############################################################
            # print('\n********************************************************************')
            # print('\tPosible common base Minutiaes: ', len(tree['base']))
            # print('\tPosible spurious base Minutiaes: ', len(first_tree[pos]['spu_b']))
            # print('\tPosible common input Minutiaes: ', len(tree['input']))
            # print('\tPosible spurious input Minutiaes: ', len(first_tree[pos]['spu_i']))

            step_ori_base = 1
            step_ori_input = 1
            step_dest_base = 2
            step_dest_input = 2
            while (step_dest_base <= base_length - 1):
                if step_dest_input > input_length - 1:
                    break

                step_ori_base, step_ori_input, step_dest_base, step_dest_input = self.__compare_edges_tree(
                    tree, step_ori_base, step_ori_input, step_dest_base, step_dest_input, first_tree, pos)

            ########################### Debug ###############################################################
            # print('\n\tPosible common base Minutiaes: ', len(first_tree[pos]['base']))
            # print('\tPosible spurious base Minutiaes: ', len(first_tree[pos]['spu_b']))
            # print('\tPosible common input Minutiaes: ', len(first_tree[pos]['input']))
            # print('\tPosible spurious input Minutiaes: ', len(first_tree[pos]['spu_i']))

            try:
                first_tree[pos]['spu_b'] += tree['base'][step_dest_base:]
            except:
                pass

            try:
                first_tree[pos]['spu_i'] += tree['input'][step_dest_input:]
            except:
                pass

            ########################### Debug ###############################################################
            # print('\n\tPosible common base Minutiaes: ', len(first_tree[pos]['base']))
            # print('\tPosible spurious base Minutiaes: ', len(first_tree[pos]['spu_b']))
            # print('\tPosible common input Minutiaes: ', len(first_tree[pos]['input']))
            # print('\tPosible spurious input Minutiaes: ', len(first_tree[pos]['spu_i']))

            pos += 1

        return first_tree

    def __obtain_bigest_tree(self, first_trees):
        max_len = len(self._possible_base_common_minutiaes) - 1
        bigest_tree = {}

        for tree in first_trees:
            len_tree = len(tree['edge_base'])

            if len_tree == max_len:
                bigest_tree = tree
                break

            try:
                if len_tree > len(bigest_tree['edge_base']):
                    bigest_tree = tree.copy()
            except KeyError:
                bigest_tree = tree.copy()

        return bigest_tree

    def __set_new_local_description(self, common_minutiae, spurious_minutiae):
        local_area = LocalArea()
        process_message = local_area.get_new_neighborhood(common_minutiae, spurious_minutiae)

        if process_message == self._FINGERPRINT_OK:
            return spurious_minutiae

        raise Exception('Few common minutias')

    def __clear_all_lists(self):
        self._base_minutiaes.clear()
        self._input_minutiaes.clear()
        self._possible_base_common_minutiaes.clear()
        self._possible_base_spurious_minutiaes.clear()
        self._possible_input_common_minutiaes.clear()
        self._possible_input_spurious_minutiaes.clear()

    def __process_match(self, base_fingerprint, input_fingerprint, bigest_tree=[], fase='initial'):
        self.__common_points()

        if self.__are_void_possible_common_minutias_list() == self._DONT_MATCH_FINGERPRINT:
            raise Exception('There are not common minutias')

        ############################ Debug ######################################
        # base_fingerprint.show_characteristic_point_from_list(type_characteristic_point='minutia')
        # input_fingerprint.show_characteristic_point_from_list(type_characteristic_point='minutia')
        # self.__see_common_and_spurious_points()

        if fase == 'check':
            self._possible_base_common_minutiaes += bigest_tree['base']
            self._possible_input_common_minutiaes += bigest_tree['input']
            bigest_tree.clear()

        sorted_possibble_common_base_minutiaes, sorted_possibble_common_input_minutiaes = self.__sort_possible_common_points()
        ############################ Debug ######################################
        # self.__mark_characteristic_point(base_fingerprint, sorted_possibble_common_base_minutiaes, 'base')
        # self.__mark_characteristic_point(input_fingerprint, sorted_possibble_common_input_minutiaes, 'input')

        all_possible_trees = self.__search_start_of_tree(sorted_possibble_common_base_minutiaes,
                                                         sorted_possibble_common_input_minutiaes)

        if len(all_possible_trees) <= 0:
            raise Exception('There are not possible trees')

        ############################ Debug ######################################
        # self.__show_all_possible_trees(all_possible_trees, base_fingerprint, input_fingerprint)

        first_trees = self.__obtain_first_trees(all_possible_trees)
        bigest_tree = self.__obtain_bigest_tree(first_trees)
        first_trees.clear()
        bigest_tree['spu_b'] += self._possible_base_spurious_minutiaes
        bigest_tree['spu_i'] += self._possible_input_spurious_minutiaes

        return bigest_tree

    def __is_figerprint_match(self, bigest_tree):
        num_base_minutiaes = len(self._base_minutiaes)
        num_input_minutiaes = len(self._input_minutiaes)

        minimum_score = ((num_base_minutiaes + num_input_minutiaes) // 4) - 1

        if len(bigest_tree['base']) == len(bigest_tree['input']):
            if len(bigest_tree['base']) >= minimum_score:
                return self._MATCH_FINGERPRINT

        return self._DONT_MATCH_FINGERPRINT

    def matching(self, base_fingerprint, input_fingerprint):

        global new_base_minutiaes, new_input_minutiaes

        self.__get_lists_of_characteristic_points(base_fingerprint=base_fingerprint,
                                                  input_fingerprint=input_fingerprint)

        try:
            bigest_tree = self.__process_match(base_fingerprint, input_fingerprint, fase='initial')
        except:
            return self._DONT_MATCH_FINGERPRINT

        ############################ Debug ######################################
        # print('\n\tBiggest tree')
        # print('Common base minutiaes: ', len(bigest_tree['base']))
        # print('Edge base minutiaes: ', len(bigest_tree['edge_base']))
        # print('Spurious base minutiaes: ', len(bigest_tree['spu_b']))
        # print('Common input minutiaes: ', len(bigest_tree['input']))
        # print('Edge input minutiaes: ', len(bigest_tree['edge_input']))
        # print('Spurious input minutiaes: ', len(bigest_tree['spu_i']))

        is_tree_compleate = False
        try:
            new_base_minutiaes = self.__set_new_local_description(common_minutiae=bigest_tree['base'],
                                                                  spurious_minutiae=bigest_tree['spu_b'])
            new_input_minutiaes = self.__set_new_local_description(common_minutiae=bigest_tree['input'],
                                                                   spurious_minutiae=bigest_tree['spu_i'])
        except:
            is_tree_compleate = True

        if not is_tree_compleate:
            self.__clear_all_lists()

            self._base_minutiaes = new_base_minutiaes.copy()
            self._input_minutiaes = new_input_minutiaes.copy()
            new_base_minutiaes.clear()
            new_input_minutiaes.clear()

            bigest_tree_copy = bigest_tree.copy()
            try:
                bigest_tree = self.__process_match(base_fingerprint, input_fingerprint, bigest_tree=bigest_tree,
                                                   fase='check')
            except:
                bigest_tree = bigest_tree_copy.copy()
            finally:
                bigest_tree_copy.clear()

        ############################ Debug ######################################
        # print('\n\tBiggest tree')
        # print('Common base minutiaes: ', len(bigest_tree['base']))
        # print('Edge base minutiaes: ', len(bigest_tree['edge_base']))
        # print('Spurious base minutiaes: ', len(bigest_tree['spu_b']))
        # print('Common input minutiaes: ', len(bigest_tree['input']))
        # print('Edge input minutiaes: ', len(bigest_tree['edge_input']))
        # print('Spurious input minutiaes: ', len(bigest_tree['spu_i']))

        process_message = self.__is_figerprint_match(bigest_tree)

        return process_message
