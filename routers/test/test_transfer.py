from typing import List

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session
from starlette import status

from db.database import get_db
from db.orm import trasnfers_orm
from schemas.transfer_base import TransferDisplay, TransferRequest

router = APIRouter(
    prefix='/test/transfer',
    tags=['tests', 'transfer']
)


@router.post(
    path='/',
    response_model=TransferDisplay,
    status_code=status.HTTP_201_CREATED
)
async def create_transfer(
        request: TransferRequest = Body(...),
        db: Session = Depends(get_db)
):
    request.type_transfer = trasnfers_orm.get_type_of_transfer(
        db=db,
        id_destination_credit=request.id_destination_credit,
        id_movement=request.id_movement
    )

    response = trasnfers_orm.create_transfer(db, request)

    return response


@router.get(
    path='/{id_transfer}',
    response_model=TransferDisplay,
    status_code=status.HTTP_200_OK
)
async def get_transfer(
        id_transfer: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db)
):
    response = trasnfers_orm.get_transfer_by_id_transfer(db, id_transfer)

    return response


@router.get(
    path='/movement/{id_movement}',
    response_model=TransferDisplay,
    status_code=status.HTTP_200_OK
)
async def get_transfer_by_id_movement(
        id_movement: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = trasnfers_orm.get_transfer_by_id_movement(db, id_movement)

    return response


@router.get(
    path='/credit/{id_credit}',
    response_model=List[TransferDisplay],
    status_code=status.HTTP_200_OK
)
async def get_transfers_by_id_credit(
        id_credit: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = trasnfers_orm.get_transfers_by_id_destination_credit(db, id_credit)

    return response
