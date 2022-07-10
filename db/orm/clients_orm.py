import uuid

from sqlalchemy.orm import Session

from db.models.clients_db import DbClient
from db.orm.exceptions_orm import db_exception, element_not_found_exception
from db.orm.functions_orm import multiple_attempts
from schemas.basic_response import BasicResponse
from schemas.client_base import ClientBase, ClientRequest


@multiple_attempts
def create_client(db: Session, request: ClientBase) -> DbClient:
    client_uuid = uuid.uuid4().hex
    id_client = f"CLI-{client_uuid}"

    new_client = DbClient(
        id_client=id_client,
        id_user=request.id_user,
        last_name=request.last_name,
        birth_date=request.birth_date
    )

    try:
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
    except Exception as e:
        db.rollback()
        raise db_exception

    return new_client


def get_client_by_id_client(db: Session, id_client: str) -> DbClient:
    try:
        client = db.query(DbClient).where(
            DbClient.id_client == id_client
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if client is None:
        raise element_not_found_exception

    return client


def get_client_by_id_user(db: Session, id_user: int) -> DbClient:
    try:
        client = db.query(DbClient).where(
            DbClient.id_user == id_user
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if client is None:
        raise element_not_found_exception

    return client


@multiple_attempts
def update_client(db: Session, request: ClientRequest, id_client: str) -> DbClient:
    updated_client = get_client_by_id_client(db, id_client)

    updated_client.last_name = request.last_name
    updated_client.birth_date = request.birth_date

    try:
        db.commit()
        db.refresh(updated_client)
    except Exception as e:
        db.rollback()
        raise db_exception

    return updated_client


@multiple_attempts
def delete_client(db: Session, id_client: str) -> BasicResponse:
    client = get_client_by_id_client(db, id_client)

    try:
        db.delete(client)
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )
