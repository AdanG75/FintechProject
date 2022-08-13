from typing import Union, List, Optional

from fastapi import APIRouter, Depends, Body, Path, Query
from sqlalchemy.orm import Session
from starlette import status

from db.database import get_db
from db.orm import fingerprints_orm
from schemas.basic_response import BasicResponse
from schemas.fingerprint_base import FingerprintBasicDisplay, FingerprintRequest, FingerprintUpdateRequest

router = APIRouter(
    prefix='/test/fingerprints',
    tags=['tests', 'fingerprint']
)


@router.post(
    path='/',
    response_model=FingerprintBasicDisplay,
    status_code=status.HTTP_201_CREATED
)
async def create_fingerprint(
        request: FingerprintRequest = Body(...),
        db: Session = Depends(get_db)
):
    response = fingerprints_orm.create_fingerprint(db, request)

    return response


@router.get(
    path='/{id_fingerprint}',
    response_model=FingerprintBasicDisplay,
    status_code=status.HTTP_200_OK
)
async def get_fingerprint(
        id_fingerprint: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db)
):
    response = fingerprints_orm.get_fingerprint_by_id(db, id_fingerprint)

    return response


@router.patch(
    path='/{id_fingerprint}',
    response_model=Union[FingerprintBasicDisplay, BasicResponse],
    status_code=status.HTTP_200_OK
)
async def light_update(
        id_fingerprint: str = Path(..., min_length=12, max_length=49),
        request: FingerprintUpdateRequest = Body(...),
        db: Session = Depends(get_db)
):
    if request.request.value == "main":
        result = fingerprints_orm.change_main_fingerprint(
            db=db,
            change_main_to=request.main_fingerprint,
            id_new_main_fingerprint=id_fingerprint
        )
        return BasicResponse(
            operation="Change main fingerprint",
            successful=result
        )
    elif request.request.value == "alias":
        result = fingerprints_orm.change_alias_fingerprint(
            db=db,
            id_fingerprint=id_fingerprint,
            alias_fingerprint=request.alias_fingerprint
        )
        return BasicResponse(
            operation="Change alias fingerprint",
            successful=result
        )
    else:
        response = fingerprints_orm.light_update(
            db=db,
            request=request,
            id_fingerprint=id_fingerprint
        )

        return response


@router.delete(
    path='/{id_fingerprint}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_fingerprint(
        id_fingerprint: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db)
):
    response = fingerprints_orm.delete_fingerprint(db, id_fingerprint)

    return response


@router.get(
    path='/client/{id_client}',
    response_model=List[FingerprintBasicDisplay],
    status_code=status.HTTP_200_OK
)
async def get_fingerprints_of_user(
        id_client: str = Path(..., min_length=12, max_length=49),
        main: Optional[bool] = Query(False),
        alias: Optional[str] = Query(None, min_length=2, max_length=79),
        db: Session = Depends(get_db)
):
    if main:
        response = [fingerprints_orm.get_main_fingerprint_of_client(db, id_client), ]
    else:
        if alias is None:
            response = fingerprints_orm.get_fingerprints_by_id_client(db, id_client)
        else:
            response = [fingerprints_orm.get_client_fingerprint_by_alias(db, id_client, alias), ]

    return response


@router.delete(
    path='/client/{id_client}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_fingerprints_of_client(
        id_client: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db)
):
    response = fingerprints_orm.delete_fingerprints_by_id_client(db, id_client)

    return response
