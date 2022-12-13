import json
from typing import List, Tuple, Union, Optional
import uuid

from redis.client import Redis
from sqlalchemy.orm import Session

from controller.characteristic_point_controller import save_minutiae_and_core_points_secure_in_cache
from controller.fingerprint_controller import get_minutiae_and_core_points_from_sample
from controller.secure_controller import cipher_minutiae_and_core_points
from controller.user_controller import get_user_using_email, return_type_id_based_on_type_of_user, get_name_of_client, \
    get_name_of_market
from db.cache.cache import batch_save
from core.utils import money_str_to_float
from db.models.credits_db import DbCredit
from db.orm.clients_orm import get_client_by_id_client
from db.orm.credits_orm import get_credits_by_id_client, get_credits_by_id_market, get_credit_by_id_credit, \
    get_credit_by_id_market_and_id_client, create_credit, approve_credit
from db.orm.exceptions_orm import type_of_value_not_compatible, existing_credit_exception, \
    type_of_user_not_compatible, not_values_sent_exception, cache_exception, not_sufficient_funds_exception
from schemas.credit_base import CreditDisplay, CreditBasicRequest, CreditRequest
from schemas.credit_complex import OwnerInner, CreditComplexProfile, CreditComplexSummary, OwnersInner
from schemas.fingerprint_model import FingerprintB64
from schemas.movement_complex import BasicExtraMovement
from schemas.type_credit import TypeCredit
from schemas.type_user import TypeUser
from secure.cipher_secure import cipher_data, decipher_data


def get_credit_using_its_id(db: Session, id_credit: int) -> DbCredit:
    return get_credit_by_id_credit(db, id_credit)


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


def get_id_of_owners_of_credit(db: Session, id_credit: int) -> Tuple[str, str]:
    """
    Return the id_client and id_market, in that order, as a tuple

    :param db: (Session) An instance on the DB
    :param id_credit: (int) ID of credit which we wish to know the owners' ID
    :return: (Tuple[str, str]) The client's id and market's id, in that order, of owners of credit
    """

    credit = get_credit_by_id_credit(db, id_credit)

    return credit.id_client, credit.id_market


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


def check_owners_of_credit(db: Session, id_credit: int, id_client: str, id_market: str) -> bool:
    credit = get_credit_by_id_credit(db, id_credit)

    if credit.id_market == id_market and credit.id_client == id_client:
        return True
    else:
        return False


def check_client_have_credit_on_market(db: Session, id_client: str, id_market: str) -> bool:
    credit = get_credit_by_id_market_and_id_client(db, id_market, id_client)

    if credit is None:
        return False
    else:
        return True


def check_funds_of_credit(
        db: Session,
        amount: Union[str, float],
        id_credit: Optional[int] = None,
        credit_obj: Optional[DbCredit] = None
) -> bool:
    if credit_obj is None:
        if id_credit is not None:
            credit_obj = get_credit_by_id_credit(db, id_credit)
        else:
            raise not_values_sent_exception

    amount_float = money_str_to_float(amount) if isinstance(amount, str) else amount

    actual_amount_float = money_str_to_float(credit_obj.amount) \
        if isinstance(credit_obj.amount, str) else credit_obj.amount

    if amount_float > actual_amount_float:
        raise not_sufficient_funds_exception

    return True


async def get_credit_description(
        db: Session,
        id_credit: int,
        type_performer_user: str,
        movements_of_credit: List[BasicExtraMovement]
) -> CreditComplexProfile:
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
    minutiae, c_points = await get_minutiae_and_core_points_from_sample(fingerprint_object.fingerprint)

    # Cipher minutiae and core points
    minutiae_secure, core_points_secure = await cipher_minutiae_and_core_points(minutiae, c_points)

    # Save cipher data into Redis
    save_minutiae_and_core_points_secure_in_cache(r, minutiae_secure, core_points_secure, id_order, 'CRT')

    return True
