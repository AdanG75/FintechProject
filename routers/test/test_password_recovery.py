
from fastapi import APIRouter, Path, Depends, Query
from sqlalchemy.orm import Session
from starlette import status

from db.database import get_db
from db.models.password_recoveries_db import DbPasswordRecovery
from db.orm import password_recoveries_orm
from db.orm.exceptions_orm import element_not_found_exception, not_values_sent_exception
from schemas.basic_response import BasicResponse
from schemas.password_recovery_base import PasswordRecoveryDisplay

router = APIRouter(
    prefix='/test/password-recovery',
    tags=['tests', 'password recovery']
)


@router.get(
    path='/{id_recover}',
    response_model=PasswordRecoveryDisplay,
    status_code=status.HTTP_200_OK
)
async def get_password_recovery(
        id_recover: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response: DbPasswordRecovery = password_recoveries_orm.get_password_recovery_by_id_recover(db, id_recover)
    if not response.is_valid:
        raise element_not_found_exception

    return response


@router.post(
    path='/user/{id_user}',
    response_model=PasswordRecoveryDisplay,
    status_code=status.HTTP_201_CREATED
)
async def generate_code(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = password_recoveries_orm.create_code_to_recover_password(db, id_user)

    return response


@router.get(
    path='/user/{id_user}',
    response_model=PasswordRecoveryDisplay,
    status_code=status.HTTP_200_OK
)
async def get_password_recovery_of_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response: DbPasswordRecovery = password_recoveries_orm.get_password_recovery_by_id_user(db, id_user)

    if not response.is_valid:
        raise element_not_found_exception

    return response


@router.put(
    path='/user/{id_user}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def check_code(
        id_user: int = Path(..., gt=0),
        code: int = Query(None, lt=100000000),
        db: Session = Depends(get_db)
):
    if code is None:
        raise not_values_sent_exception

    result = password_recoveries_orm.check_code_of_password_recovery(db, id_user, code)

    return BasicResponse(
        operation="Recover password",
        successful=result
    )


@router.delete(
    path='/user/{id_user}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_code(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    result = password_recoveries_orm.reset_password_recovery_by_id_user(db, id_user)

    return BasicResponse(
        operation="Drop recovery request",
        successful=result
    )




