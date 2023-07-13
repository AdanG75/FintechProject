# -*- coding: utf-8 -*-
import uuid


class TupleFingerprint(object):
    def __init__(self, id_minutiae, ratio, angle, origin_minutiae_type, destination_minutiae_type) -> None:
        super().__init__()
        self._id = uuid.uuid4().hex
        self._id_minutiae = id_minutiae
        self._ratio = ratio
        self._angle = angle
        self._origin_minutiae_type = origin_minutiae_type
        self._destination_minutiae_type = destination_minutiae_type

    def get_description(self):
        return (self._id, self._id_minutiae, self._ratio, self._angle, self._origin_minutiae_type,
                self._destination_minutiae_type)

    def get_tuple_id(self):
        return self._id

    def get_id_owner_minutiae(self):
        return self._id_minutiae

    def get_ratio(self):
        return self._ratio

    def get_angle(self):
        return self._angle

    def get_origin_minutiae_type(self):
        return self._origin_minutiae_type

    def get_destination_minutiae_type(self):
        return self._destination_minutiae_type
