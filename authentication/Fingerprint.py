# -*- coding: utf-8 -*-

import numpy as np
import cv2 as cv
from math import degrees
from Quality_Image import Quality_Fingerprint
from Preprocessing_Fingerprint import PreprocessingFingerprint
from Minutia import Minutiae
from Core_Point import Core_Point
from Local_Area import Local_Area
from Error_Message import Error_Message


class Fingerprint(Error_Message):
    def __init__(self, fingerprint_rows = 288, figerprint_columns = 256, name_fingerprint = 'fingerprint', 
                show_result = True, save_result = True, size_window_minutiae = 3, size_window_core = 1, 
                address_image = './authentication/preprocessingFingerprints/', address_data = './authentication/data/', 
                characteritic_point_thresh = 0.6, ridge_segment_thresh = 0.25, authentication_index_score = 0.52,
                authentication_image_score = 0.35, register_index_score = 0.62, register_cpthresh = 0.3,
                register_rsthresh = 0.15, number_minutiae_neighbordings = 5):
        super().__init__()
        self._fingerprint_rows = fingerprint_rows
        self._figerprint_columns = figerprint_columns
        self._name_fingerprint = name_fingerprint
        self._show_result = show_result
        self._save_result = save_result
        self._size_window_minutiae = size_window_minutiae
        self._size_window_core = size_window_core
        self._address_image  = address_image 
        self._address_data = address_data
        self._characteritic_point_thresh = characteritic_point_thresh
        self._ridge_segment_thresh = ridge_segment_thresh
        self._authentication_index_score = authentication_index_score
        self._authentication_image_score = authentication_image_score
        self._register_index_score = register_index_score
        self._register_cpthresh = register_cpthresh
        self._register_rsthresh = register_rsthresh
        self._number_minutiae_neighbordings = number_minutiae_neighbordings

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
        self._raw_image = np.zeros((self._fingerprint_rows, self._figerprint_columns))
        x = 0
        y = 0
        for pixel in data_fingerprint:
            self._raw_image[y][x] = pixel
            if (x == (self._figerprint_columns - 1)):
                y += 1
                x = 0
            else:
                x += 1


    def __fingerprint_enhance(self):
        preprocessing_fp = PreprocessingFingerprint(name_fingerprint= self._name_fingerprint, address_output= self._address_image, ridge_segment_thresh= self._ridge_segment_thresh)
        (self._ezquel_fingerprint, self._roi, self._angles, self._varian_mask, self._varian_index ) = preprocessing_fp.enhance(img=self._raw_image, resize=False, return_as_image = False, show_fingerprints = self._show_result, save_fingerprints = self._save_result)
        (self._rows, self._columns) = self._ezquel_fingerprint.shape
        

    def __get_quality_index(self):
        quality_image = Quality_Fingerprint(numberFilters = 16, columnsImage = self._figerprint_columns, rowsImage = self._fingerprint_rows, dataFilters = 'dataFilter.txt', showGraphs = self._show_result, address_output= self._address_data, name_fingerprint=self._name_fingerprint)
        self._quality_index = quality_image.getQualityFingerprint(self._raw_image, save_graphs = self._save_result)


    def __get_corepoints(self, angles_tolerance):
        for i in range(3, len(self._angles) - 2):             # Y
            for j in range(3, len(self._angles[i]) - 2):      # x
                # mask any singularity outside of the mask
                mask_slice = self._roi[(i-2)*self._size_window_core:(i+3)*self._size_window_core, (j-2)*self._size_window_core:(j+3)*self._size_window_core]
                mask_flag = np.sum(mask_slice)
                if mask_flag == (self._size_window_core*5)**2:
                    self.__poincare_index_at(i, j, angles_tolerance)
                    
        
        colors = {'l' : (0, 0, 255), 'd' : (0, 128, 255), 'w': (255, 153, 255)}
        figure = 'rectangle'
        to_show = 'core'
        self.__mark_characteristic_point(colors, figure, to_show)
        

    def __get_minutias(self):
        for i in range(1, self._columns - self._size_window_minutiae//2):
            for j in range(1, self._rows - self._size_window_minutiae//2):
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
                        cv.rectangle(result, ((i-1)*self._size_window_core, (j-1)*self._size_window_core), ((i+1)*self._size_window_core, (j+1)*self._size_window_core), colors[singularity], 3)
                    else:
                        pts = np.array([[i, j+1], [i-1, j-1], [i+1, j-1]], np.uint8)
                        cv.polylines(result, pts=[pts], isClosed=True, color=colors[singularity], thickness=2)

                if to_show == 'core':
                    self._core_map = result.copy()
                    self.__show_sample_fingerprint(title_image='Core points', data_image=self._core_map)
                    self.__save_sample_fingerprint(name_image='core_', image=self._core_map)

                    # if self._show_result:
                    #     cv.imshow('Core points', self._core_map)
                    #     cv.waitKey(0)
                    #     cv.destroyAllWindows()

                    # if self._save_result:
                    #     cv.imwrite(self._address_image + 'core_' +  self._name_fingerprint +'.bmp', (self._core_map))
                else:
                    self._minutiae_map = result.copy()
                    self.__show_sample_fingerprint(title_image='Minutiaes', data_image=self._minutiae_map)
                    self.__save_sample_fingerprint(name_image='minutiae_', image=self._minutiae_map)

                    # if self._show_result:
                    #     cv.imshow('Minutiaes', self._minutiae_map)
                    #     cv.waitKey(0)
                    #     cv.destroyAllWindows()

                    # if self._save_result:
                    #     cv.imwrite(self._address_image + 'minutiae_' +  self._name_fingerprint +'.bmp', (self._minutiae_map))
            

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
            if self._varian_mask[j][i] > self._characteritic_point_thresh:
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
                        angle = round(degrees(self._angles[j][i]), 2)
                        self._list_minutias.append(Minutiae(posy= j, posx= i, angle= angle, point_type='e'))

                if crossings == 3:
                    angle = round(degrees(self._angles[j][i]), 2)
                    self._list_minutias.append(Minutiae(posy= j, posx= i, angle= angle, point_type='b'))

    
    def __get_cells(self):
        if self._size_window_minutiae == 3:
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
        if self._varian_mask[j][i] > self._characteritic_point_thresh:
            angles_around_index = [degrees(self._angles[j - k][i - l]) for k, l in self._core_map]
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
                angle = round(degrees(self._angles[j][i]), 2)
                self._list_core_points.append(Core_Point(posy= j, posx= i, angle= angle, point_type='d'))
            if -180 - tolerance <= index <= -180 + tolerance:
                #loop
                angle = round(degrees(self._angles[j][i]), 2)
                self._list_core_points.append(Core_Point(posy= j, posx= i, angle= angle, point_type='l'))
            if 360 - tolerance <= index <= 360 + tolerance:
                #whorl
                angle = round(degrees(self._angles[j][i]), 2)
                self._list_core_points.append(Core_Point(posy= j, posx= i, angle= angle, point_type='w'))


    def __ezquel_to_image(self):
        self._ezquel_fingerprint = self._ezquel_fingerprint.astype('uint8')
        self._ezquel_as_image = np.zeros(shape=(self._rows, self._columns), dtype='uint8')
        im_max = self._ezquel_fingerprint.max()

        if im_max >= 1:
            self._ezquel_as_image[0:self._rows][:, 0:self._columns] = (((-255) * (self._ezquel_fingerprint/im_max)) + 255).astype('uint8')
        else:
            self._void_image = True


    def __show_sample_fingerprint(self, title_image, data_image):
        if self._show_result:
            cv.imshow(title_image, data_image)
            cv.waitKey(0)
            cv.destroyAllWindows()


    def __save_sample_fingerprint(self, name_image, image):
        if self._save_result:
            cv.imwrite(self._address_image + name_image +  self._name_fingerprint +'.bmp', (image))


    def __save_raw_fingerprint(self):
        self.__show_sample_fingerprint(title_image='Fingerprint', data_image=self._raw_image)
        self.__save_sample_fingerprint(name_image='raw_', image=self._raw_image)


    def show_characteristic_point_from_list(self, type_characteristic_point, mode='basic'):
        if type_characteristic_point == 'core':
            characteristic_points_list = self._list_core_points

        else:
            characteristic_points_list = self._list_minutias
            
        for characteristic_point in characteristic_points_list:
            if mode == 'basic':
                print(characteristic_point.get_description())
            else:
                uid_point, posy, posx, angle, point_type, description_tuple_list = characteristic_point.get_full_description()
                print(uid_point, posy, posx, angle, point_type)
                for fingerprint_tuple in description_tuple_list:
                    print("\t", fingerprint_tuple)

        print("Total {} points: {}".format(type_characteristic_point, len(characteristic_points_list)))

        print('\n*********************************************************************************************\n')


    def get_core_point_list(self):
        return self._list_core_points


    def get_minutiae_list(self):
        return self._list_minutias


    def get_fingerprint_image(self):
        return self._ezquel_as_image

    
    def reconstruction_fingerprint(self, data_fingerprint):
        self.__reconstruction_fingerprint(data_fingerprint)
        return self._raw_image
   

    def describe_fingerprint(self, data_fingerprint=[], angles_tolerance=1, from_image=False, fingerprint_image=None):
        if from_image:
            self._raw_image = np.asarray(fingerprint_image)
        else:
            self.__reconstruction_fingerprint(data_fingerprint)
            
        self.__get_quality_index()
        if self._quality_index > self._authentication_index_score:
            self._ridge_segment_thresh = self._register_rsthresh
        else:
            return self._POOR_QUALITY
            
        self.__save_raw_fingerprint()
        self.__fingerprint_enhance()
        print('Index quality: {}\nImage quality: {}'.format(self._quality_index, self._varian_index))
        
        self.__ezquel_to_image()
        
        
        if (self._varian_index > self._authentication_image_score):
            self._characteritic_point_thresh = self._register_cpthresh
        else:
            return self._POOR_QUALITY
        
        if not self._void_image:
            self.__get_cells()
            self.__get_minutias()
            self.__get_corepoints(angles_tolerance)
            if (len(self._list_minutias) < (self._number_minutiae_neighbordings + 1)):
                return self._FEW_MINUTIAES
            else:
                local_description = Local_Area()
                process_message = local_description.get_local_structure(self._list_minutias)
                
                return process_message
        else:
            return self._VOID_FINGERPRINT