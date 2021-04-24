# -*- coding: utf-8 -*-
import uuid

class Tuple_Fingerprint(object):
    def __init__(self, id_minutiae, ratio, angle, origin_minutiae_type, destination_minutiae_type) -> None:
        super().__init__()
        self._id = uuid.uuid4().hex
        self._id_minutiae = id_minutiae
        self._ratio = ratio
        self._angle = angle
        self._origin_minutiae_type = origin_minutiae_type
        self._destination_minutiae_type = destination_minutiae_type

    def get_description(self):
        return (self._id, self._id_minutiae, self._ratio, self._angle, self._origin_minutiae_type, self._destination_minutiae_type)
