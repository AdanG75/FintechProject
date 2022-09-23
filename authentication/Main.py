# -*- coding: utf-8 -*-

import Utils as u_fin


def local_test():
    print('\n\tAuthentication\'s Module\n')
    print('\nOptions:\n')
    print('\t1.- Create fingerprint\'s bank')
    print('\t2.- Fingerprints processing flow (from Sensor)')
    print('\t3.- Fingerprints processing flow (from Image)')
    print('\t4.- Fingerprints Matching process (from Sensor)')
    print('\t5.- Fingerprints Matching process (from Image)')
    print('\t6.- Fingerprints Matching tree process (from Sensor)')
    print('\t7.- Fingerprints Matching tree process (from Image)')
    print('\t8.- Fingerprints Matching Core (from Sensor)')
    print('\t9.- Fingerprints Matching Core (from Image)')
    print('\tX.- Exit the programme')

    print('\n')
    option=input('Select an option: ')

    if (option == '1'):
        u_fin.create_fingerprint_samples()

    elif (option == '2'):
        result = u_fin.get_description_fingerprint()
        if (result == True):
            return result
        else:
            result.show_characteristic_point_from_list(type_characteristic_point='minutiae')
            result.show_characteristic_point_from_list(type_characteristic_point='core')

    elif (option == '3'):
        result = u_fin.get_description_fingerprint(name_fingerprint='my_fingerprint', from_sensor=False)
        if (result == True):
            return result
        else:
            result.show_characteristic_point_from_list(type_characteristic_point='minutiae', mode='full')
            result.show_characteristic_point_from_list(type_characteristic_point='core')

    elif (option == '4'):
        fail_match = u_fin.match_index_and_base_fingerprints('base_fingerprint_S', 'index_fingerprint_S', mode='original', source='sensor')
        if (fail_match == True):
            return fail_match

    elif (option == '5'):
        fail_match = u_fin.match_index_and_base_fingerprints('base_fingerprint_I', 'index_fingerprint_I', mode='original', source='image')
        if (fail_match == True):
            return fail_match

    elif (option == '6'):
        fail_match = u_fin.match_index_and_base_fingerprints('base_fingerprint_S_tree_', 'input_fingerprint_S_tree_', mode='tree', source='sensor')
        if (fail_match == True):
            return fail_match

    elif (option == '7'):
        fail_match = u_fin.match_index_and_base_fingerprints('base_fingerprint_I_tree_', 'input_fingerprint_I_tree_', mode='tree', source='image')
        if (fail_match == True):
            return fail_match

    elif (option == '8'):
        fail_match = u_fin.match_index_and_base_fingerprints('base_fingerprint_S_core_', 'input_fingerprint_S_core_', mode='core', source='sensor')
        if (fail_match == True):
            return fail_match

    elif (option == '9'):
        fail_match = u_fin.match_index_and_base_fingerprints('base_fingerprint_I_core_', 'input_fingerprint_I_core_', mode='core', source='image')
        if (fail_match == True):
            return fail_match

    elif (option.lower() == 'x'):
        return True

    elif ((option == '\n') or (option == '')):
        pass

    else:
        print('\n:: Option can not be find it ::\n')

    return False


if __name__ == '__main__':
    while(True):
        end_programme = local_test()
        if(end_programme):
            print('\n\tGood bye :)\n')
            break
        