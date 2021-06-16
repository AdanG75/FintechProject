# -*- coding: utf-8 -*-

from os import name
import sys
from Conect_Sensor import Conect_Sensor
from Fingerprint import Fingerprint
from Bank_Fingerprint_Images import Bank_fingerprint
from Matching_Process import Matching_Process
from Matching_Tree import Matching_Tree

import cv2 as cv


def get_data_fingerprint(fingerprint, in_cloud = True, data_fingerprint = []):
    if in_cloud == False:
        conect_sensor = Conect_Sensor(serial_port = 'COM5', baud_rate = 57600, width = 256, height = 288)
        data_fingerprint = conect_sensor.catch_data_fingerprint()

    if data_fingerprint[0] == False:
        return (False,)
    
    return data_fingerprint


def create_fingerprint_samples():
    bank_fp = Bank_fingerprint(num_fingerprints= 20, address_output='./authentication/sampleImages/', name= 'Fingerprint_Test', extension= '.bmp')
    bank_fp.generate_bank_fingerprint(auto_named = False)


def get_description_fingerprint(name_fingerprint = 'fingerprint', from_sensor=True, ubication_image=''):
    fingerprint = Fingerprint(characteritic_point_thresh = 0.8, name_fingerprint= name_fingerprint)
    process_message = None
    
    if from_sensor:
        data_image = get_data_fingerprint(fingerprint=fingerprint, in_cloud=False)
        if len(data_image) < 2:
            print('Error to get the fingerprint image')
            return True
        
        process_message = fingerprint.describe_fingerprint(data_image, angles_tolerance=1)
    else:
        try:
            img = cv.imread(ubication_image, 0)
            process_message = fingerprint.describe_fingerprint(angles_tolerance=1, from_image=True, fingerprint_image=img)
        except:
            print('Error to get the fingerprint image')
            return True
    
    if process_message == fingerprint._FINGERPRINT_OK:
        return fingerprint
    else:
        fingerprint.show_message(process_message)
        return True


def get_description_by_image(name_fingerprint):
    ubication_image = change_directory_of_images()
    return get_description_fingerprint(ubication_image=ubication_image, from_sensor=False, name_fingerprint=name_fingerprint)


def match(base_fingerprint, input_fingerprint, mode='original'):
    base_fingerprint_is_ok = (base_fingerprint != True)
    index_fingerprint_is_ok =(input_fingerprint != True)

    if (base_fingerprint_is_ok and index_fingerprint_is_ok):
        if mode == 'tree':
            matching = Matching_Tree()
            process_message = matching.matching(base_fingerprint=base_fingerprint, input_fingerprint=input_fingerprint)
        else:
            matching = Matching_Process()
            process_message = matching.matching(base_fingerprint=base_fingerprint, index_fingerprint=input_fingerprint)

        matching.show_message(process_message)
    else:
        return True    


def match_index_and_base_fingerprints():
    base_fingerprint = get_description_fingerprint(name_fingerprint='base_fingerprint_S')
    index_fingerprint = get_description_fingerprint(name_fingerprint='index_fingerprint_S')

    return match(base_fingerprint, index_fingerprint)


def match_by_image():
    base_fingerprint = get_description_by_image('base_fingerprint_I')
    input_fingerprint = get_description_by_image('input_fingerprint_I')

    return match(base_fingerprint, input_fingerprint)


def matching_tree_by_sensor():
    base_fingerprint = get_description_fingerprint(name_fingerprint='base_fingerprint_S_tree_')
    index_fingerprint = get_description_fingerprint(name_fingerprint='index_fingerprint_S_tree_')

    return match(base_fingerprint, index_fingerprint, mode='tree')


def matching_tree_by_image():
    base_fingerprint = get_description_by_image('base_fingerprint_I')
    input_fingerprint = get_description_by_image('input_fingerprint_I')

    return match(base_fingerprint, input_fingerprint, mode='tree')


def change_directory_of_images():
    finish = False
    ubication_image=None

    while(not finish):
        ubication_image='./authentication/sampleImages/'
        print('\n\t Directory to search image: {}'.format(ubication_image))
        print('Would you like to change the directory by default:\n')
        print('\t [Y]es')
        print('\t [N]o')
        option = input('\nSelect you option: ')

        if (option[0].upper() == 'Y'):
            ubication_image=input('Write the new directory to search image: ')
            finish = True
        elif (option[0].upper() == 'N'):
            finish = True
        else:
            continue

    name_image = input('Write the image name (with extension): ')
    ubication_image += name_image

    return ubication_image


def local_test():
    sys.stdout.flush()
    print('\n\tAuthentication\'s Module\n')
    print('\nOptions:\n')
    print('\t1.- Create fingerprint\'s bank')
    print('\t2.- Fingerprints processing flow (from Sensor)')
    print('\t3.- Fingerprints processing flow (from Image)')
    print('\t4.- Fingerprints Matching process (from Sensor)')
    print('\t5.- Fingerprints Matching process (from Image)')
    print('\t6.- Fingerprints Matching tree process (from Sensor)')
    print('\t7.- Fingerprints Matching tree process (from Image)')
    print('\t9.- Exit the programme')

    print('\n')
    option=input('Select an option: ')

    if (option == '1'):
        create_fingerprint_samples()

    elif (option == '2'):
        result = get_description_fingerprint()
        if (result == True):
            return result
        else:
            result.show_characteristic_point_from_list(type_characteristic_point='minutiae')
            result.show_characteristic_point_from_list(type_characteristic_point='core')

    elif (option == '3'):
        result = get_description_by_image('my_fingerprint')
        if (result == True):
            return result
        else:
            result.show_characteristic_point_from_list(type_characteristic_point='minutiae', mode='full')
            result.show_characteristic_point_from_list(type_characteristic_point='core')

    elif (option == '4'):
        fail_match = match_index_and_base_fingerprints()
        if (fail_match == True):
            return fail_match

    elif (option == '5'):
        fail_match = match_by_image()
        if (fail_match == True):
            return fail_match

    elif (option == '6'):
        fail_match = matching_tree_by_sensor()
        if (fail_match == True):
            return fail_match

    elif (option == '7'):
        fail_match = matching_tree_by_image()
        if (fail_match == True):
            return fail_match

    elif (option == '9'):
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
        