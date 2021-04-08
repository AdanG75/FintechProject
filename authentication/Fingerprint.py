import numpy as np

class Fingerprint(object):
    def __init__(self, fingerprint_rows = 288, figerprint_columns = 256):
        self.fingerprint_rows = fingerprint_rows
        self.figerprint_columns = figerprint_columns

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
        pass

    def get_quality_index(self):
        pass

    def get_corepoints(self):
        pass

    def get_minutias(self):
        pass

