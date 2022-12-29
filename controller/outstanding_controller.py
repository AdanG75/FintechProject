from typing import List, Optional

from redis.client import Redis
from sqlalchemy.orm import Session

from controller.general_controller import save_value_in_cache_with_formatted_name, delete_values_in_cache
from core.utils import money_str_to_float
from db.models.outstanding_payments_db import DbOutstandingPayment
from db.orm.outstanding_payments_orm import get_all_outstanding_payments, start_cash_closing, cancel_cash_closing, \
    finish_cash_closing
from schemas.outstanding_base import ListOPDisplay, OutstandingPaymentDisplay


def get_outstanding_payments(db: Session) -> ListOPDisplay:
    outstanding_payments: List[DbOutstandingPayment] = get_all_outstanding_payments(db)
    op_objects = []

    for op in outstanding_payments:
        op_object = OutstandingPaymentDisplay.from_orm(op)
        op_objects.append(op_object)

    return ListOPDisplay(outstanding_payments=op_objects)


def get_non_zero_outstanding_payments(db: Session) -> ListOPDisplay:
    outstanding_payments: List[DbOutstandingPayment] = get_all_outstanding_payments(db)
    op_objects = []

    for op in outstanding_payments:
        amount_float = money_str_to_float(op.amount) if isinstance(op.amount, str) else op.amount
        if amount_float > 0:
            op_object = OutstandingPaymentDisplay.from_orm(op)
            op_objects.append(op_object)

    return ListOPDisplay(outstanding_payments=op_objects)


def start_cash_closing_from_controller(db: Session, id_outstanding: int) -> bool:
    outstanding_db = start_cash_closing(db, id_outstanding)

    return outstanding_db is not None


def finish_cash_closing_from_controller(db: Session, id_outstanding: int) -> DbOutstandingPayment:
    outstanding_db = finish_cash_closing(db, id_outstanding)

    return outstanding_db


def cancel_cash_closing_from_controller(db: Session, id_outstanding: int) -> OutstandingPaymentDisplay:
    outstanding_db = cancel_cash_closing(db, id_outstanding)

    return OutstandingPaymentDisplay.from_orm(outstanding_db)


async def save_id_outstanding_in_cache(r: Redis, paypal_order: str, id_outstanding: int) -> bool:
    return await save_value_in_cache_with_formatted_name(r, 'PYP', 'OTS', paypal_order, id_outstanding, 3600)


async def get_id_outstanding_from_cache(r: Redis, paypal_order: str) -> Optional[int]:
    id_outstanding_cache = r.get(f'PYP-OTS-{paypal_order}')
    if id_outstanding_cache is None:
        return None

    return int(id_outstanding_cache)


async def delete_id_outstanding_from_cache(r: Redis, paypal_order: str) -> bool:
    return await delete_values_in_cache(r, 'PYP', 'OTS', paypal_order)
