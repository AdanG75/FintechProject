from typing import List

from sqlalchemy.orm import Session

from controller.movement_controller import get_all_movements_of_credit
from db.models.credits_db import DbCredit
from db.orm.clients_orm import get_client_by_id_client
from db.orm.credits_orm import get_credits_by_id_client, get_credits_by_id_market, get_credit_by_id_credit
from db.orm.exceptions_orm import type_of_value_not_compatible
from db.orm.markets_orm import get_market_by_id_market
from db.orm.users_orm import get_user_by_id
from schemas.credit_base import CreditDisplay
from schemas.credit_complex import OwnerInner, CreditComplexProfile
from schemas.type_user import TypeUser


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
        market = get_market_by_id_market(db, credit.id_market)
        user = get_user_by_id(db, market.id_user)
        name_owner = user.name
        type_owner = user.type_user

    elif type_user == TypeUser.market.value or type_user == TypeUser.system.value:
        credit = get_credit_by_id_credit(db, id_credit)
        client = get_client_by_id_client(db, credit.id_client)
        user = get_user_by_id(db, client.id_user)
        name_owner = f'{user.name} {client.last_name}'
        type_owner = TypeUser.client.value

    else:
        raise type_of_value_not_compatible

    return OwnerInner(
        name_owner=name_owner,
        type_owner=type_owner
    )


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
