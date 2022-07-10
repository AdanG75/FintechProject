from typing import Optional, List

from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import Session

from db.models.addresses_db import DbAddress
from db.orm.exceptions_orm import db_exception, element_not_found_exception, type_not_found_exception, \
    not_values_sent_exception, not_unique_value
from db.orm.functions_orm import multiple_attempts
from schemas.address_base import AddressRequest
from schemas.basic_response import BasicResponse


def create_address(db: Session, request: AddressRequest) -> DbAddress:
    if request.type_owner.value == 'market':
        return create_branch_address(db, request)
    elif request.type_owner.value == 'client':
        return create_client_address(db, request)
    else:
        raise type_not_found_exception


def create_branch_address(db: Session, request: AddressRequest) -> DbAddress:
    request.id_client = None
    if request.id_branch is None:
        raise not_values_sent_exception

    # Due to branch only can have an address, the address always will be the main address
    request.is_main = True

    try:
        branch_address = get_address_by_id_branch(db, request.id_branch)
    except element_not_found_exception:
        return add_address(db, request)
    else:
        return update_address(db, request, branch_address.id_address)


def create_client_address(db: Session, request: AddressRequest) -> DbAddress:
    request.id_branch = None
    if request.id_client is None:
        raise not_values_sent_exception

    try:
        past_main_address = get_main_address_of_client(db, request.id_client)
    except element_not_found_exception:
        # We ensure that at least one address is main
        request.is_main = True
    else:
        if request.is_main:
            past_main_address.is_main = False

            try:
                db.commit()
                db.refresh(past_main_address)
            except Exception as e:
                db.rollback()
                raise db_exception

    return add_address(db, request)


@multiple_attempts
def add_address(db: Session, request: AddressRequest) -> DbAddress:
    new_address = DbAddress(
        id_branch=request.id_branch,
        id_client=request.id_client,
        type_owner=request.type_owner.value,
        is_main=request.is_main,
        zip_code=request.zip_code,
        state=request.state,
        city=request.city,
        neighborhood=request.neighborhood,
        street=request.street,
        ext_number=request.ext_number,
        inner_number=request.inner_number
    )

    try:
        db.add(new_address)
        db.commit()
        db.refresh(new_address)
    except Exception as e:
        db.rollback()
        raise db_exception

    return new_address


def get_address_by_id_address(db: Session, id_address: int) -> Optional[DbAddress]:
    try:
        address = db.query(DbAddress).where(
            DbAddress.id_address == id_address,
            DbAddress.dropped == False
        ).one_or_none()

    except Exception as e:
        raise db_exception

    if address is None:
        raise element_not_found_exception

    return address


def get_addresses_by_type_owner(db: Session, type_owner: str) -> Optional[List[DbAddress]]:
    try:
        addresses = db.query(DbAddress).where(
            DbAddress.type_owner == type_owner
        ).all()

    except Exception as e:
        raise db_exception

    return addresses


def get_address_by_id_branch(db: Session, id_branch: str) -> DbAddress:
    try:
        address = db.query(DbAddress).where(
            DbAddress.id_branch == id_branch,
            DbAddress.type_owner == 'market',
            DbAddress.dropped == False
        ).one_or_none()
    except MultipleResultsFound:
        raise not_unique_value
    except Exception as e:
        raise db_exception

    if address is None:
        raise element_not_found_exception

    return address


def get_addresses_by_id_client(db: Session, id_client: str) -> List[DbAddress]:
    try:
        addresses = db.query(DbAddress).where(
            DbAddress.id_client == id_client,
            DbAddress.type_owner == 'client',
            DbAddress.dropped == False
        ).all()
    except Exception as e:
        raise db_exception

    if addresses is None:
        raise element_not_found_exception

    return addresses


def get_main_address_of_client(db: Session, id_client: str) -> DbAddress:
    try:
        address = db.query(DbAddress).where(
            DbAddress.id_client == id_client,
            DbAddress.type_owner == 'client',
            DbAddress.is_main == True,
            DbAddress.dropped == False
        ).one_or_none()
    except MultipleResultsFound:
        raise not_unique_value
    except Exception as e:
        raise db_exception

    if address is None:
        raise element_not_found_exception

    return address


@multiple_attempts
def update_address(db: Session, request: AddressRequest, id_address: int) -> DbAddress:
    updated_address = get_address_by_id_address(db, id_address)

    updated_address.is_main = request.is_main
    updated_address.zip_code = request.zip_code
    updated_address.state = request.state
    updated_address.city = request.city
    updated_address.neighborhood = request.neighborhood
    updated_address.street = request.street
    updated_address.ext_number = request.ext_number
    updated_address.inner_number = request.inner_number
    updated_address.dropped = False

    try:
        db.commit()
        db.refresh(updated_address)
    except Exception as e:
        db.rollback()
        raise db_exception

    return updated_address


def delete_addresses_by_id_owner(db: Session, id_owner: str, type_owner: str) -> BasicResponse:
    if type_owner == 'market':
        address = get_address_by_id_branch(db, id_owner)
        return delete_address(db, address.id_address)
    elif type_owner == 'client':
        return delete_addresses_by_id_client(db, id_owner)
    else:
        raise type_not_found_exception


@multiple_attempts
def delete_address(db: Session, id_address: int) -> BasicResponse:
    address = get_address_by_id_address(db, id_address)
    address.dropped = True

    try:
        db.commit()
        db.refresh(address)
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )


@multiple_attempts
def delete_addresses_by_id_client(db: Session, id_client: str) -> BasicResponse:
    addresses = get_addresses_by_id_client(db, id_client)

    for address in addresses:
        address.dropped = True

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="batch delete",
        successful=True
    )








