import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from db.models.movements_db import DbMovement
from db.models.payments_db import DbPayment
from db.orm.credits_orm import get_credit_by_id_credit
from db.orm.exceptions_orm import wrong_data_sent_exception, NotFoundException, option_not_found_exception, \
    not_unique_value, element_not_found_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.movements_orm import check_type_and_status_of_movement, get_movement_by_id_movement
from schemas.payment_base import PaymentRequest
from schemas.type_money import TypeMoney


@multiple_attempts
@full_database_exceptions
def create_payment(db: Session, request: PaymentRequest, execute: str = 'now') -> DbPayment:
    check_type_and_status_of_movement(db, request.id_movement, 'payment')

    try:
        get_payment_by_id_movement(db, request.id_movement)
    except NotFoundException:
        if request.type_payment.value == 'paypal' and request.paypal_id_order is None:
            raise wrong_data_sent_exception

        payment_uuid = uuid.uuid4().hex
        id_payment = "PYM-" + payment_uuid

        new_payment = DbPayment(
            id_payment=id_payment,
            id_movement=request.id_movement,
            id_market=request.id_market,
            type_payment=request.type_payment.value,
            paypal_id_order=request.paypal_id_order
        )

        try:
            db.add(new_payment)
            if execute == 'now':
                db.commit()
                db.refresh(new_payment)
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

    return new_payment


@multiple_attempts
@full_database_exceptions
def get_payment_by_id_payment(db: Session, id_payment: str) -> DbPayment:
    try:
        payment = db.query(DbPayment).where(
            DbPayment.id_payment == id_payment
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if payment is None:
        raise element_not_found_exception

    return payment


@multiple_attempts
@full_database_exceptions
def get_payment_by_id_movement(db: Session, id_movement: int) -> DbPayment:
    try:
        payment = db.query(DbPayment).where(
            DbPayment.id_movement == id_movement
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if payment is None:
        raise element_not_found_exception

    return payment


@multiple_attempts
@full_database_exceptions
def get_payments_by_id_market(db: Session, id_market: str) -> List[DbPayment]:
    try:
        payments = db.query(DbPayment).where(
            DbPayment.id_market == id_market
        ).all()
    except Exception as e:
        print(e)
        raise e

    if payments is None:
        payments = []

    return payments


@multiple_attempts
@full_database_exceptions
def get_payment_type(
        db: Session,
        id_movement: Optional[int] = None,
        movement_object: Optional[DbMovement] = None
) -> TypeMoney:
    if movement_object is None:
        if id_movement is not None:
            movement_object = get_movement_by_id_movement(db, id_movement)
        else:
            raise wrong_data_sent_exception

    credit = get_credit_by_id_credit(db, movement_object.id_credit)

    if credit.type_credit == 'local':
        return TypeMoney.local
    elif credit.type_credit == 'global':
        return TypeMoney.globalC
    else:
        raise option_not_found_exception
