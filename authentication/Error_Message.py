# -*- coding: utf-8 -*-

class Error_Message(object):
    def __init__(self) -> None:
        super().__init__()
        self._FINGERPRINT_OK = 0
        self._POOR_QUALITY = 1
        self._FEW_MINUTIAES = 2
        self._VOID_FINGERPRINT = 3

    def show_message(self, error_code):
        if error_code == self._FINGERPRINT_OK:
            print('\n\tProcess finished successfully')
        elif error_code == self._POOR_QUALITY:
            print('\n\tPoor quality fingerpint')
        elif error_code == self._FEW_MINUTIAES:
            print('\n\tFew minutiaes have been finding')
        elif error_code == self._VOID_FINGERPRINT:
            print('\n\tFingerprint imaga is void')
        else:
            print('\n\tUnknown Error')