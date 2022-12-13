from typing import Union, Optional, Tuple, List

from redis import Redis

from controller.characteristic_point_controller import from_json_get_minutiae_list_object, \
    from_json_get_core_point_list_object
from core.logs import show_error_message
from db.cache.cache import is_the_same, item_save, check_item_if_exist
from db.orm.exceptions_orm import not_longer_available_exception, operation_need_authorization_exception, \
    cache_exception
from fingerprint_process.models.core_point import CorePoint
from fingerprint_process.models.minutia import Minutiae
from secure.cipher_secure import decipher_data


AUTH_OK: str = 'OK'
AUTH_WRONG: str = 'WR'


async def save_value_in_cache_with_formatted_name(
        r: Redis,
        subject: str,
        type_s: str,
        identifier: Union[str, int],
        value: Union[int, float, str, bool, bytes],
        seconds: int
) -> bool:
    if 1 > len(subject) or len(subject) > 9:
        raise ValueError("Subject too long or too short")

    if 1 > len(type_s) or len(type_s) > 9:
        raise ValueError("Type movement too long or too short")

    if isinstance(identifier, str):
        if 3 > len(identifier) or len(identifier) > 50:
            raise ValueError("Identifier too long or too short")

    value = str(value) if isinstance(value, bool) else value

    key = f'{subject}-{type_s}-{identifier}'

    return item_save(r, key, value, seconds)


async def delete_values_in_cache(
        r: Redis,
        subject: str,
        type_s: str,
        identifier: Union[str, int]
) -> bool:
    if r.exists(f'{subject}-{type_s}-{identifier}') > 0:
        try:
            result = r.delete(f'{subject}-{type_s}-{identifier}')
        except Exception as e:
            show_error_message(e)
            raise cache_exception

        return result > 0

    return True


async def save_performer_in_cache(
        r: Redis,
        type_s: str,
        identifier: Union[str, int],
        value: Union[int, float, str, bool, bytes],
        seconds: int = 3600
) -> bool:
    return await save_value_in_cache_with_formatted_name(r, 'PFR', type_s, identifier, value, seconds)


async def save_requester_in_cache(
        r: Redis,
        type_s: str,
        identifier: Union[str, int],
        value: Union[int, float, str, bool, bytes],
        seconds: int = 3600
) -> bool:
    return await save_value_in_cache_with_formatted_name(r, 'RQT', type_s, identifier, value, seconds)


def check_performer_in_cache(
        r: Redis,
        identifier: Union[str, int],
        type_s: str,
        actual_performer: Union[str, int]
) -> Optional[bool]:
    above_performer = r.get(f'PFR-{type_s}-{identifier}')
    if above_performer is None:
        return None
    else:
        return is_the_same(above_performer, actual_performer)


def get_requester_from_cache(r: Redis, type_s: str, identifier: Union[str, int]) -> str:
    requester = r.get(f'RQT-{type_s}-{identifier}')
    if requester is None:
        raise not_longer_available_exception

    return requester.decode('utf-8')


async def delete_performer_in_cache(r: Redis, type_s: str, identifier: Union[str, int]) -> bool:
    return await delete_values_in_cache(r, 'PFR', type_s, identifier)


async def delete_requester_in_cache(r: Redis, type_s: str, identifier: Union[str, int]) -> bool:
    return await delete_values_in_cache(r, 'RQT', type_s, identifier)


def get_fingerprint_auth_data(
        r: Redis, type_s: str, identifier: Union[str, int]
) -> Tuple[List[Minutiae], List[CorePoint]]:
    mnt_cache = r.get(f'MNT-{type_s}-{identifier}')
    crp_cache = r.get(f'CRP-{type_s}-{identifier}')

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


async def delete_fingerprint_auth_data(r: Redis, type_s: str, identifier: Union[str, int]) -> bool:
    if r.exists(f'MNT-{type_s}-{identifier}', f'CRP-{type_s}-{identifier}') > 0:
        result = r.delete(f'MNT-{type_s}-{identifier}', f'CRP-{type_s}-{identifier}')

        return result > 0

    return True


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


async def save_type_auth_movement_cache(r: Redis, identifier: int, type_auth: str, seconds: int = 3600) -> bool:
    return await save_value_in_cache_with_formatted_name(r, 'TAU', 'MOV', identifier, type_auth, seconds)


async def get_type_auth_movement_cache(r: Redis, identifier: int) -> str:
    requester = r.get(f'TAU-MOV-{identifier}')
    if requester is None:
        raise not_longer_available_exception

    return requester.decode('utf-8')


async def check_type_auth_movement_cache(r: Redis, identifier: int, wished_type: str) -> Optional[bool]:
    auth_type = r.get(f'TAU-MOV-{identifier}')
    if auth_type is None:
        return None
    else:
        return is_the_same(auth_type, wished_type)


async def delete_type_auth_movement_cache(r: Redis, identifier: int) -> bool:
    return await delete_values_in_cache(r, 'TAU', 'MOV', identifier)


async def check_auth_movement_result(r: Redis, subject: str, identifier: Union[str, int], type_s: str) -> bool:
    check_auth = check_item_if_exist(r, f'{subject}-{type_s}-{identifier}', AUTH_OK)
    if check_auth is None:
        raise operation_need_authorization_exception

    return check_auth


async def delete_full_data_movement_cache(r: Redis, identifier: int) -> bool:
    if r.exists(f'PFR-MOV-{identifier}', f'MNT-MOV-{identifier}', f'CRP-MOV-{identifier}',
                f'ATM-MOV-{identifier}', f'TAU-MOV-{identifier}', f'F-AUTH-MOV-{identifier}',
                f'P-AUTH-MOV-{identifier}') > 0:

        result = r.delete(f'PFR-MOV-{identifier}', f'MNT-MOV-{identifier}', f'CRP-MOV-{identifier}',
                          f'ATM-MOV-{identifier}', f'TAU-MOV-{identifier}', f'F-AUTH-MOV-{identifier}',
                          f'P-AUTH-MOV-{identifier}')

        return result > 0

    return True


async def save_finish_movement_cache(r: Redis, identifier: int) -> bool:
    return await save_value_in_cache_with_formatted_name(r, 'FNS', 'MOV', identifier, True, 3600)


async def check_if_is_movement_finnish(r: Redis, identifier: int) -> bool:
    movement_finnish = r.get(f'FNS-MOV-{identifier}')
    if movement_finnish is None:
        return False
    else:
        return is_the_same(movement_finnish, True)


async def save_paypal_money_cache(r: Redis, identifier: int, amount: Union[int, float, str]) -> bool:
    return await save_value_in_cache_with_formatted_name(r, 'P-MNY', 'MOV', identifier, amount, 3600)


async def get_paypal_money_cache(r: Redis, identifier: int) -> Optional[float]:
    paypal_amount = r.get(f'P-MNY-MOV-{identifier}')
    if paypal_amount is None:
        return None

    return float(paypal_amount)


async def delete_paypal_money_cache(r: Redis, identifier: int) -> bool:
    return await delete_values_in_cache(r, 'P-MNY', 'MOV', identifier)
