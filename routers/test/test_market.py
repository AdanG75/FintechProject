from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session
from starlette import status

from controller.login_controller import get_current_token, check_type_user
from db.database import get_db
from db.orm import markets_orm
from db.orm.exceptions_orm import credentials_exception
from schemas.basic_response import BasicResponse
from schemas.market_base import MarketDisplay, MarketRequest
from schemas.token_base import TokenSummary

router = APIRouter(
    prefix="/test/market",
    tags=["tests", "market"]
)


@router.post(
    path="/",
    response_model=MarketDisplay,
    status_code=status.HTTP_201_CREATED
)
async def create_market(
        request: MarketRequest = Body(...),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = markets_orm.create_market(db, request)

    return response


@router.get(
    path="/{id_market}",
    response_model=MarketDisplay,
    status_code=status.HTTP_200_OK
)
async def get_market(
        id_market: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = markets_orm.get_market_by_id_market(db, id_market)

    return response


@router.get(
    path="/user/{id_user}",
    response_model=MarketDisplay,
    status_code=status.HTTP_200_OK
)
async def get_market_by_id_user(
        id_user: int = Path(..., gt=0),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = markets_orm.get_market_by_id_user(db, id_user)

    return response


@router.put(
    path='/{id_market}',
    response_model=MarketDisplay,
    status_code=status.HTTP_200_OK
)
async def update_market(
        id_market: str = Path(..., min_length=12, max_length=49),
        request: MarketRequest = Body(...),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = markets_orm.update_market(db, request, id_market)

    return response


@router.delete(
    path='/{id_market}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_market(
        id_market: str = Path(..., min_length=12, max_length=49),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = markets_orm.delete_market(db, id_market)

    return response
