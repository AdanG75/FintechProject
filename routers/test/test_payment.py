from typing import List

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session
from starlette import status

from controller.login_controller import get_current_token, check_type_user
from db.database import get_db
from db.orm import payments_orm
from db.orm.exceptions_orm import credentials_exception
from schemas.payment_base import PaymentDisplay, PaymentRequest
from schemas.token_base import TokenSummary

router = APIRouter(
    prefix='/test/payment',
    tags=['tests', 'payment']
)


@router.post(
    path='/',
    response_model=PaymentDisplay,
    status_code=status.HTTP_201_CREATED
)
async def create_payment(
        request: PaymentRequest = Body(...),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    if request.type_payment.value != 'paypal':
        request.type_payment = payments_orm.get_payment_type(db=db, id_movement=request.id_movement)

    response = payments_orm.create_payment(db, request)

    return response


@router.get(
    path='/{id_payment}',
    response_model=PaymentDisplay,
    status_code=status.HTTP_200_OK
)
async def get_payment(
        id_payment: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = payments_orm.get_payment_by_id_payment(db, id_payment)

    return response


@router.get(
    path='/movement/{id_movement}',
    response_model=PaymentDisplay,
    status_code=status.HTTP_200_OK
)
async def get_payment_by_id_movement(
        id_movement: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = payments_orm.get_payment_by_id_movement(db, id_movement)

    return response


@router.get(
    path='/market/{id_market}',
    response_model=List[PaymentDisplay],
    status_code=status.HTTP_200_OK
)
async def get_payments_to_market(
        id_market: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = payments_orm.get_payments_by_id_market(db, id_market)

    return response
