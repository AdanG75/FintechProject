from typing import List

from sqlalchemy.orm import Session

from db.models.credits_db import DbCredit
from db.orm.credits_orm import get_credits_by_id_client, get_credits_by_id_market
from db.orm.exceptions_orm import type_of_value_not_compatible
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
