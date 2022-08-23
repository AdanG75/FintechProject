from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session
from starlette import status

from db.database import get_db
from db.orm import withdraws_orm
from schemas.withdraw_base import WithdrawDisplay, WithdrawRequest

router = APIRouter(
    prefix='/test/withdraw',
    tags=['tests', 'withdraw']
)


@router.post(
    path='/',
    response_model=WithdrawDisplay,
    status_code=status.HTTP_201_CREATED
)
async def create_withdraw(
        request: WithdrawRequest = Body(...),
        db: Session = Depends(get_db)
):
    response = withdraws_orm.create_withdraw(db, request)

    return response


@router.get(
    path='/{id_withdraw}',
    response_model=WithdrawDisplay,
    status_code=status.HTTP_200_OK
)
async def get_withdraw(
        id_withdraw: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db)
):
    response = withdraws_orm.get_withdraw_by_id_withdraw(db, id_withdraw)

    return response


@router.get(
    path='/movement/{id_movement}',
    response_model=WithdrawDisplay,
    status_code=status.HTTP_200_OK
)
async def get_withdraw_by_id_movement(
        id_movement: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = withdraws_orm.get_withdraw_by_id_movement(db, id_movement)

    return response
