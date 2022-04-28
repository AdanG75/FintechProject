from typing import Optional, List, Dict

from fastapi import APIRouter, Body, Path, Query, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status

from core import token_functions
from core.hash import Hash
from db.database import get_db
from db.models.admins_db import DbAdmin
from db.orm import admins_orm
from schemas.admin_base import AdminDisplay, AdminRequest, AdminToken
from schemas.basic_response import BasicResponse

router = APIRouter(
    prefix='/admin',
    tags=['admin']
)


# Create
@router.post(
    path='/',
    response_model=AdminDisplay
)
async def create_admin(
        request: AdminRequest = Body(...),
        db: Session = Depends(get_db),
        current_admin: DbAdmin = Depends(admins_orm.get_current_admin)
):
    register_admin = admins_orm.create_admin(db=db, request=request)

    return register_admin


# Read
@router.get(
    path='/{username}',
    response_model=AdminDisplay
)
async def get_admin(
        username: str = Path(...),
        db: Session = Depends(get_db),
        current_admin: DbAdmin = Depends(admins_orm.get_current_admin)
):
    admin = admins_orm.get_admin(db=db, username=username)

    return admin


# Update
@router.put(
    path='/{username}',
    response_model=AdminDisplay
)
async def update_admin(
        username: str = Path(...),
        request: AdminRequest = Body(...),
        db: Session = Depends(get_db),
        current_admin: DbAdmin = Depends(admins_orm.get_current_admin)
):
    updated_admin = admins_orm.update_admin(db=db, request=request, username=username)

    return updated_admin


# Delete
@router.delete(
    path='/{username}',
    response_model=BasicResponse
)
async def delete_admin(
        username: str = Path(...),
        db: Session = Depends(get_db),
        current_admin: DbAdmin = Depends(admins_orm.get_current_admin)
):
    response = admins_orm.delete_admin(db=db, username=username)

    return response


# Login
@router.post(
    path='/login',
    response_model=AdminToken
)
async def get_token(
        request: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    admin: Optional[DbAdmin] = admins_orm.get_admin(db=db, username=request.username)

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid user or password"
        )

    if not Hash.verify(admin.password, request.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid user or password"
        )

    access_token = token_functions.create_access_token(
        data={
            'id': admin.id,
            'username': admin.username,
            'email': admin.email
        })

    response_token = AdminToken(access_token=access_token, token_type='bearer', admin=admin)

    return response_token

