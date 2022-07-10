from datetime import datetime
import uuid
from typing import Union, Optional, List

from sqlalchemy.orm import Session

from db.models.sessions_db import DbSession
from db.orm.exceptions_orm import db_exception, element_not_found_exception
from db.orm.functions_orm import multiple_attempts
from schemas.basic_response import BasicResponse
from schemas.session_base import SessionRequest, SessionStrRequest


@multiple_attempts
def start_session(db: Session, request: Union[SessionRequest, SessionStrRequest]) -> DbSession:
    if request.session_start is None:
        start_session_user = datetime.utcnow()
    else:
        start_session_user = get_time_session_as_datetime_object(request.session_start)

    session_uuid = uuid.uuid4().hex
    id_session = f"SSS-{session_uuid}"

    new_session = DbSession(
        id_session=id_session,
        id_user=request.id_user,
        session_start=start_session_user,
        session_finish=None
    )

    try:
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
    except Exception as e:
        db.rollback()
        raise db_exception

    return new_session


@multiple_attempts
def finish_session(db: Session, request: Union[SessionRequest, SessionStrRequest], id_session) -> DbSession:
    updated_session = get_session_by_id_session(db, id_session)

    if updated_session.session_finish is None:
        if request.session_finish is None:
            finish_session_user = datetime.utcnow()
        else:
            finish_session_user = get_time_session_as_datetime_object(request.session_finish)
    else:
        finish_session_user = updated_session.session_finish

    updated_session.session_finish = finish_session_user

    try:
        db.commit()
        db.refresh(updated_session)
    except Exception as e:
        db.rollback()
        raise db_exception

    return updated_session


def get_session_by_id_session(db: Session, id_session: str) -> DbSession:
    try:
        session = db.query(DbSession).where(
            DbSession.id_session == id_session
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if session is None:
        raise element_not_found_exception

    return session


def get_sessions_by_id_user(db: Session, id_user: int) -> List[DbSession]:
    try:
        sessions: List[DbSession] = db.query(DbSession).where(
            DbSession.id_user == id_user
        ).all()
    except Exception as e:
        raise db_exception

    if sessions is None or len(sessions) < 1:
        raise element_not_found_exception

    return sessions


def get_time_session_as_datetime_object(session: Union[str, datetime, None]) -> Optional[datetime]:
    datetime_format = "%Y-%m-%d %H:%M:%S"

    if session is not None:
        if isinstance(session, str):
            session_str = session.replace("T", " ")
            session_datetime = datetime.strptime(session_str, datetime_format)
        else:
            session_datetime = session
    else:
        return session

    return session_datetime


@multiple_attempts
def delete_session(db: Session, id_session: str) -> BasicResponse:
    session = get_session_by_id_session(db, id_session)

    try:
        db.delete(session)
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )
