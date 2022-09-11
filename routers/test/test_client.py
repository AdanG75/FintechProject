from fastapi import APIRouter, Path, Depends, Body
from sqlalchemy.orm import Session
from starlette import status

from controller.login import get_current_token, check_type_user
from db.database import get_db
from db.orm import clients_orm
from db.orm.exceptions_orm import credentials_exception
from schemas.basic_response import BasicResponse
from schemas.client_base import ClientDisplay, ClientRequest
from schemas.token_base import TokenSummary

router = APIRouter(
    prefix='/test/client',
    tags=['tests', 'client']
)


@router.post(
    path='/',
    response_model=ClientDisplay,
    status_code=status.HTTP_200_OK
)
async def create_client(
        request: ClientRequest = Body(...),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = clients_orm.create_client(db, request)

    return response


@router.get(
    path='/{id_client}',
    response_model=ClientDisplay,
    status_code=status.HTTP_200_OK
)
async def get_client(
        id_client: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = clients_orm.get_client_by_id_client(db, id_client)

    return response


@router.get(
    path='/user/{id_user}',
    response_model=ClientDisplay,
    status_code=status.HTTP_200_OK
)
async def get_client_by_id_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = clients_orm.get_client_by_id_user(db, id_user)

    return response


@router.put(
    path='/{id_client}',
    response_model=ClientDisplay,
    status_code=status.HTTP_200_OK
)
async def update_client(
        id_client: str = Path(..., min_length=12, max_length=49),
        request: ClientRequest = Body(...),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = clients_orm.update_client(db, request, id_client)

    return response


@router.delete(
    path='/{id_client}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_client(
        id_client: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = clients_orm.delete_client(db, id_client)

    return response
