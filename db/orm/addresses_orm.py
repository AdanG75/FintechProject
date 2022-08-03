from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from db.models.addresses_db import DbAddress
from db.models.branches_db import DbBranch  # Don't erase because it is used by relationship
from db.models.clients_db import DbClient  # Don't erase because it is used by relationship
from db.models.fingerprints_db import DbFingerprint  # Don't erase because it is used by relationship
from db.models.markets_db import DbMarket  # Don't erase because it is used by relationship
from db.orm.branches_orm import get_branch_by_id
from db.orm.clients_orm import get_client_by_id_client
from db.orm.exceptions_orm import element_not_found_exception, type_not_found_exception, \
    not_values_sent_exception, NotFoundException, option_not_found_exception, not_valid_operation_exception, \
    operation_need_a_precondition_exception, not_main_element_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from schemas.address_base import AddressRequest
from schemas.basic_response import BasicResponse


def create_address(db: Session, request: AddressRequest, execute: str = 'now') -> DbAddress:
    if request.type_owner.value == 'market':
        return create_branch_address(db, request, execute=execute)
    elif request.type_owner.value == 'client':
        return create_client_address(db, request, execute=execute)
    else:
        raise type_not_found_exception


def create_branch_address(db: Session, request: AddressRequest, execute: str = 'now') -> DbAddress:
    request.id_client = None
    if request.id_branch is None:
        raise not_values_sent_exception

    try:
        get_branch_by_id(db, request.id_branch)
    except NotFoundException:
        raise element_not_found_exception

    # Due to branch only can have an address, the address always will be the main address
    request.is_main = True

    try:
        branch_address = get_address_by_id_branch(db, request.id_branch, mode='all')
    except NotFoundException:
        return add_address(db, request, execute=execute)
    else:
        if branch_address.dropped:
            return update_address(db, request, branch_address.id_address, mode='all', execute=execute)
        else:
            raise not_valid_operation_exception


def create_client_address(db: Session, request: AddressRequest, execute: str = 'now') -> DbAddress:
    request.id_branch = None
    if request.id_client is None:
        raise not_values_sent_exception

    try:
        get_client_by_id_client(db, request.id_client)
    except NotFoundException:
        raise element_not_found_exception

    flag_is_first_address = False
    try:
        get_addresses_by_id_client(db, request.id_client)
    except NotFoundException:
        flag_is_first_address = True
        # We ensure that at least one address is main
        request.is_main = True
    else:
        if request.is_main and not flag_is_first_address:
            change_main_address(
                db=db,
                id_client=request.id_client,
                execute='wait'
            )

    return add_address(db, request, execute=execute)


@multiple_attempts
@full_database_exceptions
def add_address(db: Session, request: AddressRequest, execute: str = 'now') -> DbAddress:
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
        inner_number=request.inner_number,
        created_time=datetime.utcnow(),
        dropped=False
    )

    try:
        db.add(new_address)
        if execute == 'now':
            db.commit()
            db.refresh(new_address)
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return new_address


@full_database_exceptions
def get_address_by_id_address(db: Session, id_address: int, mode: str = 'active') -> Optional[DbAddress]:

    if mode == 'active':
        try:
            address = db.query(DbAddress).where(
                DbAddress.id_address == id_address,
                DbAddress.dropped == False
            ).one_or_none()

        except Exception as e:
            print(e)
            raise e
    elif mode == 'all':
        try:
            address = db.query(DbAddress).where(
                DbAddress.id_address == id_address
            ).one_or_none()

        except Exception as e:
            print(e)
            raise e
    else:
        raise option_not_found_exception

    if address is None:
        raise element_not_found_exception

    return address


@full_database_exceptions
def get_addresses_by_type_owner(db: Session, type_owner: str) -> Optional[List[DbAddress]]:
    try:
        addresses = db.query(DbAddress).where(
            DbAddress.type_owner == type_owner,
            DbAddress.dropped == False
        ).all()

    except Exception as e:
        print(e)
        raise e

    return addresses


@full_database_exceptions
def get_address_by_id_branch(
        db: Session,
        id_branch: str,
        mode: str = 'active'
) -> DbAddress:
    if mode == 'active':
        try:
            address = db.query(DbAddress).where(
                DbAddress.id_branch == id_branch,
                DbAddress.type_owner == 'market',
                DbAddress.dropped == False
            ).one_or_none()
        except Exception as e:
            print(e)
            raise e
    elif mode == 'all':
        try:
            address = db.query(DbAddress).where(
                DbAddress.id_branch == id_branch,
                DbAddress.type_owner == 'market'
            ).one_or_none()
        except Exception as e:
            print(e)
            raise e
    else:
        raise option_not_found_exception

    if address is None:
        raise element_not_found_exception

    return address


@full_database_exceptions
def get_addresses_by_id_client(db: Session, id_client: str, mode: str = 'active') -> List[DbAddress]:
    try:
        if mode == 'active':
            addresses = db.query(DbAddress).where(
                DbAddress.id_client == id_client,
                DbAddress.type_owner == 'client',
                DbAddress.dropped == False
            ).all()
        elif mode == 'all':
            addresses = db.query(DbAddress).where(
                DbAddress.id_client == id_client,
                DbAddress.type_owner == 'client'
            ).all()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    if addresses is None or len(addresses) < 1:
        raise element_not_found_exception

    return addresses


