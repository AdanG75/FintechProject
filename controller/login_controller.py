from datetime import datetime, timedelta

from fastapi import Depends
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from auth.token_functions import create_access_token, oauth2_schema, SECRET_KEY, ALGORITHM, is_token_expired
from controller.user_controller import return_type_id_based_on_type_of_user
from db.database import get_db
from db.models.sessions_db import DbSession
from db.models.users_db import DbUser
from db.orm.exceptions_orm import email_or_password_are_wrong_exception, NotFoundException, too_early_exception, \
    credentials_exception, expired_session_exception, expired_token_exception
from db.orm.login_attempts_orm import check_attempt, add_attempt, reset_login_attempt
from db.orm.sessions_orm import start_session, get_session_by_id_session, finish_session
from db.orm.users_orm import get_user_by_email
from schemas.movement_base import UserDataMovement
from schemas.session_base import SessionRequest
from schemas.token_base import TokenBase, TokenSummary
from schemas.type_user import TypeUser
from secure.hash import Hash


def login(db: Session, email: str, password: str) -> TokenBase:
    try:
        user: DbUser = get_user_by_email(db, email)
    except NotFoundException:
        raise email_or_password_are_wrong_exception

    # Check if login it is a valid operation
    if check_attempt(db, user.id_user, raise_exception=True):
        if not Hash.verify(user.password, password):
            add_attempt(db, user.id_user)
            raise email_or_password_are_wrong_exception

        else:
            # Reset login attempts
            reset_login_attempt(db, user.id_user)
            # Start a new session
            session_request = SessionRequest(
                id_user=user.id_user,
                session_start=datetime.utcnow(),
                session_finish=None
            )
            new_session: DbSession = start_session(db, session_request)

    else:
        raise too_early_exception

    # Set expire time within token
    expires_delta = timedelta(days=1) if user.type_user == 'market' else None
    # Get id_type based on type user
    id_type = return_type_id_based_on_type_of_user(db, user.id_user, user.type_user)
    # Create access token
    access_token = create_access_token(
        data={
            "id_user": user.id_user,
            "type_user": user.type_user,
            "id_type": id_type,
            "id_session": new_session.id_session
        },
        expires_delta=expires_delta
    )

    return TokenBase(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id_user,
        type_user=user.type_user,
        id_type=id_type
    )


def logout(db: Session, id_session: int) -> bool:
    session_request = SessionRequest(
        id_user=1,
        session_start=None,
        session_finish=datetime.utcnow()
    )
    finish_session(db, session_request, id_session=id_session)

    return True


def get_current_token(token: str = Depends(oauth2_schema), db: Session = Depends(get_db)) -> TokenSummary:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("id_session") is None or payload.get("id_user") is None \
                or payload.get("type_user") is None or payload.get("id_type") is None or payload.get("exp") is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    current_session: DbSession = get_session_by_id_session(db, payload.get("id_session"))
    if current_session.session_finish is not None:
        raise expired_session_exception

    if not is_token_expired(payload.get("exp")):
        token_obj = TokenSummary.parse_obj(payload)
        return token_obj

    else:
        session_request = SessionRequest(
            id_user=1,
            session_start=None,
            session_finish=datetime.utcnow()
        )
        finish_session(db, session_request, session_obj=current_session)

        raise expired_token_exception


def check_type_user(token_summary: TokenSummary, is_a: str) -> bool:
    if token_summary.type_user == is_a:
        return True
    else:
        return False


def get_logged_user_to_make_movement(token_summary: TokenSummary) -> UserDataMovement:
    return UserDataMovement(
        id_performer=token_summary.id_user,
        type_user=TypeUser(token_summary.type_user),
        id_type_performer=token_summary.id_type,
        id_requester=None
    )
