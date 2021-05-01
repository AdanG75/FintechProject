# -*- coding: utf-8 -*-
from Characteristic_Point import Characteristic_Point
# from Tuple_Fingerprint import Tuple_Fingerprint

class Minutiae(Characteristic_Point):
    def __init__(self, posy, posx, angle, point_type) -> None:
        super().__init__(posy, posx, angle, point_type)
        self._tuple_fingerprint_list = []

    def set_tuple_fingerprint_list(self, tuple_fingerprint_list):
        self._tuple_fingerprint_list = tuple_fingerprint_list.copy()

    def get_tuple_fingerprint_list(self):
        return self._tuple_fingerprint_list

    def get_description(self):
        description_tuple_list = []
        for tuple_fingerprint in self._tuple_fingerprint_list:
            description = tuple_fingerprint.get_description()
            description_tuple_list.append(description)

        return (self.uid_point, self.posy, self.posx, self.angle, self.point_type, description_tuple_list)

    def get_short_descrption(self):
        return (self.uid_point, self.posy, self.posx, self.angle, self.point_type)