@full_database_exceptions
def get_main_address_of_client(db: Session, id_client: str) -> DbAddress:
    try:
        address = db.query(DbAddress).where(
            DbAddress.id_client == id_client,
            DbAddress.type_owner == 'client',
            DbAddress.is_main == True,
            DbAddress.dropped == False
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if address is None:
        raise element_not_found_exception

    return address


@full_database_exceptions
def get_a_secondary_address_of_client(db: Session, id_client: str) -> DbAddress:
    try:
        address = db.query(DbAddress).where(
            DbAddress.id_client == id_client,
            DbAddress.type_owner == 'client',
            DbAddress.is_main == False,
            DbAddress.dropped == False
        ).first()
    except Exception as e:
        print(e)
        raise e

    if address is None:
        raise element_not_found_exception

    return address


@multiple_attempts
@full_database_exceptions
def update_address(
        db: Session,
        request: AddressRequest,
        id_address: int,
        mode: str = 'active',
        execute: str = 'now'
) -> DbAddress:
    updated_address = get_address_by_id_address(db, id_address, mode=mode)

    if updated_address.is_main:
        if not request.is_main:
            raise not_main_element_exception

    else:
        if request.is_main:
            # Only clients can change main address due to branch object only have one address associate to it.
            change_main_address(
                db=db,
                id_client=updated_address.id_client,
                new_main_address=updated_address,
                execute='wait'
            )

    updated_address.zip_code = request.zip_code
    updated_address.state = request.state
    updated_address.city = request.city
    updated_address.neighborhood = request.neighborhood
    updated_address.street = request.street
    updated_address.ext_number = request.ext_number
    updated_address.inner_number = request.inner_number
    updated_address.dropped = False

    if execute == 'now':
        try:
            db.commit()
            db.refresh(updated_address)
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    elif execute == 'wait':
        pass
    else:
        raise option_not_found_exception

    return updated_address


@multiple_attempts
@full_database_exceptions
def change_main_address(
        db: Session,
        id_client: Optional[str] = None,
        id_address: Optional[int] = None,
        new_main_address: Optional[DbAddress] = None,
        execute: str = 'now'
) -> bool:
    flag_id_client_none = False

    if id_client is not None:
        __change_main_address(db, id_client, execute='wait')
    else:
        flag_id_client_none = True

    if new_main_address is not None:
        if flag_id_client_none:
            __change_main_address(db, new_main_address.id_client, execute='wait')

        new_main_address.is_main = True
    else:
        if id_address is not None:
            main_address = get_address_by_id_address(db, id_address)
            if flag_id_client_none:
                __change_main_address(db, main_address.id_client, execute='wait')

            main_address.is_main = True

    if execute == 'now':
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    elif execute == 'wait':
        pass
    else:
        raise option_not_found_exception

    return True


def __change_main_address(
        db: Session,
        id_client: Optional[str] = None,
        execute: str = 'now'
):
    if id_client is not None:
        past_main_address = get_main_address_of_client(db, id_client)
        past_main_address.is_main = False

        if execute == 'now':
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                print(e)
                raise e
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception


def delete_addresses_by_id_owner(
        db: Session,
        id_owner: str,
        type_owner: str,
        execute: str = 'now'
) -> BasicResponse:
    if type_owner == 'market':
        address = get_address_by_id_branch(db, id_owner)
        return delete_address(db, address.id_address, execute=execute)
    elif type_owner == 'client':
        return delete_addresses_by_id_client(db, id_owner, execute=execute)
    else:
        raise type_not_found_exception


@multiple_attempts
@full_database_exceptions
def delete_address(db: Session, id_address: int, execute: str = 'now') -> BasicResponse:
    address = get_address_by_id_address(db, id_address)

    if address.type_owner == 'market':
        try:
            get_branch_by_id(db, address.id_branch)
        except NotFoundException:
            # If branch was not found that means it was deleted
            pass
        else:
            # It is necessary that the branch is erased to drop this address.
            raise operation_need_a_precondition_exception
    elif address.type_owner == 'client':
        if address.is_main:
            try:
                secondary_address = get_a_secondary_address_of_client(db, address.id_client)
                change_main_address(db, new_main_address=secondary_address, execute='wait')
            except NotFoundException:
                raise not_main_element_exception
    else:
        raise option_not_found_exception

    address.dropped = True

    if execute == 'now':
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    elif execute == 'wait':
        pass
    else:
        raise option_not_found_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )


@multiple_attempts
@full_database_exceptions
def delete_addresses_by_id_client(db: Session, id_client: str, execute: str = 'now') -> BasicResponse:
    try:
        get_client_by_id_client(db, id_client)
    except NotFoundException:
        # If client was not found that means it was deleted
        pass
    else:
        # It is necessary that the client is erased to drop all addresses.
        raise operation_need_a_precondition_exception

    addresses = get_addresses_by_id_client(db, id_client)

    for address in addresses:
        address.is_main = False
        address.dropped = True

    if execute == 'now':
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    elif execute == 'wait':
        pass
    else:
        raise option_not_found_exception

    return BasicResponse(
        operation="Batch delete",
        successful=True
    )
