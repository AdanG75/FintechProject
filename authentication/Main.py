# -*- coding: utf-8 -*-

import sys
from Conect_Sensor import Conect_Sensor
from Fingerprint import Fingerprint
from Bank_Fingerprint_Images import Bank_fingerprint
from Matching_Process import Matching_Process

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


def get_description_fingerprint(name_fingerprint = 'fingerprint'):
    fingerprint = Fingerprint(characteritic_point_thresh = 0.8, name_fingerprint= name_fingerprint)
    data_image = get_data_fingerprint(fingerprint=fingerprint, in_cloud=False)
    if len(data_image) < 2:
        print('Error to get the fingerprint image')
        return True
    process_message = fingerprint.describe_fingerprint(data_image, angles_tolerance=1)
    
    if process_message == fingerprint._FINGERPRINT_OK:
        return fingerprint
    else:
        fingerprint.show_message(process_message)
        return True


def show_characteristic_point_from_list(characteristic_points_list):
    for characteristic_point in characteristic_points_list:
        print(characteristic_point.get_description())

    print('\n*********************************************************************************************\n')


def match_index_and_base_fingerprints():
    base_fingerprint = get_description_fingerprint(name_fingerprint='base_fingerprint')
    index_fingerprint = get_description_fingerprint(name_fingerprint='index_fingerprint')

    base_fingerprint_is_ok = (base_fingerprint != True)
    index_fingerprint_is_ok =(index_fingerprint != True)

    if (base_fingerprint_is_ok and index_fingerprint_is_ok):
        base_fingerprint_core_point_list = base_fingerprint.get_core_point_list()
        base_fingerprint_minutiae_list = base_fingerprint.get_minutiae_list()
        index_fingerprint_core_point_list = index_fingerprint.get_core_point_list()
        index_fingerprint_minutiae_list = index_fingerprint.get_minutiae_list()

        show_characteristic_point_from_list(base_fingerprint_core_point_list)
        show_characteristic_point_from_list(base_fingerprint_minutiae_list)
        show_characteristic_point_from_list(index_fingerprint_core_point_list)
        show_characteristic_point_from_list(index_fingerprint_minutiae_list)

        matching = Matching_Process()
        process_message = matching.matching(base_minutiaes_list= base_fingerprint_minutiae_list, base_core_list= base_fingerprint_core_point_list,
                            index_minutiaes_list= index_fingerprint_minutiae_list, index_core_list= index_fingerprint_core_point_list)

        matching.show_message(process_message)
    else:
        return True

    
def local_test():
    sys.stdout.flush()
    print('\n\tAuthentication\'s Module\n')
    print('\nOptions:\n')
    print('\t1.- Create fingerprint\'s bank')
    print('\t2.- Fingerprints processing flow')
    print('\t3.- Fingerprints Matching process')
    print('\t9.- Exit the programme')

    print('\n')
    option=input('Select an option: ')

    if (option == '1'):
        create_fingerprint_samples()
    elif (option == '2'):
        fail_description = get_description_fingerprint()
        if (fail_description == True):
            return fail_description
    elif (option == '3'):
        fail_match = match_index_and_base_fingerprints()
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
        