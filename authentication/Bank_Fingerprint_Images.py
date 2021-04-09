# -*- coding: utf-8 -*-

from Conect_Sensor import Conect_Sensor
from Fingerprint import Fingerprint
import cv2 as cv

class Bank_fingerprint(object):
    def __init__(self, num_fingerprints= 20, address_output='./sampleImages/', name= 'Fingerprint_Test', extension= '.bmp'):
        self.num_fingerprints = num_fingerprints
        self.address_output = address_output
        self.name = name
        self.extension = extension

    def generate_bank_fingerprint(self, auto_named = True):
        if auto_named == False:
            self.name = input('\nWrite the name to fingerprint image (without extension) to be saved:  ')
            self.extension = input('\nWrite the image\'s extension (include \".\" at beginning):  ')

        conect_sensor = Conect_Sensor(serial_port = 'COM5', baud_rate = 57600, width = 256, height = 288)
        fingerprint = Fingerprint()
    
        for _ in range(self.num_fingerprints):
            data_fingerprint = conect_sensor.catch_data_fingerprint()

            if data_fingerprint[0] == False:
                print('Fatal error trying to catch fingerprint image')
                break

            raw_image = fingerprint.reconstruction_fingerprint(data_fingerprint)
            
            cv.imwrite(self.address_output + self.name + str(_) + self.extension, (raw_image))

