import uuid
from datetime import date, datetime
from typing import Optional, Union

from sqlalchemy.orm import Session

from db.models.addresses_db import DbAddress  # Don't erase because it is used by relationship
from db.models.branches_db import DbBranch  # Don't erase because it is used by relationship
from db.models.clients_db import DbClient
from db.models.fingerprints_db import DbFingerprint  # Don't erase because it is used by SQLAlchemy
from db.models.markets_db import DbMarket  # Don't erase because it is used by relationship
from db.models.users_db import DbUser
from db.orm.exceptions_orm import element_not_found_exception, type_of_value_not_compatible, wrong_data_sent_exception, \
    option_not_found_exception, NotFoundException, not_unique_value, operation_need_a_precondition_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.users_orm import get_user_by_id
from schemas.basic_response import BasicResponse
from schemas.client_base import ClientRequest


@multiple_attempts
def create_client(db: Session, request: ClientRequest, execute: str = 'now') -> DbClient:

    user: Optional[DbUser] = get_user_by_id(db, request.id_user)
    if user.type_user != 'client':
        raise type_of_value_not_compatible

    # Clear user object to save space
    user = None

    try:
        client = get_client_by_id_user(db, request.id_user, mode='all')
    except NotFoundException:
        date_birthday = cast_str_date_to_date_object(request.birth_date)

        client_uuid = uuid.uuid4().hex
        id_client = f"CLI-{client_uuid}"

        new_client = DbClient(
            id_client=id_client,
            id_user=request.id_user,
            last_name=request.last_name,
            birth_date=date_birthday,
            dropped=False
        )

        try:
            db.add(new_client)
            if execute == 'now':
                db.commit()
                db.refresh(new_client)
            elif execute == 'wait':
                pass
            else:
                raise option_not_found_exception
        except Exception as e:
            db.rollback()
            print(e)
            raise e

        return new_client

    if client.dropped:
        return update_client(
            db,
            request,
            client.id_client,
            mode='all',
            execute=execute
        )

    raise not_unique_value


@full_database_exceptions
def get_client_by_id_client(db: Session, id_client: str, mode: str = 'active') -> DbClient:
    if mode == 'active':
        try:
            client = db.query(DbClient).where(
                DbClient.id_client == id_client,
                DbClient.dropped == False
            ).one_or_none()
        except Exception as e:
            print(e)
            raise e
    elif mode == 'all':
        try:
            client = db.query(DbClient).where(
                DbClient.id_client == id_client
            ).one_or_none()
        except Exception as e:
            print(e)
            raise e
    else:
        raise option_not_found_exception

    if client is None:
        raise element_not_found_exception

    return client


@full_database_exceptions
def get_client_by_id_user(db: Session, id_user: int, mode: str = 'active') -> DbClient:
    try:
        if mode == 'active':
            client = db.query(DbClient).where(
                DbClient.id_user == id_user,
                DbClient.dropped == False
            ).one_or_none()
        elif mode == 'all':
            client = db.query(DbClient).where(
                DbClient.id_user == id_user
            ).one_or_none()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    if client is None:
        raise element_not_found_exception

    return client


@multiple_attempts
@full_database_exceptions
def update_client(
        db: Session,
        request: ClientRequest,
        id_client: str,
        mode: str = 'active',
        execute: str = 'now'
) -> DbClient:
    updated_client = get_client_by_id_client(db, id_client, mode=mode)

    updated_client.last_name = request.last_name
    updated_client.birth_date = request.birth_date
    updated_client.dropped = False

    if execute == 'now':
        try:
            db.commit()
            db.refresh(updated_client)
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    elif execute == 'wait':
        pass
    else:
        raise option_not_found_exception

    return updated_client


@multiple_attempts
@full_database_exceptions
def delete_client(db: Session, id_client: str, execute: str = 'now') -> BasicResponse:
    client = get_client_by_id_client(db, id_client)
    try:
        get_user_by_id(db, client.id_user)
    except NotFoundException:
        # If user was not found that means it was deleted
        pass
    else:
        # It is necessary that the user is erased to drop the client.
        raise operation_need_a_precondition_exception

    client.dropped = True

    if execute == 'now':
        try:
            # No longer necessary
            # db.delete(client)
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


def cast_str_date_to_date_object(this_date: Union[str, date]) -> date:
    if isinstance(this_date, str):
        date_format = "%Y-%m-%d"
        this_date_clean = this_date.replace(".", "-").replace("/", "-")
        try:
            date_object = datetime.strptime(this_date_clean, date_format).date()
        except ValueError:
            raise wrong_data_sent_exception
    else:
        date_object = this_date

    return date_object
