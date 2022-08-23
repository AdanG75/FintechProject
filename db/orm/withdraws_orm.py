import uuid
from sqlalchemy.orm import Session

from db.models.withdraws_db import DbWithdraw
from db.orm.exceptions_orm import type_of_value_not_compatible, movement_already_linked_exception, NotFoundException, \
    option_not_found_exception, element_not_found_exception, not_unique_value
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.movements_orm import check_type_and_status_of_movement
from schemas.withdraw_base import WithdrawRequest


@multiple_attempts
@full_database_exceptions
def create_withdraw(db: Session, request: WithdrawRequest, execute: str = 'now') -> DbWithdraw:
    check_type_and_status_of_movement(db, request.id_movement, 'withdraw')

    try:
        get_withdraw_by_id_movement(db, request.id_movement)
    except NotFoundException:
        withdraw_uuid = uuid.uuid4().hex
        id_withdraw = "WTD-" + withdraw_uuid

        new_withdraw = DbWithdraw(
            id_withdraw=id_withdraw,
            id_movement=request.id_movement,
            type_withdraw=request.type_withdraw.value
        )

        try:
            db.add(new_withdraw)
            if execute == 'now':
                db.commit()
                db.refresh(new_withdraw)
            elif execute == 'wait':
                pass
            else:
                raise option_not_found_exception
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    else:
        raise not_unique_value

    return new_withdraw


@multiple_attempts
@full_database_exceptions
def get_withdraw_by_id_withdraw(db: Session, id_withdraw: str) -> DbWithdraw:
    try:
        withdraw = db.query(DbWithdraw).where(
            DbWithdraw.id_withdraw == id_withdraw
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if withdraw is None:
        raise element_not_found_exception

    return withdraw


@multiple_attempts
@full_database_exceptions
def get_withdraw_by_id_movement(db: Session, id_movement: int) -> DbWithdraw:
    try:
        withdraw = db.query(DbWithdraw).where(
            DbWithdraw.id_movement == id_movement
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if withdraw is None:
        raise element_not_found_exception

    return withdraw

