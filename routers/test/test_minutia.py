from typing import List

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session
from starlette import status

from controller.login import get_current_token, check_type_user
from db.database import get_db
from db.orm import minutiae_orm
from db.orm.exceptions_orm import wrong_data_sent_exception, credentials_exception
from fingerprint_process.models.minutia import Minutiae
from schemas.basic_response import BasicResponse
from schemas.minutia_base import MinutiaDisplay, MinutiaRequest
from schemas.token_base import TokenSummary

router = APIRouter(
    prefix='/test/minutia',
    tags=['tests', 'minutia']
)


@router.post(
    path='/',
    response_model=BasicResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_minutia(
        request: MinutiaRequest = Body(...),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    new_minutia = Minutiae(
        posy=request.pos_y,
        posx=request.pos_x,
        angle=request.angle,
        point_type=request.type_minutia.value
    )

    result = minutiae_orm.create_minutia(db, new_minutia, request.id_fingerprint)

    return BasicResponse(
        operation="Create",
        successful=result
    )


@router.get(
    path='/{id_minutia}',
    response_model=MinutiaDisplay,
    status_code=status.HTTP_200_OK
)
async def get_minutia(
        id_minutia: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = minutiae_orm.get_minutia_by_id(db, id_minutia)

    return response


@router.delete(
    path='/{id_minutia}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_minutia(
        id_minutia: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = minutiae_orm.delete_minutia(db=db, id_minutia=id_minutia)

    return response


@router.post(
    path='/fingerprint/{id_fingerprint}',
    response_model=BasicResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_all_minutiae_of_a_fingerprint(
        id_fingerprint: str = Path(..., min_length=12, max_length=40),
        request: List[MinutiaRequest] = Body(...),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    id_fingerprint_of_request = request[0].id_fingerprint
    new_minutiae: List[Minutiae] = []

    for element in request:
        if id_fingerprint_of_request != element.id_fingerprint:
            raise wrong_data_sent_exception
        else:
            new_minutia = Minutiae(
                posy=element.pos_y,
                posx=element.pos_x,
                angle=element.angle,
                point_type=element.type_minutia.value
            )
            new_minutiae.append(new_minutia)

    if id_fingerprint_of_request != id_fingerprint:
        raise wrong_data_sent_exception

    result = minutiae_orm.insert_list_of_minutiae(db, new_minutiae, id_fingerprint)

    return BasicResponse(
        operation="Create",
        successful=result
    )


@router.get(
    path='/id_fingerprint/{id_fingerprint}',
    response_model=List[MinutiaDisplay],
    status_code=status.HTTP_200_OK
)
async def get_minutiae_of_fingerprint(
        id_fingerprint: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = minutiae_orm.get_minutiae_by_id_fingerprint(db, id_fingerprint)

    return response


@router.delete(
    path='/id_fingerprint/{id_fingerprint}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_minutiae_of_fingerprint(
        id_fingerprint: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = minutiae_orm.delete_all_minutiae_of_fingerprint(db, id_fingerprint)

    return response
