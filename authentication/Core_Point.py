# -*- coding: utf-8 -*-
from Characteristic_Point import Characteristic_Point

class Core_Point(Characteristic_Point):
    def __init__(self, posy, posx, angle, point_type) -> None:
        super().__init__(posy, posx, angle, point_type)