import uuid
from datetime import date, datetime
from typing import Optional, Union

from sqlalchemy.orm import Session

from db.models.addresses_db import DbAddress  # Don't erase, it's used by relationship from SQLAlchemy
from db.models.branches_db import DbBranch  # Don't erase, it's used by relationship from SQLAlchemy
from db.models.clients_db import DbClient
from db.models.fingerprints_db import DbFingerprint  # Don't erase, it's used by relationship from SQLAlchemy
from db.models.users_db import DbUser
from db.orm.exceptions_orm import element_not_found_exception, type_of_value_not_compatible, wrong_data_sent_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.users_orm import get_user_by_id
from schemas.basic_response import BasicResponse
from schemas.client_base import ClientRequest


@multiple_attempts
def create_client(db: Session, request: ClientRequest) -> DbClient:

    user: Optional[DbUser] = get_user_by_id(db, request.id_user)
    if user.type_user != 'client':
        raise type_of_value_not_compatible

    # Clear user object to save space
    user = None

    date_birthday = cast_str_date_to_date_object(request.birth_date)

    client_uuid = uuid.uuid4().hex
    id_client = f"CLI-{client_uuid}"

    new_client = DbClient(
        id_client=id_client,
        id_user=request.id_user,
        last_name=request.last_name,
        birth_date=date_birthday
    )

    try:
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return new_client


@full_database_exceptions
def get_client_by_id_client(db: Session, id_client: str) -> DbClient:
    try:
        client = db.query(DbClient).where(
            DbClient.id_client == id_client
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if client is None:
        raise element_not_found_exception

    return client


@full_database_exceptions
def get_client_by_id_user(db: Session, id_user: int) -> DbClient:
    try:
        client = db.query(DbClient).where(
            DbClient.id_user == id_user
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if client is None:
        raise element_not_found_exception

    return client


@multiple_attempts
@full_database_exceptions
def update_client(db: Session, request: ClientRequest, id_client: str) -> DbClient:
    updated_client = get_client_by_id_client(db, id_client)

    updated_client.last_name = request.last_name
    updated_client.birth_date = request.birth_date

    try:
        db.commit()
        db.refresh(updated_client)
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return updated_client


@multiple_attempts
@full_database_exceptions
def delete_client(db: Session, id_client: str) -> BasicResponse:
    client = get_client_by_id_client(db, id_client)

    try:
        db.delete(client)
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        raise e

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
