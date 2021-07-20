# -*- coding: utf-8 -*-

from Conect_Sensor import Conect_Sensor
from Fingerprint import Fingerprint
from Bank_Fingerprint_Images import Bank_fingerprint
from Match import match

import cv2 as cv


def create_fingerprint_samples():
    bank_fp = Bank_fingerprint(num_fingerprints= 20, address_output='./authentication/sampleImages/', name= 'Fingerprint_Test', extension= '.bmp')
    bank_fp.generate_bank_fingerprint(auto_named = False)


def get_data_fingerprint(fingerprint, in_cloud = True, data_fingerprint = []):
    if in_cloud == False:
        conect_sensor = Conect_Sensor(serial_port = 'COM3', baud_rate = 57600, width = 256, height = 288)
        data_fingerprint = conect_sensor.catch_data_fingerprint()

    if data_fingerprint[0] == False:
        return (False,)
    
    return data_fingerprint


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
        ubication_image = change_directory_of_images()
        try:
            img = cv.imread(ubication_image, 0)
            #img = cv.imread('./authentication/sampleImages/Huella70.bmp', 0)
            process_message = fingerprint.describe_fingerprint(angles_tolerance=1, from_image=True, fingerprint_image=img)
        except:
            print('Error to get the fingerprint image')
            return True
    
    if process_message == fingerprint._FINGERPRINT_OK:
        return fingerprint
    else:
        fingerprint.show_message(process_message)
        return True


def match_index_and_base_fingerprints(base_name, input_name, mode, source):

    if source.lower() == 'sensor':
        base_fingerprint = get_description_fingerprint(name_fingerprint=base_name, from_sensor=True)
        index_fingerprint = get_description_fingerprint(name_fingerprint=input_name, from_sensor=True)
    else:
        base_fingerprint = get_description_fingerprint(name_fingerprint=base_name, from_sensor=False)
        index_fingerprint = get_description_fingerprint(name_fingerprint=input_name, from_sensor=False)

    return match(base_fingerprint, index_fingerprint, mode)