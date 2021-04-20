# -*- coding: utf-8 -*-

import sys
from Conect_Sensor import Conect_Sensor
from Fingerprint import Fingerprint
from Bank_Fingerprint_Images import Bank_fingerprint


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

def local_test():
    sys.stdout.flush()
    print('\n\tAuthentication\'s Module\n')
    print('\nOptions:\n')
    print('\t1.- Create fingerprint\'s bank')
    print('\t2.- Fingerprints processing flow')
    print('\t9.- Exit the programme')

    print('\n')
    option=input('Select an option: ')

    if (option == '1'):
        create_fingerprint_samples()
    elif (option == '2'):
        fingerprint = Fingerprint(characteritic_point_thresh = 0.8)
        data_image = get_data_fingerprint(fingerprint=fingerprint, in_cloud=False)
        if len(data_image) < 2:
            print('Error to get the fingerprint image')
            return True
        fingerprint.describe_fingerprint(data_image, angles_tolerance=1)
        
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
        