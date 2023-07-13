from random import getrandbits
from typing import Optional, List

from fastapi import APIRouter, Depends, Body, Path, Query
from sqlalchemy.orm import Session
from starlette import status

from controller.login_controller import get_current_token, check_type_user
from db.database import get_db
from db.orm import movements_orm
from db.orm.exceptions_orm import credentials_exception
from schemas.movement_base import MovementRequest, MovementDisplay
from schemas.token_base import TokenSummary

router = APIRouter(
    prefix='/test/movement',
    tags=['tests', 'movement']
)


@router.post(
    path='/',
    response_model=MovementDisplay,
    status_code=status.HTTP_201_CREATED
)
async def make_movement(
        request: MovementRequest = Body(...),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = movements_orm.make_movement(db, request)

    return response


@router.get(
    path="/{id_movement}",
    response_model=MovementDisplay,
    status_code=status.HTTP_200_OK
)
async def get_movement(
        id_movement: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = movements_orm.get_movement_by_id_movement(db, id_movement)

    return response


@router.get(
    path='/credit/{id_credit}',
    response_model=List[MovementDisplay],
    status_code=status.HTTP_200_OK
)
async def get_movements_by_credit(
        id_credit: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = movements_orm.get_movements_by_id_credit(db, id_credit)

    return response


@router.get(
    path='/performer/{id_user}',
    response_model=List[MovementDisplay],
    status_code=status.HTTP_200_OK
)
async def get_movements_by_performer(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = movements_orm.get_movements_by_id_performer(db, id_user)

    return response


@router.get(
    path='/requester/{id_client}',
    response_model=List[MovementDisplay],
    status_code=status.HTTP_200_OK
)
async def get_movements_by_id_requester(
        id_client: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = movements_orm.get_movements_by_id_requester(db, id_client)

    return response


@router.patch(
    path='/authorize/{id_movement}',
    response_model=MovementDisplay,
    status_code=status.HTTP_200_OK
)
async def authorize_movement(
        id_movement: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = movements_orm.authorized_movement(db=db, id_movement=id_movement)

    return response


@router.patch(
    path='/finish/{id_movement}',
    response_model=MovementDisplay,
    status_code=status.HTTP_200_OK
)
async def finish_movement(
        id_movement: int = Path(..., gt=0),
        result: Optional[bool] = Query(None),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    if result is None:
        # Get a random result (True or False)
        result = not getrandbits(1)

    response = movements_orm.finish_movement(db=db, was_successful=result, id_movement=id_movement)

    return response
