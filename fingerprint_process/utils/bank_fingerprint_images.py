# -*- coding: utf-8 -*-

import cv2 as cv
import numpy as np
from glob import glob

from fingerprint_process.description.fingerprint import Fingerprint
from fingerprint_process.preprocessing.connect_sensor import ConnectSensor


class BankFingerprint(object):
    def __init__(
            self,
            num_fingerprints=20,
            address_output='./fingerprint_process/sampleImages/',
            name='Fingerprint_Test',
            extension='.bmp'
    ):
        super().__init__()
        self._num_fingerprints = num_fingerprints
        self._address_output = address_output
        self._name = name
        self._extension = extension

    def generate_bank_fingerprint(self, auto_named=True):
        if auto_named == False:
            self._name = input('\nWrite the name to fingerprint image (without extension) to be saved:  ')
            self._extension = input('\nWrite the image\'s extension (include \".\" at beginning):  ')

        connect_sensor = ConnectSensor(serial_port='COM3', baud_rate=57600, width=256, height=288)
        fingerprint = Fingerprint()

        for _ in range(self._num_fingerprints):
            data_fingerprint = connect_sensor.catch_data_fingerprint()

            if data_fingerprint[0] == False:
                print('Fatal error trying to catch fingerprint image')
                break

            raw_image = fingerprint.reconstruction_fingerprint(data_fingerprint)

            cv.imwrite(self._address_output + self._name + str(_) + self._extension, raw_image)

    def get_bank_fingerprints(self):
        images_paths = glob(self._address_output)
        return np.array([cv.imread(img_path, 0) for img_path in images_paths])
