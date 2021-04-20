# -*- coding: utf-8 -*-

import numpy as np
import cv2 as cv
import math
from Quality_Image import Quality_Fingerprint
from Preprocessing_Fingerprint import PreprocessingFingerprint
from Minutia import Minutiae
from Core_Point import Core_Point

class Fingerprint(object):
    def __init__(self, fingerprint_rows = 288, figerprint_columns = 256, name_fingerprint = 'fingerprint', 
                show_result = True, save_result = True, size_window_minutiae = 3, size_window_core = 1, 
                address_image = './authentication/preprocessingFingerprints/', address_data = './authentication/data/'):
        self.fingerprint_rows = fingerprint_rows
        self.figerprint_columns = figerprint_columns
        self.name_fingerprint = name_fingerprint
        self.show_result = show_result
        self.save_result = save_result
        self.size_window_minutiae = size_window_minutiae
        self.size_window_core = size_window_core
        self.address_image  = address_image 
        self.address_data = address_data

        self._varian_index = 0.0
        self._quality_index = 0.0
        self._void_image = False
        self._rows = 0
        self._columns = 0

        self._raw_image = []
        self._ezquel_fingerprint = []
        self._minutiae_map = []
        self._core_map = []
        self._varian_mask = []
        self._roi = []
        self._angles = []
        self._list_minutias = []
        self._list_core_points = []
        self._minutiae_cell = []
        self._core_cell = []
        self._ezquel_as_image = [] 

    def __reconstruction_fingerprint(self, data_fingerprint):
        self._raw_image = np.zeros((self.fingerprint_rows, self.figerprint_columns))
        x = 0
        y = 0
        for pixel in data_fingerprint:
            self._raw_image[y][x] = pixel
            if (x == (self.figerprint_columns - 1)):
                y += 1
                x = 0
            else:
                x += 1


    def __fingerprint_enhance(self):
        preprocessing_fp = PreprocessingFingerprint(name_fingerprint= self.name_fingerprint, address_output= self.address_image, ridge_segment_thresh=0.25)
        (self._ezquel_fingerprint, self._roi, self._angles, self._varian_mask, self._varian_index ) = preprocessing_fp.enhance(img=self._raw_image, resize=False, return_as_image = False, show_fingerprints = self.show_result, save_fingerprints = self.save_result)
        (self._rows, self._columns) = self._ezquel_fingerprint.shape
        

    def __get_quality_index(self):
        quality_image = Quality_Fingerprint(numberFilters = 16, columnsImage = self.figerprint_columns, rowsImage = self.fingerprint_rows, dataFilters = 'dataFilter.txt', showGraphs = self.show_result, address_output= self.address_data, name_fingerprint=self.name_fingerprint)
        self._quality_index = quality_image.getQualityFingerprint(self._raw_image, save_graphs = self.save_result)


    def __get_corepoints(self, angles_tolerance):
        for i in range(3, len(self._angles) - 2):             # Y
            for j in range(3, len(self._angles[i]) - 2):      # x
                # mask any singularity outside of the mask
                mask_slice = self._roi[(i-2)*self.size_window_core:(i+3)*self.size_window_core, (j-2)*self.size_window_core:(j+3)*self.size_window_core]
                mask_flag = np.sum(mask_slice)
                if mask_flag == (self.size_window_core*5)**2:
                    self.__poincare_index_at(i, j, angles_tolerance)
                    
        
        colors = {'l' : (0, 0, 255), 'd' : (0, 128, 255), 'w': (255, 153, 255)}
        figure = 'rectangle'
        to_show = 'core'
        self.__mark_characteristic_point(colors, figure, to_show)
        

    def __get_minutias(self):
        for i in range(1, self._columns - self.size_window_minutiae//2):
            for j in range(1, self._rows - self.size_window_minutiae//2):
                self.__minutiae_at(j, i)
                
        
        colors = {'e' : (150, 0, 0), 'b' : (0, 150, 0)}
        figure = 'circle'
        to_show = 'minutiae'
        self.__mark_characteristic_point(colors, figure, to_show)
        

    def __mark_characteristic_point(self, colors, figure, to_show):   
        if self._void_image == False:
            result = cv.cvtColor(self._ezquel_as_image, cv.COLOR_GRAY2RGB)
            characteristic_list = []

            if to_show == 'core':
                characteristic_list = self._list_core_points.copy()
            elif to_show == 'minutiae':
                characteristic_list = self._list_minutias.copy()
            else:
                self._void_image = True
                
            if (not self._void_image):
                for characteristic_point in characteristic_list:
                    singularity = characteristic_point.get_point_type()
                    j = characteristic_point.get_posy()
                    i = characteristic_point.get_posx()

                    if figure == 'circle':
                        cv.circle(result, (i,j), radius=2, color=colors[singularity], thickness=2)
                    elif figure == 'rectangle':
                        cv.rectangle(result, ((i-1)*self.size_window_core, (j-1)*self.size_window_core), ((i+1)*self.size_window_core, (j+1)*self.size_window_core), colors[singularity], 3)
                    else:
                        pts = np.array([[i, j+1], [i-1, j-1], [i+1, j-1]], np.uint8)
                        cv.polylines(result, pts=[pts], isClosed=True, color=colors[singularity], thickness=2)

                if to_show == 'core':
                    self._core_map = result.copy()

                    if self.show_result:
                        cv.imshow('Core points', self._core_map)
                        cv.waitKey(0)
                        cv.destroyAllWindows()

                    if self.save_result:
                        cv.imwrite(self.address_image + 'core_' +  self.name_fingerprint +'.bmp', (self._core_map))
                else:
                    self._minutiae_map = result.copy()

                    if self.show_result:
                        cv.imshow('Minutiaes', self._minutiae_map)
                        cv.waitKey(0)
                        cv.destroyAllWindows()

                    if self.save_result:
                        cv.imwrite(self.address_image + 'minutiae_' +  self.name_fingerprint +'.bmp', (self._minutiae_map))
            

    def __minutiae_at(self, j, i):
        """
        https://airccj.org/CSCP/vol7/csit76809.pdf pg93
        Crossing number methods is a really simple way to detect ridge endings and ridge bifurcations.
        Then the crossing number algorithm will look at 3x3 pixel blocks:

        if middle pixel is black (represents ridge):
        if pixel on boundary are crossed with the ridge once, then it is a possible ridge ending
        if pixel on boundary are crossed with the ridge three times, then it is a ridge bifurcation

        :param pixels:
        :param i:
        :param j:
        :return:
        """
        # if middle pixel is black (represents ridge)
        if self._ezquel_fingerprint[j][i] == 1:
            if self._varian_mask[j][i] > 0.65:
                values = [self._ezquel_fingerprint[j + l][i + k] for k, l in self._minutiae_cell]
                #values = np.asarray(values).astype('uint8')
                #print(values)

                non_border = 0
                region = ((j-15, i), (j+15, i), (j, i-15), (j, i+15))
                for _ in range(len(region)):
                    if ((region[_][0] >= self._rows) or (region[_][1] >= self._columns)):
                        non_border = 0
                        break
                    else:
                        non_border += self._roi[region[_][0]][region[_][1]]

                # count crossing how many times it goes from 0 to 1
                crossings = 0
                for k in range(0, len(values)-1):
                    crossings += abs(int(values[k]) - int(values[k + 1]))
                crossings //= 2

                if crossings == 1:
                    if non_border >= 4:
                        self._list_minutias.append(Minutiae(posy= j, posx= i, angle= self._angles[j][i], point_type='e'))

                if crossings == 3:
                    self._list_minutias.append(Minutiae(posy= j, posx= i, angle= self._angles[j][i], point_type='b'))

    def __get_cells(self):
        if self.size_window_minutiae == 3:
            self._minutiae_cell = [(-1, -1), (-1, 0), (-1, 1),          # p1 p2 p3
                (0, 1),  (1, 1),  (1, 0),                               # p8    p4
                (1, -1), (0, -1), (-1, -1)]                             # p7 p6 p5
        else:
            self._minutiae_cell = [(-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2),                   # p1 p2   p3
                (-1, 2), (0, 2),  (1, 2),  (2, 2), (2, 1), (2, 0),                                  # p8      p4
                (2, -1), (2, -2), (1, -2), (0, -2), (-1, -2), (-2, -2)]                             # p7 p6   p5

        self._core_map = [(-1, -1), (-1, 0), (-1, 1),           # p1 p2 p3
                (0, 1),  (1, 1),  (1, 0),                       # p8    p4
                (1, -1), (0, -1), (-1, -1)]                     # p7 p6 p5

    def __poincare_index_at(self, j, i, tolerance):
        """
        compute the summation difference between the adjacent orientations such that the orientations is less then 90 degrees
        https://books.google.pl/books?id=1Wpx25D8qOwC&lpg=PA120&ots=9wRY0Rosb7&dq=poincare%20index%20fingerprint&hl=pl&pg=PA120#v=onepage&q=poincare%20index%20fingerprint&f=false
        :param i:
        :param j:
        :param angles:
        :param tolerance:
        :return:
        """
        if self._varian_mask[j][i] > 0.65:
            angles_around_index = [math.degrees(self._angles[j - k][i - l]) for k, l in self._core_map]
            index = 0
            for k in range(0, 8):

                # calculate the difference
                difference = angles_around_index[k] - angles_around_index[k + 1]
                if difference > 90:
                    difference -= 180
                elif difference < -90:
                    difference += 180

                index += difference

            if 180 - tolerance <= index <= 180 + tolerance:
                #delta
                self._list_core_points.append(Core_Point(posy= j, posx= i, angle= self._angles[j][i], point_type='d'))
            if -180 - tolerance <= index <= -180 + tolerance:
                #loop
                self._list_core_points.append(Core_Point(posy= j, posx= i, angle= self._angles[j][i], point_type='l'))
            if 360 - tolerance <= index <= 360 + tolerance:
                #whorl
                self._list_core_points.append(Core_Point(posy= j, posx= i, angle= self._angles[j][i], point_type='w'))

    def __ezquel_to_image(self):
        self._ezquel_as_image = np.zeros(shape=(self._rows, self._columns), dtype='uint8')
        im_max = self._ezquel_fingerprint.max()

        if im_max >= 1:
            self._ezquel_as_image[0:self._rows][:, 0:self._columns] = (((-255) * (self._ezquel_fingerprint/im_max)) + 255).astype('uint8')
        else:
            self._void_image = True

        

    def describe_fingerprint(self, data_fingerprint, angles_tolerance=1):
        self.__reconstruction_fingerprint(data_fingerprint)
        self.__get_quality_index()
        self.__fingerprint_enhance()
        self._ezquel_fingerprint = self._ezquel_fingerprint.astype('uint8')
        print('Index quality: {}\nImage quality: {}'.format(self._quality_index, self._varian_index))
        self.__ezquel_to_image()
        if not self._void_image:
            self.__get_cells()
            self.__get_minutias()
            self.__get_corepoints(angles_tolerance)
            for core in self._list_core_points:
                print(core.get_description())
            for minutia in self._list_minutias:
                print(minutia.get_description())