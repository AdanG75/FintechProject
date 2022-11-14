from typing import Union, Optional, Tuple, List

from redis import Redis

from controller.characteristic_point_controller import from_json_get_minutiae_list_object, \
    from_json_get_core_point_list_object
from core.cache import is_the_same, item_save, check_item_if_exist
from db.orm.exceptions_orm import not_longer_available_exception, operation_need_authorization_exception
from fingerprint_process.models.core_point import CorePoint
from fingerprint_process.models.minutia import Minutiae
from secure.cipher_secure import decipher_data


AUTH_OK: str = 'OK'
AUTH_WRONG: str = 'WR'


def check_performer_in_cache(
        r: Redis,
        identifier: Union[str, int],
        actual_performer: Union[str, int]
) -> Optional[bool]:
    above_performer = r.get(f'PFR-{identifier}')
    if above_performer is None:
        return None
    else:
        return is_the_same(above_performer, actual_performer)


def get_fingerprint_auth_data(r: Redis, identifier: Union[str, int]) -> Tuple[List[Minutiae], List[CorePoint]]:
    mnt_cache = r.get(f'MNT-{identifier}')
    crp_cache = r.get(f'CRP-{identifier}')

    if mnt_cache is not None and crp_cache is not None:
        mnt_str = mnt_cache.decode('utf-8')
        mnt_json = decipher_data(mnt_str)
        minutiae = from_json_get_minutiae_list_object(mnt_json)

        crp_str = crp_cache.decode('utf-8')
        crp_json = decipher_data(crp_str)
        core_points = from_json_get_core_point_list_object(crp_json)
    else:
        raise not_longer_available_exception

    return minutiae, core_points


async def delete_fingerprint_auth_data(r: Redis, identifier: Union[str, int]) -> bool:
    if r.exists(f'MNT-{identifier}', f'CRP-{identifier}') > 0:
        result = r.delete(f'MNT-{identifier}', f'CRP-{identifier}')

        return result > 0

    return True


def get_requester_from_cache(r: Redis, identifier: Union[str, int]) -> str:
    requester = r.get(f'RQT-{identifier}')
    if requester is None:
        raise not_longer_available_exception

    return requester.decode('utf-8')


def add_attempt_cache(r: Redis, identifier: Union[str, int], type_s: str) -> bool:
    if r.exists(f'ATM-{type_s}-{identifier}') > 0:
        attempts = r.get(f'ATM-{type_s}-{identifier}')
        if int(attempts) > 7:
            raise not_longer_available_exception
        else:
            r.incr(f'ATM-{type_s}-{identifier}')

    else:
        return item_save(r, f'ATM-{type_s}-{identifier}', 1, seconds=1800)

    return True


def erase_attempt_cache(r: Redis, identifier: Union[str, int], type_s: str) -> bool:
    if r.exists(f'ATM-{type_s}-{identifier}') > 0:
        result = r.delete(f'ATM-{type_s}-{identifier}')

        return result > 0

    return True


def save_auth_result(r: Redis, identifier: Union[str, int], type_s: str, auth_result: bool) -> bool:
    if auth_result:
        return item_save(r, f'RST-{type_s}-{identifier}', AUTH_OK, seconds=1800)
    else:
        return item_save(r, f'RST-{type_s}-{identifier}', AUTH_WRONG, seconds=1800)


def check_auth_result(r: Redis, identifier: Union[str, int], type_s: str) -> bool:
    check_auth = check_item_if_exist(r, f'RST-{type_s}-{identifier}', AUTH_OK)
    if check_auth is None:
        raise operation_need_authorization_exception

    return check_auth


async def delete_auth_resul(r: Redis, identifier: Union[str, int], type_s: str) -> bool:
    result = r.delete(f'RST-{type_s}-{identifier}')

    return result > 0

