# -*- coding: utf-8 -*-
from fingerprint_process.models.characteristic_point import CharacteristicPoint


class CorePoint(CharacteristicPoint):
    def __init__(self, posy, posx, angle, point_type) -> None:
        super().__init__(posy, posx, angle, point_type)
