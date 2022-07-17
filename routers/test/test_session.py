from typing import List

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session
from starlette import status

from db.database import get_db
from db.orm import sessions_orm
from schemas.basic_response import BasicResponse
from schemas.session_base import SessionDisplay, SessionStrRequest

router = APIRouter(
    prefix="/test/session",
    tags=["tests", "session"]
)


@router.post(
    path="/",
    response_model=SessionDisplay,
    status_code=status.HTTP_201_CREATED
)
async def new_session(
        request: SessionStrRequest = Body(...),
        db: Session = Depends(get_db)
):
    response = sessions_orm.start_session(db, request)

    return response


@router.patch(
    path='/end-session/{id_session}',
    response_model=SessionDisplay,
    status_code=status.HTTP_200_OK
)
async def finnish_session(
        id_session: int = Path(..., gt=0),
        request: SessionStrRequest = Body(...),
        db: Session = Depends(get_db)
):
    response = sessions_orm.finish_session(db, request, id_session)

    return response


@router.delete(
    path='/{id_session}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_session(
        id_session: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = sessions_orm.delete_session(db, id_session)

    return response


@router.delete(
    path="/user/{id_user}",
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_sessions_of_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = sessions_orm.delete_sessions_by_id_user(db, id_user)

    return response


@router.get(
    path="/{id_session}",
    response_model=SessionDisplay,
    status_code=status.HTTP_200_OK
)
async def get_session(
        id_session: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = sessions_orm.get_session_by_id_session(db, id_session)

    return response


@router.get(
    path='/user/{id_user}',
    response_model=List[SessionDisplay],
    status_code=status.HTTP_200_OK
)
async def get_sessions_of_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = sessions_orm.get_sessions_by_id_user(db, id_user)

    return response


@router.get(
    path='/active/user/{id_user}',
    response_model=List[SessionDisplay],
    status_code=status.HTTP_200_OK
)
async def get_active_sessions_of_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = sessions_orm.get_active_sessions_by_id_user(db, id_user)

    return response


@router.put(
    path='/active/user/{id_user}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def close_active_sessions_of_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = sessions_orm.finish_all_active_sessions_of_user(db, id_user)

    return response
