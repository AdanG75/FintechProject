import json
from typing import List, Tuple, Union
import uuid

from redis.client import Redis
from sqlalchemy.orm import Session

from controller.characteristic_point_controller import get_json_of_minutiae_list, get_json_of_core_points_list
from controller.fingerprint_controller import describe_fingerprint_from_sample
from controller.movement_controller import get_all_movements_of_credit
from controller.user_controller import get_user_using_email, return_type_id_based_on_type_of_user, get_name_of_client, \
    get_name_of_market
from core.cache import batch_save
from db.models.credits_db import DbCredit
from db.orm.clients_orm import get_client_by_id_client
from db.orm.credits_orm import get_credits_by_id_client, get_credits_by_id_market, get_credit_by_id_credit, \
    get_credit_by_id_market_and_id_client, create_credit, approve_credit
from db.orm.exceptions_orm import type_of_value_not_compatible, existing_credit_exception, \
    type_of_user_not_compatible, not_values_sent_exception, cache_exception
from fingerprint_process.description.fingerprint import Fingerprint
from schemas.credit_base import CreditDisplay, CreditBasicRequest, CreditRequest
from schemas.credit_complex import OwnerInner, CreditComplexProfile, CreditComplexSummary, OwnersInner
from schemas.fingerprint_model import FingerprintB64
from schemas.type_credit import TypeCredit
from schemas.type_user import TypeUser
from secure.cipher_secure import cipher_data, decipher_data


def get_credits(db: Session, type_user: str, id_type: str) -> List[DbCredit]:
    if type_user == TypeUser.client.value:
        user_credits = get_credits_by_id_client(db, id_type)

    elif type_user == TypeUser.market.value:
        user_credits = get_credits_by_id_market(db, id_type)

    else:
        raise type_of_value_not_compatible

    if user_credits is None:
        user_credits = []

    return user_credits


async def new_credit(db: Session, request: CreditRequest, type_performer: str) -> CreditDisplay:
    credit_db = create_credit(db, request, type_performer)

    return CreditDisplay.from_orm(credit_db)


async def approve_credit_market(db: Session, id_credit: int) -> CreditDisplay:
    approved_credit = approve_credit(db, id_credit)

    return CreditDisplay.from_orm(approved_credit)


async def get_owner_credit(db: Session, id_credit: int, type_user: str) -> OwnerInner:
    """
    Return the owner client if a user of type market or system do the request and return the owner market
    if a client do the request

    :param db: (Session) A session of the database
    :param id_credit: (int) The id of credit which you wish to know the owner
    :param type_user: (str) The type of user that do the request. Can be: 'market', 'system' or 'client'

    :return: (OwnerInner) An object with the type of owner and its name
    """
    if type_user == TypeUser.client.value:
        credit = get_credit_by_id_credit(db, id_credit)
        name_owner = await get_name_of_market(db, credit.id_market)
        type_owner = TypeUser.market.value

    elif type_user == TypeUser.market.value or type_user == TypeUser.system.value:
        credit = get_credit_by_id_credit(db, id_credit)
        name_owner = await get_name_of_client(db, credit.id_client)
        type_owner = TypeUser.client.value

    else:
        raise type_of_value_not_compatible

    return OwnerInner(
        name_owner=name_owner,
        type_owner=type_owner
    )


async def get_name_of_the_owners_of_credit(
        db: Session,
        id_client: str,
        id_market: str
) -> Tuple[str, str]:
    client_name = await get_name_of_client(db, id_client)
    market_name = await get_name_of_market(db, id_market)

    return client_name, market_name


def check_owner_credit(db: Session, id_credit: int, type_owner: str, id_owner: str) -> bool:
    if type_owner == TypeUser.client.value:
        credit = get_credit_by_id_credit(db, id_credit)
        if credit.id_client == id_owner:
            return True

    elif type_owner == TypeUser.market.value or type_owner == TypeUser.system.value:
        credit = get_credit_by_id_credit(db, id_credit)
        if credit.id_market == id_owner:
            return True

    else:
        raise type_of_value_not_compatible

    return False


def check_client_have_credit_on_market(db: Session, id_client: str, id_market: str) -> bool:
    credit = get_credit_by_id_market_and_id_client(db, id_market, id_client)

    if credit is None:
        return False
    else:
        return True


async def get_credit_description(db: Session, id_credit: int, type_performer_user: str) -> CreditComplexProfile:
    movements_of_credit = await get_all_movements_of_credit(db, id_credit)
    owner_of__credit = await get_owner_credit(db, id_credit, type_performer_user)

    credit = get_credit_by_id_credit(db, id_credit)
    credit_display = CreditDisplay.from_orm(credit)

    return CreditComplexProfile(
        credit=credit_display,
        movements=movements_of_credit,
        owner=owner_of__credit
    )


