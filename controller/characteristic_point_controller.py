import json
from typing import List, Union

from db.models.cores_db import DbCores
from db.models.minutiae_db import DbMinutiae
from db.orm.exceptions_orm import type_not_found_exception
from fingerprint_process.models.characteristic_point import CharacteristicPoint
from fingerprint_process.models.core_point import CorePoint
from fingerprint_process.models.minutia import Minutiae
from schemas.characteristic_point_base import CPBase
from web_utils.web_functions import serialize_base_model_object_to_json_str


def get_json_of_minutiae_list(minutiae: List[Minutiae]) -> str:
    cp_basics = parse_cp_object_list_to_cp_basic_list(minutiae)

    return serialize_base_model_object_to_json_str(cp_basics)


def get_json_of_core_points_list(core_points: List[CorePoint]) -> str:
    cp_basics = parse_cp_object_list_to_cp_basic_list(core_points)

    return serialize_base_model_object_to_json_str(cp_basics)


def from_json_get_minutiae_list_object(json_str: str) -> List[Minutiae]:
    """
    Parse a JSON string to a list of Minutiae Object. The JSON string should be formatted by CPBase Object

    :param json_str: (str) A string formatted like a list of CPBase
    :return: List[Minutiae] A list of Minutiae
    """
    return from_json_get_cp_list(json_str, 'Minutia')


def from_json_get_core_point_list_object(json_str: str) -> List[CorePoint]:
    """
    Parse a JSON string to a list of CorePoint Object. The JSON string should be formatted by CPBase Object

    :param json_str: (str) A string formatted like a list of CPBase
    :return: List[CorePoint] A list of CorePoints
    """
    return from_json_get_cp_list(json_str, 'Core')


def from_json_get_cp_list(json_str: str, cp_type: str) -> list:
    raw_list = json.loads(json_str)

    if len(raw_list) > 0:
        cps = []
        for element in raw_list:
            if isinstance(element, str):
                element_dict = json.loads(element)
                cp = parse_dict_to_cp_point(element_dict, cp_type)
            else:
                cp = parse_dict_to_cp_point(element, cp_type)

            cps.append(cp)

        return cps

    return []


def parse_cp_object_list_to_cp_basic_list(characteristics_points: List[CharacteristicPoint]) -> List[CPBase]:
    if len(characteristics_points) > 0:
        cp_basics = []
        for cp in characteristics_points:
            cp_basic = parse_CharacteristicPoint_to_CPBase(cp)
            cp_basics.append(cp_basic)

        return cp_basics

    return []


def parse_CharacteristicPoint_to_CPBase(characteristic_point: CharacteristicPoint) -> CPBase:
    return CPBase(
        id_point=characteristic_point.get_minutiae_id(),
        pos_x=characteristic_point.get_posx(),
        pos_y=characteristic_point.get_posy(),
        angle=characteristic_point.get_angle(),
        type_point=characteristic_point.get_point_type()
    )


def parse_CPBase_to_Minutiae(cp_schema: CPBase) -> Minutiae:
    return Minutiae(
        posy=cp_schema.pos_x,
        posx=cp_schema.pos_x,
        angle=cp_schema.angle,
        point_type=cp_schema.type_point.value
    )


def parse_CPBase_to_CorePoint(cp_schema: CPBase) -> CorePoint:
    return CorePoint(
        posy=cp_schema.pos_x,
        posx=cp_schema.pos_x,
        angle=cp_schema.angle,
        point_type=cp_schema.type_point.value
    )


def parse_db_list_to_cp_list(db_list: Union[List[DbMinutiae], List[DbCores]], cp_type: str) -> list:
    if cp_type.lower() == 'minutia':
        minutiae_obj = []
        for minutia_db in db_list:
            minutia_obj = parse_minutia_db_to_minutia(minutia_db)
            minutiae_obj.append(minutia_obj)

        return minutiae_obj

    elif cp_type.lower() == 'core':
        cores_obj = []
        for core_db in db_list:
            core_obj = parse_core_point_db_to_core_point(core_db)
            cores_obj.append(core_obj)

        return cores_obj

    else:
        raise type_not_found_exception


def parse_minutia_db_to_minutia(minutia_db: DbMinutiae) -> Minutiae:
    return Minutiae(
        posy=minutia_db.pos_y,
        posx=minutia_db.pos_x,
        angle=minutia_db.angle,
        point_type=minutia_db.type_minutia
    )


def parse_core_point_db_to_core_point(core_point_db: DbCores) -> CorePoint:
    return CorePoint(
        posy=core_point_db.pos_y,
        posx=core_point_db.pos_x,
        angle=core_point_db.angle,
        point_type=core_point_db.type_core
    )


def parse_dict_to_cp_point(element: dict, type_cp: str) -> Union[Minutiae, CorePoint]:
    """
    Parse a dict from CPBase to a Minutiae Object or a CorePoint Object

    :param element: (dict) The format should be similar to CPBase
    :param type_cp: (str) Can be 'minutia' or 'core'

    :return: Union[Minutiae, CorePoint] Return a Minutiae or CorePoint Object based on type_cp
    """
    if type_cp.lower() == 'minutia':
        return Minutiae(posy=element['pos_y'], posx=element['pos_x'],
                        angle=element['angle'], point_type=element['type_point'])
    elif type_cp.lower() == 'core':
        return CorePoint(posy=element['pos_y'], posx=element['pos_x'],
                         angle=element['angle'], point_type=element['type_point'])
    else:
        raise type_not_found_exception
