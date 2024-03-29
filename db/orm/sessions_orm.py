from datetime import datetime
from typing import Union, Optional, List

from sqlalchemy.orm import Session

from db.models.sessions_db import DbSession
from db.orm.exceptions_orm import element_not_found_exception, wrong_data_sent_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from schemas.basic_response import BasicResponse
from schemas.session_base import SessionRequest, SessionStrRequest


@multiple_attempts
@full_database_exceptions
def start_session(db: Session, request: Union[SessionRequest, SessionStrRequest]) -> DbSession:
    if request.session_start is None:
        start_session_user = datetime.utcnow()
    else:
        start_session_user = get_time_session_as_datetime_object(request.session_start)

    new_session = DbSession(
        id_user=request.id_user,
        session_start=start_session_user,
        session_finish=None
    )

    try:
        db.add(new_session)
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return new_session


@multiple_attempts
@full_database_exceptions
def finish_session(
        db: Session,
        request: Union[SessionRequest, SessionStrRequest],
        id_session: int = None,
        session_obj: DbSession = None
) -> DbSession:

    if isinstance(session_obj, DbSession):
        updated_session = session_obj
    elif isinstance(id_session, int):
        updated_session = get_session_by_id_session(db, id_session)
    else:
        raise wrong_data_sent_exception

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
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return updated_session


@full_database_exceptions
def get_session_by_id_session(db: Session, id_session: int) -> DbSession:
    try:
        session = db.query(DbSession).where(
            DbSession.id_session == id_session
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if session is None:
        raise element_not_found_exception

    return session


@full_database_exceptions
def get_sessions_by_id_user(db: Session, id_user: int) -> List[DbSession]:
    try:
        sessions: List[DbSession] = db.query(DbSession).where(
            DbSession.id_user == id_user
        ).all()
    except Exception as e:
        print(e)
        raise e

    if sessions is None or len(sessions) < 1:
        raise element_not_found_exception

    return sessions


@full_database_exceptions
def get_active_sessions_by_id_user(db: Session, id_user: int) -> List[DbSession]:
    try:
        active_sessions: List[DbSession] = db.query(DbSession).where(
            DbSession.id_user == id_user,
            DbSession.session_finish == None
        ).all()
    except Exception as e:
        print(e)
        raise e

    return active_sessions


@multiple_attempts
@full_database_exceptions
def finish_all_active_sessions_of_user(db: Session, id_user: int) -> BasicResponse:
    active_sessions: List[DbSession] = get_active_sessions_by_id_user(db, id_user)

    if len(active_sessions) > 0:
        finish_time_session = datetime.utcnow()
        for active_session in active_sessions:
            active_session.session_finish = finish_time_session

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return BasicResponse(
        operation="Finish active sessions",
        successful=True
    )


@multiple_attempts
@full_database_exceptions
def delete_session(db: Session, id_session: int) -> BasicResponse:
    session = get_session_by_id_session(db, id_session)

    try:
        db.delete(session)
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return BasicResponse(
        operation="delete",
        successful=True
    )


@multiple_attempts
@full_database_exceptions
def delete_sessions_by_id_user(db: Session, id_user: int) -> BasicResponse:
    sessions: List[DbSession] = get_sessions_by_id_user(db, id_user)

    if len(sessions) > 0:
        for session in sessions:
            try:
                db.delete(session)
            except Exception as e:
                db.rollback()
                print(e)
                raise e

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(e)
            raise e

    return BasicResponse(
        operation="batch delete",
        successful=True
    )


def get_time_session_as_datetime_object(session: Union[str, datetime, None]) -> Optional[datetime]:
    datetime_format = "%Y-%m-%d %H:%M:%S"

    if session is not None:
        if isinstance(session, str):
            session_str = session.replace("T", " ").replace(".", "-").replace("/", "-")
            try:
                session_datetime = datetime.strptime(session_str, datetime_format)
            except ValueError:
                raise wrong_data_sent_exception
        else:
            session_datetime = session
    else:
        return session

    return session_datetime
