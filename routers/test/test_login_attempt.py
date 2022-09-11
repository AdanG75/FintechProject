from fastapi import APIRouter, Path, Depends
from sqlalchemy.orm import Session
from starlette import status

from controller.login import get_current_token, check_type_user
from db.database import get_db
from db.orm import login_attempts_orm
from db.orm.exceptions_orm import credentials_exception
from schemas.basic_response import BasicResponse
from schemas.login_attempt_base import LoginAttemptDisplay
from schemas.token_base import TokenSummary

router = APIRouter(
    prefix='/test/attempt',
    tags=['tests', 'login attempt']
)


@router.get(
    path='/{id_attempt}',
    response_model=LoginAttemptDisplay,
    status_code=status.HTTP_200_OK
)
async def get_attempt(
        id_attempt: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = login_attempts_orm.get_login_attempt_by_id_attempt(db, id_attempt)

    return response


@router.get(
    path='/user/{id_user}',
    response_model=LoginAttemptDisplay,
    status_code=status.HTTP_200_OK
)
async def get_attempt_of_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = login_attempts_orm.get_login_attempt_by_id_user(db, id_user)

    return response


@router.get(
    path='/status/user/{id_user}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def check_status_attempt_of_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    result = login_attempts_orm.check_attempt(db, id_user)

    return BasicResponse(
        operation='Valid next attempt',
        successful=result
    )


@router.put(
    path='/add/user/{id_user}',
    response_model=LoginAttemptDisplay,
    status_code=status.HTTP_200_OK
)
async def add_attempt_to_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = login_attempts_orm.add_attempt(db, id_user)

    return response


@router.put(
    path='/reset/user/{id_user}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def reset_attempts_of_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    result = login_attempts_orm.reset_login_attempt(db, id_user)

    return BasicResponse(
        operation='Reset attempts of user',
        successful=result
    )
