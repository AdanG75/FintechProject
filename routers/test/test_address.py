from typing import List

from fastapi import APIRouter, Depends, Body, Path, Query
from requests import Session
from starlette import status

from db.database import get_db
from db.models.addresses_db import DbAddress
from db.orm import addresses_orm
from schemas.address_base import AddressDisplay, AddressDisplayMarket, AddressDisplayClient, AddressRequest
from schemas.basic_response import BasicResponse
from schemas.type_user import TypeUser

router = APIRouter(
    prefix='/test/address',
    tags=['tests', 'address']
)


@router.post(
    path='/',
    response_model=AddressDisplay,
    status_code=status.HTTP_201_CREATED
)
async def create_address(
        request: AddressRequest = Body(...),
        db: Session = Depends(get_db)
):
    response = addresses_orm.create_address(db, request)

    return response


@router.get(
    path='/{id_address}',
    response_model=AddressDisplay,
    status_code=status.HTTP_200_OK
)
async def get_address(
        id_address: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response: DbAddress = addresses_orm.get_address_by_id_address(db, id_address)

    return response


@router.get(
    path='/client/{id_client}',
    response_model=List[AddressDisplayClient],
    status_code=status.HTTP_200_OK
)
async def get_addresses_of_client(
        id_client: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db)
):
    response = addresses_orm.get_addresses_by_id_client(db, id_client)

    return response


@router.get(
    path='/client/main/{id_client}',
    response_model=AddressDisplayClient,
    status_code=status.HTTP_200_OK
)
async def get_main_address_of_client(
        id_client: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db)
):
    response = addresses_orm.get_main_address_of_client(db, id_client)

    return response


@router.get(
    path='/branch/{id_branch}',
    response_model=AddressDisplayMarket,
    status_code=status.HTTP_200_OK
)
async def get_address_of_branch(
        id_branch: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db)
):
    response = addresses_orm.get_address_by_id_branch(db, id_branch)

    return response


@router.put(
    path='/{id_address}',
    response_model=AddressDisplay,
    status_code=status.HTTP_200_OK
)
async def update_address(
        id_address: int = Path(..., gt=0),
        request: AddressRequest = Body(...),
        db: Session = Depends(get_db)
):
    response = addresses_orm.update_address(db, request, id_address)

    return response


@router.patch(
    path='/main/{id_address}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def set_main_address(
        id_address: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    result = addresses_orm.change_main_address(db=db, id_address=id_address)

    return BasicResponse(
        operation="Set main address",
        successful=result
    )


@router.delete(
    path='/{id_address}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_address(
        id_address: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = addresses_orm.delete_address(db, id_address)

    return response


@router.delete(
    path='/owner/{id_owner}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_addresses_of_owner(
        id_owner: str = Path(..., min_length=12, max_length=49),
        type_owner: TypeUser = Query('client'),
        db: Session = Depends(get_db)
):
    response = addresses_orm.delete_addresses_by_id_owner(db, id_owner, type_owner.value)

    return response
