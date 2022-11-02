from typing import Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session
from starlette import status

from controller.login_controller import get_current_token, check_type_user
from db.database import get_db
from db.orm import deposits_orm
from db.orm.exceptions_orm import credentials_exception
from schemas.deposit_base import DepositDisplay, DepositRequest
from schemas.token_base import TokenSummary

router = APIRouter(
    prefix='/test/deposit',
    tags=['tests', 'deposit']
)


@router.post(
    path='/',
    response_model=DepositDisplay,
    status_code=status.HTTP_201_CREATED
)
async def create_deposit(
        request: DepositRequest = Body(...),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = deposits_orm.create_deposit(db, request)

    return response


@router.get(
    path='/{id_deposit}',
    response_model=DepositDisplay,
    status_code=status.HTTP_200_OK
)
async def get_deposit(
        id_deposit: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = deposits_orm.get_deposit_by_id_deposit(db, id_deposit)

    return response


@router.get(
    path='/movement/{id_movement}',
    response_model=DepositDisplay,
    status_code=status.HTTP_200_OK
)
async def get_deposit_by_id_movement(
        id_movement: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = deposits_orm.get_deposit_by_id_movement(db, id_movement)

    return response


@router.patch(
    path='/order/{id_deposit}',
    response_model=DepositDisplay,
    status_code=status.HTTP_200_OK
)
async def put_paypal_id_order(
        id_deposit: str = Path(..., min_length=12, max_length=40),
        paypal_id_order: Optional[str] = Query(None, min_length=8, max_length=25),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    if paypal_id_order is None:
        response = deposits_orm.get_deposit_by_id_deposit(db, id_deposit)
    else:
        response = deposits_orm.put_paypal_id_order(db=db, paypal_id_order=paypal_id_order, id_deposit=id_deposit)

    return response
