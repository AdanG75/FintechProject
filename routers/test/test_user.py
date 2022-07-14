from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session
from starlette import status

from db.database import get_db
from db.models.users_db import DbUser
from db.orm import users_orm
from db.orm.exceptions_orm import NotFoundException
from schemas.basic_response import BasicResponse
from schemas.type_user import TypeUser
from schemas.user_base import UserRequest, UserDisplay, PublicKeyDisplay, UserPublicKeyRequest

router = APIRouter(
    prefix='/test/user',
    tags=['tests', 'user']
)


@router.post(
    path="/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserDisplay
)
async def create_user(
        user: UserRequest = Body(...),
        db: Session = Depends(get_db)
):
    user: DbUser = users_orm.create_user(db, user)

    return user


@router.put(
    path="/{id_user}",
    response_model=UserDisplay,
    status_code=status.HTTP_200_OK
)
async def update_user(
        id_user: int = Path(..., gt=0),
        user: UserRequest = Body(...),
        db: Session = Depends(get_db)
):
    user: DbUser = users_orm.update_user(db, user, id_user)

    return user


@router.patch(
    path="/{id_user}",
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def update_public_key_of_user(
        id_user: int = Path(..., gt=0),
        request: UserPublicKeyRequest = Body(...),
        db: Session = Depends(get_db)
):
    response = users_orm.set_public_key(db, id_user, request.public_key)

    return response


@router.get(
    path="/all",
    status_code=status.HTTP_200_OK,
    response_model=Optional[List[UserDisplay]]
)
async def get_all_users(
        db: Session = Depends(get_db)
):
    users = users_orm.get_all_users(db)

    return users


@router.get(
    path="/public_key/{id_user}",
    response_model=PublicKeyDisplay,
    status_code=status.HTTP_200_OK
)
async def get_public_key_of_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    pem: str = users_orm.get_public_key_pem(db, id_user)

    return PublicKeyDisplay(public_key=pem)


@router.get(
    path="/by_type",
    response_model=List[Optional[UserDisplay]],
    status_code=status.HTTP_200_OK
)
async def get_users_by_type(
        type_user: TypeUser = Query(TypeUser.market),
        db: Session = Depends(get_db)
):
    # if type_user is None:
    #     type_user = TypeUser.client

    try:
        users: List[DbUser] = users_orm.get_users_by_type(db, type_user.value)
    except NotFoundException:
        users = []

    return users


@router.delete(
    path="/{id_user}",
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = users_orm.delete_user(db, id_user)

    return response
