from typing import Optional

from sqlalchemy.orm import Session

from db.models.addresses_db import DbAddress
from db.orm.exceptions_orm import db_exception, element_not_found_exception
from db.orm.functions_orm import multiple_attempts
from schemas.address_base import AddressRequest
from schemas.basic_response import BasicResponse


@multiple_attempts
def create_address(db: Session, request: AddressRequest) -> DbAddress:
    new_address = DbAddress(
        zip_code=request.zip_code,
        state=request.state,
        city=request.city,
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


def get_address_by_id(db: Session, id_address: int) -> Optional[DbAddress]:
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


@multiple_attempts
def update_address(db: Session, request: DbAddress, id_address: int) -> DbAddress:
    updated_address = get_address_by_id(db, id_address)

    updated_address.city = request.city
    updated_address.state = request.state
    updated_address.street = request.street
    updated_address.zip_code = request.zip_code
    updated_address.ext_number = request.ext_number
    updated_address.inner_number = request.inner_number

    try:
        db.commit()
        db.refresh(updated_address)
    except Exception as e:
        db.rollback()
        raise db_exception

    return updated_address


@multiple_attempts
def delete_address(db: Session, id_address: int) -> BasicResponse:
    address = get_address_by_id(db, id_address)
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



