# -*- coding: utf-8 -*-

import numpy as np
from Quality_Image import Quality_Fingerprint
from Preprocessing_Fingerprint import PreprocessingFingerprint

class Fingerprint(object):
    def __init__(self, fingerprint_rows = 288, figerprint_columns = 256, name_fingerprint = 'fingerprint'):
        self.fingerprint_rows = fingerprint_rows
        self.figerprint_columns = figerprint_columns
        self.name_fingerprint = name_fingerprint

        self.varian_index = 0.0
        self.quality_index = 0.0

        self.raw_image = []
        self.ezquel_fingerprint = []
        self.varian_mask = []
        self.roi = []
        self.angles = []
        self.list_minutias = []
        self.list_core_points = []

    def reconstruction_fingerprint(self, data_fingerprint):
        self.raw_image = np.zeros((self.fingerprint_rows, self.figerprint_columns))
        x = 0
        y = 0
        for pixel in data_fingerprint:
            self.raw_image[y][x] = pixel
            if (x == 255):
                y += 1
                x = 0
            else:
                x += 1

        
        return self.raw_image

    def fingerprint_enhance(self):
        preprocessing_fp = PreprocessingFingerprint(name_fingerprint= self.name_fingerprint, address_output='./authentication/preprocessingFingerprints/', ridge_segment_thresh=0.3)
        (self.ezquel_fingerprint, self.roi, self.angles, self.varian_mask, self.varian_index ) = preprocessing_fp.enhance(img=self.raw_image, resize=False, return_as_image = False, show_fingerprints = True, save_fingerprints = True)
        

    def get_quality_index(self):
        quality_image = Quality_Fingerprint(numberFilters = 16, columnsImage = 256, rowsImage = 288, dataFilters = 'dataFilter.txt', showGraphs = True, address_output='./authentication/data/', name_fingerprint=self.name_fingerprint)
        self.quality_index = quality_image.getQualityFingerprint(self.raw_image, save_graphs = True)

        return self.quality_index

    def get_corepoints(self):
        pass

    def get_minutias(self):
        pass

