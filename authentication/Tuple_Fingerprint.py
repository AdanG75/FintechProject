# -*- coding: utf-8 -*-
import uuid

class Tuple_Fingerprint(object):
    def __init__(self) -> None:
        super().__init__()
        self._id = uuid.uuid4().hex
        self._id_minutiae = ''
        self._ratio = 0.0
        self._angle = 0.0
        self._origin_minutiae_type = 'x'
        self._destination_minutiae_type = 'x'
