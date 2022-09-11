from fastapi import APIRouter, Body, Path, Depends
from sqlalchemy.orm import Session
from starlette import status

from controller.login import get_current_token, check_type_user
from db.database import get_db
from db.orm import admins_orm
from db.orm.exceptions_orm import credentials_exception
from schemas.admin_base import AdminDisplay, AdminRequest
from schemas.basic_response import BasicResponse
from schemas.token_base import TokenSummary

router = APIRouter(
    prefix='/test/admin',
    tags=['tests', 'admin']
)


@router.post(
    path='/',
    response_model=AdminDisplay,
    status_code=status.HTTP_201_CREATED
)
async def create_admin(
        request: AdminRequest = Body(...),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = admins_orm.create_admin(db, request)

    return response


@router.get(
    path='/{id_admin}',
    response_model=AdminDisplay,
    status_code=status.HTTP_200_OK
)
async def get_admin(
        id_admin: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = admins_orm.get_admin_by_id_admin(db, id_admin)

    return response


@router.get(
    path='/user/{id_user}',
    response_model=AdminDisplay,
    status_code=status.HTTP_200_OK
)
async def get_admin_by_id_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = admins_orm.get_admin_by_id_user(db, id_user)

    return response


@router.put(
    path='/{id_admin}',
    response_model=AdminDisplay,
    status_code=status.HTTP_200_OK
)
async def update_admin(
        id_admin: str = Path(..., min_length=12, max_length=49),
        request: AdminRequest = Body(...),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = admins_orm.update_admin(db, request, id_admin)

    return response


@router.delete(
    path='/{id_admin}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_admin(
        id_admin: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = admins_orm.delete_admin(db, id_admin)

    return response
