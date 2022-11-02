from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session
from starlette import status

from controller.login_controller import get_current_token, check_type_user
from db.database import get_db
from db.orm import outstanding_payments_orm
from db.orm.exceptions_orm import credentials_exception
from schemas.basic_response import BasicResponse
from schemas.outstanding_base import OutstandingPaymentRequest, OutstandingPaymentDisplay
from schemas.token_base import TokenSummary

router = APIRouter(
    prefix='/test/outstanding-payment',
    tags=['tests', 'outstanding payment']
)


@router.post(
    path='/',
    response_model=OutstandingPaymentDisplay,
    status_code=status.HTTP_201_CREATED
)
async def create_outstanding_payment(
        request: OutstandingPaymentRequest = Body(...),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = outstanding_payments_orm.create_outstanding_payment(db, request)

    return response


@router.get(
    path='/',
    response_model=List[OutstandingPaymentDisplay],
    status_code=status.HTTP_200_OK
)
async def get_outstanding_payments(
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = outstanding_payments_orm.get_all_outstanding_payments(db)

    return response


@router.get(
    path='/{id_outstanding}',
    response_model=OutstandingPaymentDisplay,
    status_code=status.HTTP_200_OK
)
async def get_outstanding_payments(
        id_outstanding: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = outstanding_payments_orm.get_outstanding_payment_by_id_outstanding(db, id_outstanding)

    return response


@router.delete(
    path='/{id_outstanding}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_outstanding_payment(
        id_outstanding: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = outstanding_payments_orm.delete_outstanding_payment(db, id_outstanding)

    return response


@router.get(
    path='/market/{id_market}',
    response_model=OutstandingPaymentDisplay,
    status_code=status.HTTP_200_OK
)
async def get_outstanding_payment_by_id_market(
        id_market: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = outstanding_payments_orm.get_outstanding_payment_by_id_market(db, id_market)

    return response


@router.patch(
    path='/add/{id_outstanding}',
    response_model=OutstandingPaymentDisplay,
    status_code=status.HTTP_200_OK
)
async def add_amount_to_outstanding_payment(
        id_outstanding: int = Path(..., gt=0),
        amount: Optional[float] = Query(0, ge=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = outstanding_payments_orm.add_amount(db, id_outstanding, amount)

    return response


@router.patch(
    path='/cash-closing/start/{id_outstanding}',
    response_model=OutstandingPaymentDisplay,
    status_code=status.HTTP_200_OK
)
async def start_cash_closing(
        id_outstanding: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = outstanding_payments_orm.start_cash_closing(db, id_outstanding)

    return response


@router.patch(
    path='/cash-closing/cancel/{id_outstanding}',
    response_model=OutstandingPaymentDisplay,
    status_code=status.HTTP_200_OK
)
async def cancel_cash_closing(
        id_outstanding: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = outstanding_payments_orm.cancel_cash_closing(db, id_outstanding)

    return response


@router.patch(
    path='/cash-closing/finish/{id_outstanding}',
    response_model=OutstandingPaymentDisplay,
    status_code=status.HTTP_200_OK
)
async def finish_cash_closing(
        id_outstanding: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = outstanding_payments_orm.finish_cash_closing(db, id_outstanding)

    return response
