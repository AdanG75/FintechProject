# -*- coding: utf-8 -*-
from fastapi import HTTPException
from starlette import status


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

    def show_message(self, error_code, web: bool = False):
        if error_code == self._FINGERPRINT_OK:
            if web:
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail='Process finished successfully'
                )
            else:
                print('\n\tProcess finished successfully')
        elif error_code == self._POOR_QUALITY:
            if web:
                raise HTTPException(
                    status_code=status.HTTP_418_IM_A_TEAPOT,
                    detail='Poor quality fingerprint'
                )
            else:
                print('\n\tPoor quality fingerprint')
        elif error_code == self._FEW_MINUTIAES:
            if web:
                raise HTTPException(
                    status_code=status.HTTP_418_IM_A_TEAPOT,
                    detail='Few minutiae have been finding'
                )
            else:
                print('\n\tFew minutiae have been finding')
        elif error_code == self._VOID_FINGERPRINT:
            if web:
                raise HTTPException(
                    status_code=status.HTTP_418_IM_A_TEAPOT,
                    detail='Fingerprint image is void'
                )
            else:
                print('\n\tFingerprint image is void')
        elif error_code == self._DONT_MATCH_FINGERPRINT:
            if web:
                raise HTTPException(
                    status_code=status.HTTP_418_IM_A_TEAPOT,
                    detail='Fingerprints do not match'
                )
            else:
                print('\n\tFingerprints do not match')
        elif error_code == self._MATCH_FINGERPRINT:
            if web:
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail='Fingerprints successfully matching'
                )
            else:
                print('\n\tFingerprints successfully matching')
        elif error_code == self._WRONG_ANGLES:
            if web:
                raise HTTPException(
                    status_code=status.HTTP_418_IM_A_TEAPOT,
                    detail='Angles do not 180°'
                )
            else:
                print('\n\tAngles do not 180°')
        elif error_code == self._NOT_OPTION_FOUND:
            if web:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Option couldn\'t be found'
                )
            else:
                print('\n\tOption couldn\'t be found')
        elif error_code == self._RECONSTRUCTION_FAILED:
            if web:
                raise HTTPException(
                    status_code=status.HTTP_418_IM_A_TEAPOT,
                    detail='Reconstruction fingerprint failed'
                )
            else:
                print('\n\tReconstruction fingerprint failed')
        else:
            if web:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Unknown Error'
                )
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
