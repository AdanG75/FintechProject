import uuid
from typing import Optional, List

from sqlalchemy.orm import Session

from db.models.deposits_db import DbDeposit
from db.orm.exceptions_orm import element_not_found_exception, NotFoundException, option_not_found_exception, \
    not_unique_value, not_values_sent_exception, wrong_data_sent_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.movements_orm import check_type_and_status_of_movement
from schemas.deposit_base import DepositRequest


@multiple_attempts
@full_database_exceptions
def create_deposit(db: Session, request: DepositRequest, execute: str = 'now') -> DbDeposit:
    check_type_and_status_of_movement(db, request.id_movement, 'deposit')

    try:
        get_deposit_by_id_movement(db, request.id_movement)
    except NotFoundException:
        if request.type_deposit.value == 'paypal' and request.paypal_id_order is None:
            raise wrong_data_sent_exception

        deposit_uuid = uuid.uuid4().hex
        id_deposit = "DPT-" + deposit_uuid

        new_deposit = DbDeposit(
            id_deposit=id_deposit,
            id_movement=request.id_movement,
            id_destination_credit=request.id_destination_credit,
            depositor_name=request.depositor_name,
            depositor_email=request.depositor_email,
            type_deposit=request.type_deposit.value,
            paypal_id_order=request.paypal_id_order
        )

        try:
            db.add(new_deposit)
            if execute == 'now':
                db.commit()
                db.refresh(new_deposit)
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

    return new_deposit


@multiple_attempts
@full_database_exceptions
def get_deposit_by_id_deposit(db: Session, id_deposit: str) -> DbDeposit:
    try:
        deposit = db.query(DbDeposit).where(
            DbDeposit.id_deposit == id_deposit
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if deposit is None:
        raise element_not_found_exception

    return deposit


@multiple_attempts
@full_database_exceptions
def get_deposit_by_id_movement(db: Session, id_movement: int) -> DbDeposit:
    try:
        deposit = db.query(DbDeposit).where(
            DbDeposit.id_movement == id_movement
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if deposit is None:
        raise element_not_found_exception

    return deposit


@multiple_attempts
@full_database_exceptions
def get_deposits_by_id_destination_credit(db: Session, id_destination_credit: int) -> List[DbDeposit]:
    try:
        deposits = db.query(DbDeposit).where(
            DbDeposit.id_destination_credit == id_destination_credit
        ).all()
    except Exception as e:
        print(e)
        raise e

    if deposits is None:
        raise element_not_found_exception

    return deposits


@multiple_attempts
@full_database_exceptions
def put_paypal_id_order(
        db: Session,
        paypal_id_order: str,
        id_deposit: Optional[str] = None,
        id_movement: Optional[int] = None,
        deposit_object: Optional[DbDeposit] = None,
        execute: str = 'now'
) -> DbDeposit:
    if deposit_object is None:
        if id_movement is not None:
            deposit_object = get_deposit_by_id_movement(db, id_movement)
        elif id_deposit is not None:
            deposit_object = get_deposit_by_id_deposit(db, id_deposit)
        else:
            raise not_values_sent_exception

    if deposit_object.paypal_id_order is None:
        deposit_object.paypal_id_order = paypal_id_order

    try:
        if execute == 'now':
            db.commit()
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return deposit_object
