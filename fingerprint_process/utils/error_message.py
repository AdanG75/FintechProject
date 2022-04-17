# -*- coding: utf-8 -*-

class ErrorMessage(object):
    def __init__(self) -> None:
        super().__init__()
        self._FINGERPRINT_OK = 0
        self._POOR_QUALITY = 1
        self._FEW_MINUTIAES = 2
        self._VOID_FINGERPRINT = 3
        self._DONT_MATCH_FINGERPRINT = 4
        self._MATCH_FINGERPRINT = 5
        self._WRONG_ANGLES = 6
        self._NOT_OPTION_FOUND = 7
        self._RECONSTRUCTION_FAILED = 8

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
        elif error_code == self._NOT_OPTION_FOUND:
            print('\n\tOption couldn\'t be found')
        elif error_code == self._RECONSTRUCTION_FAILED:
            print('\n\tReconstruction fingerprint failed')
        else:
            print('\n\tUnknown Error')

    @property
    def FINGERPRINT_OK(self):
        return self._FINGERPRINT_OK

    @property
    def POOR_QUALITY(self):
        return self._POOR_QUALITY

    @property
    def FEW_MINUTIAES(self):
        return self._FEW_MINUTIAES

    @property
    def VOID_FINGERPRINT(self):
        return self._VOID_FINGERPRINT

    @property
    def DONT_MATCH_FINGERPRINT(self):
        return self._DONT_MATCH_FINGERPRINT

    @property
    def MATCH_FINGERPRINT(self):
        return self._MATCH_FINGERPRINT

    @property
    def WRONG_ANGLES(self):
        return self._WRONG_ANGLES

    @property
    def NOT_OPTION_FOUND(self):
        return self._NOT_OPTION_FOUND

    @property
    def RECONSTRUCTION_FAILED(self):
        return self._RECONSTRUCTION_FAILED
