from typing import Optional, List

from email_validator import validate_email, EmailNotValidError
from fastapi import APIRouter, Body, Depends, Path, Query, HTTPException
from requests import Session
from starlette import status

from db.database import get_db
from db.orm import accounts_orm
from schemas.account_base import AccountDisplay, AccountRequest
from schemas.basic_response import BasicResponse

router = APIRouter(
    prefix='/test/accounts',
    tags=['tests', 'account']
)


@router.post(
    path='/',
    response_model=AccountDisplay,
    status_code=status.HTTP_201_CREATED
)
async def create_account(
        request: AccountRequest = Body(...),
        test: Optional[bool] = Query(False),
        db: Session = Depends(get_db)
):
    check_email(test, request.paypal_email)
    response = accounts_orm.create_account(db, request)

    return response


@router.get(
    path='/{id_account}',
    response_model=AccountDisplay,
    status_code=status.HTTP_200_OK
)
async def get_account(
        id_account: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = accounts_orm.get_account_by_id(db, id_account)

    return response


@router.put(
    path='/{id_account}',
    response_model=AccountDisplay,
    status_code=status.HTTP_200_OK
)
async def update_account(
        id_account: int = Path(..., gt=0),
        request: AccountRequest = Body(...),
        test: Optional[bool] = Query(False),
        db: Session = Depends(get_db)
):
    check_email(test, request.paypal_email)
    response = accounts_orm.update_account(db, request, id_account)

    return response


@router.delete(
    path='/{id_account}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_account(
        id_account: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = accounts_orm.delete_account(db, id_account)

    return response


@router.get(
    path='/user/{id_user}',
    response_model=List[AccountDisplay],
    status_code=status.HTTP_200_OK
)
async def get_accounts_of_user(
        id_user: int = Path(..., gt=0),
        main: Optional[bool] = Query(False),
        alias: Optional[str] = Query(None, min_length=2, max_length=79),
        db: Session = Depends(get_db)
):
    if main:
        response = [accounts_orm.get_main_account_of_user(db, id_user), ]
    else:
        if alias is not None:
            response = accounts_orm.get_accounts_by_user_and_alias(db, id_user, alias)
        else:
            response = accounts_orm.get_accounts_by_user(db, id_user)

    return response


@router.delete(
    path='/user/{id_user}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_accounts_of_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = accounts_orm.delete_accounts_by_id_user(db, id_user)

    return response


def check_email(flag: bool, email: str) -> bool:
    if not flag:
        try:
            validate_email(email)
        except EmailNotValidError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value is not a valid email address"
            )

    return True
