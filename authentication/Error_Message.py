# -*- coding: utf-8 -*-

class Error_Message(object):
    def __init__(self) -> None:
        super().__init__()
        self._FINGERPRINT_OK = 0
        self._POOR_QUALITY = 1
        self._FEW_MINUTIAES = 2
        self._VOID_FINGERPRINT = 3
        self._DONT_MATCH_FINGERPRINT = 4
        self._MATCH_FINGERPRINT = 5
        self._WRONG_ANGLES = 6


    def show_message(self, error_code):
        if error_code == self._FINGERPRINT_OK:
            print('\n\tProcess finished successfully')
        elif error_code == self._POOR_QUALITY:
            print('\n\tPoor quality fingerpint')
        elif error_code == self._FEW_MINUTIAES:
            print('\n\tFew minutiaes have been finding')
        elif error_code == self._VOID_FINGERPRINT:
            print('\n\tFingerprint image is void')
        elif error_code == self._DONT_MATCH_FINGERPRINT:
            print('\n\tFingerprints do not match')
        elif error_code == self._MATCH_FINGERPRINT:
            print('\n\tFingerprints successfully matching')
        elif error_code == self._WRONG_ANGLES:
            print('\n\tAngles do not 180°')
        else:
            print('\n\tUnknown Error')