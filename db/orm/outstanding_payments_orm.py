from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.config import settings
from core.utils import money_str_to_float
from db.models.outstanding_payments_db import DbOutstandingPayment
from db.orm.exceptions_orm import wrong_data_sent_exception, NotFoundException, option_not_found_exception, \
    not_unique_value, element_not_found_exception, movement_in_process_exception, \
    operation_need_a_precondition_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.markets_orm import get_market_by_id_market
from schemas.basic_response import BasicResponse
from schemas.outstanding_base import OutstandingPaymentRequest


@multiple_attempts
@full_database_exceptions
def create_outstanding_payment(
        db: Session,
        request: OutstandingPaymentRequest,
        execute: str = 'now'
) -> DbOutstandingPayment:
    try:
        get_market_by_id_market(db, request.id_market)
    except NotFoundException:
        raise wrong_data_sent_exception

    try:
        outstanding_payment = get_outstanding_payment_by_id_market(db, request.id_market, mode='all')
    except NotFoundException:
        new_outstanding_payment = DbOutstandingPayment(
            id_system=settings.get_id_system(),
            id_market=request.id_market,
            amount=request.amount,
            past_amount=0,
            in_process=False,
            last_cash_closing=None,
            created_time=datetime.utcnow(),
            dropped=False
        )

        try:
            db.add(new_outstanding_payment)
            if execute == 'now':
                db.commit()
                db.refresh(new_outstanding_payment)
            elif execute == 'wait':
                pass
            else:
                raise option_not_found_exception
        except Exception as e:
            db.rollback()
            print(e)
            raise e

        return new_outstanding_payment

    if outstanding_payment.dropped:
        return update_outstanding_payment(
            db,
            outstanding_payment.id_outstanding,
            request,
            mode='all',
            execute=execute
        )

    raise not_unique_value


@multiple_attempts
@full_database_exceptions
def get_outstanding_payment_by_id_outstanding(
        db: Session,
        id_outstanding: int,
        mode: str = 'active'
) -> DbOutstandingPayment:
    try:
        if mode == 'active':
            outstanding_payment = db.query(DbOutstandingPayment).where(
                DbOutstandingPayment.id_outstanding == id_outstanding,
                DbOutstandingPayment.dropped == False
            ).one_or_none()
        elif mode == 'all':
            outstanding_payment = db.query(DbOutstandingPayment).where(
                DbOutstandingPayment.id_outstanding == id_outstanding
            ).one_or_none()
        else:
            raise option_not_found_exception
    except HTTPException as httpe:
        raise httpe
    except Exception as e:
        print(e)
        raise e

    if outstanding_payment is None:
        raise element_not_found_exception

    return outstanding_payment


@multiple_attempts
@full_database_exceptions
def get_outstanding_payment_by_id_market(
        db: Session,
        id_market: str,
        mode: str = 'active'
) -> DbOutstandingPayment:
    try:
        if mode == 'active':
            outstanding_payment = db.query(DbOutstandingPayment).where(
                DbOutstandingPayment.id_market == id_market,
                DbOutstandingPayment.dropped == False
            ).one_or_none()
        elif mode == 'all':
            outstanding_payment = db.query(DbOutstandingPayment).where(
                DbOutstandingPayment.id_market == id_market
            ).one_or_none()
        else:
            raise option_not_found_exception
    except HTTPException as httpe:
        raise httpe
    except Exception as e:
        print(e)
        raise e

    if outstanding_payment is None:
        raise element_not_found_exception

    return outstanding_payment


@multiple_attempts
@full_database_exceptions
def get_all_outstanding_payments(db: Session, mode: str = 'active') -> List[DbOutstandingPayment]:
    try:
        if mode == 'active':
            outstanding_payments = db.query(DbOutstandingPayment).where(
                DbOutstandingPayment.dropped == False
            ).all()
        elif mode == 'all':
            outstanding_payments = db.query(DbOutstandingPayment).all()
        else:
            raise option_not_found_exception
    except HTTPException as httpe:
        raise httpe
    except Exception as e:
        print(e)
        raise e

    if outstanding_payments is None:
        outstanding_payments = []

    return outstanding_payments


@multiple_attempts
@full_database_exceptions
def update_outstanding_payment(
        db: Session,
        id_outstanding: int,
        request: OutstandingPaymentRequest,
        mode: str = 'active',
        execute: str = 'now'
):
    outstanding_payment = get_outstanding_payment_by_id_outstanding(db, id_outstanding, mode=mode)

    if outstanding_payment.dropped:
        outstanding_payment.past_amount = outstanding_payment.amount
        outstanding_payment.amount = request.amount
        outstanding_payment.in_process = False
        outstanding_payment.last_cash_closing = datetime.utcnow()

    outstanding_payment.dropped = False

    try:
        if execute == 'now':
            db.commit()
            db.refresh(outstanding_payment)
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return outstanding_payment


@multiple_attempts
@full_database_exceptions
def add_amount(db: Session, id_outstanding: int, amount: float) -> DbOutstandingPayment:
    outstanding_payment = get_outstanding_payment_by_id_outstanding(db, id_outstanding)

    if not outstanding_payment.in_process:
        outstanding_payment.amount = money_str_to_float(str(outstanding_payment.amount)) + amount
    else:
        raise movement_in_process_exception

    try:
        db.commit()
        db.refresh(outstanding_payment)
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return outstanding_payment


@multiple_attempts
@full_database_exceptions
def start_cash_closing(db: Session, id_outstanding: int) -> DbOutstandingPayment:
    outstanding_payment = get_outstanding_payment_by_id_outstanding(db, id_outstanding)

    if not outstanding_payment.in_process:
        outstanding_payment.in_process = True
        outstanding_payment.past_amount = outstanding_payment.amount
        outstanding_payment.amount = 0
    else:
        raise movement_in_process_exception

    try:
        db.commit()
        db.refresh(outstanding_payment)
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return outstanding_payment


@multiple_attempts
@full_database_exceptions
def cancel_cash_closing(db: Session, id_outstanding: int) -> DbOutstandingPayment:
    outstanding_payment = get_outstanding_payment_by_id_outstanding(db, id_outstanding)

    if outstanding_payment.in_process:
        outstanding_payment.amount = outstanding_payment.past_amount
        outstanding_payment.in_process = False
    else:
        return outstanding_payment

    try:
        db.commit()
        db.refresh(outstanding_payment)
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return outstanding_payment


@multiple_attempts
@full_database_exceptions
def finish_cash_closing(db: Session, id_outstanding: int) -> DbOutstandingPayment:
    outstanding_payment = get_outstanding_payment_by_id_outstanding(db, id_outstanding)

    if outstanding_payment.in_process:
        outstanding_payment.last_cash_closing = datetime.utcnow()
        outstanding_payment.in_process = False
    else:
        return outstanding_payment

    try:
        db.commit()
        db.refresh(outstanding_payment)
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return outstanding_payment


@multiple_attempts
@full_database_exceptions
def delete_outstanding_payment(db: Session, id_outstanding: int, execute: str = 'now') -> BasicResponse:
    outstanding_payment = get_outstanding_payment_by_id_outstanding(db, id_outstanding)

    market = get_market_by_id_market(db, outstanding_payment.id_market, mode='all')
    if not market.dropped:
        # It is necessary that the marked is erased to drop the outstanding payment.
        raise operation_need_a_precondition_exception

    outstanding_payment.in_process = False
    outstanding_payment.dropped = True

    if execute == 'now':
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    elif execute == 'wait':
        pass
    else:
        raise option_not_found_exception

    return BasicResponse(
        operation="Delete",
        successful=True
    )
