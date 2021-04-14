# -*- coding: utf-8 -*-


class Characteristic_Point(object):
    def __init__(self, posy= 0, posx= 0, angle= 0.0, type='n'):
        self.posy = posy
        self.posx = posx
        self.angle = angle
        self.type = type

        #self.marked_image = []

    def get_posy(self):
        return self.posy
    
    def get_posx(self):
        return self.posx

    def get_angle(self):
        return self.angle

    def get_type(self):
        return self.type

    

