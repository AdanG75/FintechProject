# -*- coding: utf-8 -*-

import numpy as np
import cv2 as cv
from Quality_Image import Quality_Fingerprint
from Preprocessing_Fingerprint import PreprocessingFingerprint

class Fingerprint(object):
    def __init__(self, fingerprint_rows = 288, figerprint_columns = 256, name_fingerprint = 'fingerprint', show_result = True, save_result = True):
        self.fingerprint_rows = fingerprint_rows
        self.figerprint_columns = figerprint_columns
        self.name_fingerprint = name_fingerprint
        self.show_result = show_result
        self.save_result = save_result

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
        (self.ezquel_fingerprint, self.roi, self.angles, self.varian_mask, self.varian_index ) = preprocessing_fp.enhance(img=self.raw_image, resize=False, return_as_image = False, show_fingerprints = self.show_result, save_fingerprints = self.save_result)
        

    def get_quality_index(self):
        quality_image = Quality_Fingerprint(numberFilters = 16, columnsImage = 256, rowsImage = 288, dataFilters = 'dataFilter.txt', showGraphs = self.show_result, address_output='./authentication/data/', name_fingerprint=self.name_fingerprint)
        self.quality_index = quality_image.getQualityFingerprint(self.raw_image, save_graphs = self.save_result)

        return self.quality_index

    def get_corepoints(self):
        colors = {'l' : (0, 0, 255), 'd' : (0, 128, 255), 'w': (255, 153, 255)}
        figure = 'rectangle'
        to_show = 'core'
        

    def get_minutias(self):
        colors = {'e' : (150, 0, 0), 'b' : (0, 150, 0)}
        figure = 'circle'
        to_show = 'minutia'
        

    def mark_characteristic_point(self, colors, figure, to_show):
        marked_image = np.zeros((self.ezquel_fingerprint))
        im_max = self.ezquel_fingerprint.max()
        (rows, columns) = marked_image.shape
        void_image = False
        if im_max == 1:
            marked_image[0:rows][:, 0:columns] = (((-255) * marked_image) + 255).astype('uint8')
        elif im_max == 0:
            void_image = False
        else:
            marked_image[0:rows][:, 0:columns] = (((-255) * (marked_image/im_max)) + 255).astype('uint8')
        
        if void_image == False:
            marked_image = cv.cvtColor(marked_image, cv.COLOR_GRAY2RGB)

            if to_show == 'core':
                characteristic_list = self.list_core_points.copy
            elif to_show == 'minuta':
                characteristic_list = self.list_minutias.copy
            else:
                characteristic_list = []

            for characteristic_point in characteristic_list:
                singularity = characteristic_point.get_type()
                i = characteristic_point.get_posy()
                j = characteristic_point.get_posx()
                if figure == 'circle':
                    cv.circle(marked_image, (i,j), radius=2, color=colors[singularity], thickness=2)
                elif figure == 'rectangle':
                    cv.rectangle(marked_image, ((j+0), (i+0)), ((j+1), (i+1)), colors[singularity], 3)
                else:
                    pts = np.array([[j, i+1], [j-1, i-1], [j+1, i-1]], np.int32)
                    cv.polylines(marked_image, pts=[pts], isClosed=True, color=colors[singularity], thickness=2)