async def generate_pre_credit(
        db: Session,
        r: Redis,
        pre_credit_order: CreditBasicRequest,
        id_performer: int,
        is_approved: bool
) -> CreditComplexSummary:
    if pre_credit_order.id_client is None:
        if pre_credit_order.client_email is None:
            raise not_values_sent_exception
        else:
            user = get_user_using_email(db, pre_credit_order.client_email)

            if user.type_user == TypeUser.client.value:
                id_client = return_type_id_based_on_type_of_user(db, user.id_user, 'client')
            else:
                raise type_of_user_not_compatible
    else:
        client = get_client_by_id_client(db, pre_credit_order.id_client)
        id_client = client.id_client

    if check_client_have_credit_on_market(db, id_client, pre_credit_order.id_market):
        raise existing_credit_exception

    client_name, market_name = await get_name_of_the_owners_of_credit(db, id_client, pre_credit_order.id_market)

    pre_credit = CreditRequest(
        id_client=id_client,
        id_market=pre_credit_order.id_market,
        id_account=None,
        alias_credit=pre_credit_order.alias_credit,
        type_credit=TypeCredit.local.value,
        amount=pre_credit_order.amount,
        is_approved=is_approved
    )

    ticket: str = uuid.uuid4().hex

    # Save pre-credit, id_requester and id_performer into cache using ticket as reference
    save_pre_credit_requester_and_performer_in_cache(r, ticket, pre_credit, id_client, id_performer, 'CRT')

    owners = OwnersInner(
        market_name=market_name,
        client_name=client_name
    )

    return CreditComplexSummary(
        credit=pre_credit,
        owners=owners,
        id_pre_credit=ticket
    )


def save_pre_credit_requester_and_performer_in_cache(
        r: Redis,
        ticket: str,
        pre_credit: Union[dict, CreditRequest],
        id_requester: str,
        id_performer: int,
        type_s: str
) -> bool:
    if isinstance(pre_credit, dict):
        pre_credit_str = json.dumps(pre_credit)
    elif isinstance(pre_credit, CreditRequest):
        pre_credit_str = pre_credit.json()
    else:
        raise type_of_value_not_compatible

    # Cipher credit's data to secure it
    secure_data = cipher_data(pre_credit_str)

    values_to_catching = {
        f'PRE-{type_s}-{ticket}': secure_data,
        f'RQT-{type_s}-{ticket}': id_requester,
        f'PFR-{type_s}-{ticket}': id_performer
    }
    result = batch_save(r, values_to_catching, seconds=1800)

    if result.count(False) > 0:
        raise cache_exception

    return True


def get_pre_credit_request_from_cache(r: Redis, id_order: Union[str, int], type_s: str = 'CRT') -> CreditRequest:
    pre_credit_cache = r.get(f'PRE-{type_s}-{id_order}')
    pre_credit_str = pre_credit_cache.decode('utf-8')
    pre_credit_json = decipher_data(pre_credit_str)

    return CreditRequest.parse_raw(pre_credit_json)


async def delete_pre_credit_requester_and_performer_in_cache(
        r: Redis,
        identifier: Union[str, int],
        type_s: str = 'CRT'
) -> bool:
    if r.exists(f'PRE-{type_s}-{identifier}', f'RQT-{type_s}-{identifier}', f'PFR-{type_s}-{identifier}') > 0:
        result = r.delete(f'PRE-{type_s}-{identifier}', f'RQT-{type_s}-{identifier}', f'PFR-{type_s}-{identifier}')

        return result > 0

    return True


async def save_precredit_fingerprint(r: Redis, id_order: str, fingerprint_object: FingerprintB64) -> bool:
    fingerprint: Fingerprint = await describe_fingerprint_from_sample(fingerprint_object.fingerprint)

    minutiae_str = get_json_of_minutiae_list(fingerprint.get_minutiae_list())
    # print(len(fingerprint.get_minutiae_list()))

    core_points_str = get_json_of_core_points_list(fingerprint.get_core_point_list())
    # print(len(fingerprint.get_core_point_list()))

    # Cipher minutiae_str and core_points_str
    minutiae_secure = cipher_data(minutiae_str)
    core_points_secure = cipher_data(core_points_str)

    # Save cipher data into Redis
    save_minutiae_and_core_points_secure_in_cache(r, minutiae_secure, core_points_secure, id_order, 'CRT')

    return True


def save_minutiae_and_core_points_secure_in_cache(
        r: Redis,
        minutiae_secure: str,
        core_points_secure: str,
        id_order: str,
        type_s: str
) -> bool:
    values_to_catching = {
        f'MNT-{type_s}-{id_order}': minutiae_secure,
        f'CRP-{type_s}-{id_order}': core_points_secure
    }
    result = batch_save(r, values_to_catching, seconds=1800)

    if result.count(False) > 0:
        raise cache_exception

    return True
