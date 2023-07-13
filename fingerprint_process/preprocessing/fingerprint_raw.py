# -*- coding: utf-8 -*-
from typing import Union

import numpy as np

from core.utils import cast_base64_to_bytes


class FingerprintRaw(object):
    def __init__(self, width=256, height=288):
        super().__init__()
        self.width = width
        self.height = height
        self.fingerprint_length = int(self.height * self.width)
        self.read_length_fingerprint = int(self.fingerprint_length / 2)
        self.mask = 0b00001111
        self.data_fingerprint_raw = []

        self.default_response = (False,)

    def get_fingerprint_raw(self, data: Union[str, list] = None):
        """
        Convert an IntArray to fingerprint raw data

        :param data: An Int array (len = width*height/2) or a string encoded in base64
            which contain the data of a fingerprint

        :return: A fingerprint raw data object (len = width*height)
        """
        if data is None:
            data = []

        self.data_fingerprint_raw = np.zeros(self.fingerprint_length, 'uint8')
        data_bytes = cast_base64_to_bytes(data) if isinstance(data, str) else data.copy()

        if len(data_bytes) == self.read_length_fingerprint:
            count = 0
            for nibble in data_bytes:
                # byte = nibble.to_bytes(1, 'big')
                byte = np.uint8(nibble)
                self.data_fingerprint_raw[count] = ((byte >> 4) * 17)
                count += 1
                self.data_fingerprint_raw[count] = ((byte & self.mask) * 17)
                count += 1
        else:
            return self.default_response

        return self.data_fingerprint_raw
