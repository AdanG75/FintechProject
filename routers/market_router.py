from typing import Union

from fastapi import APIRouter, Query, Depends, Path
from sqlalchemy.orm import Session
from starlette import status

from controller.login_controller import get_current_token
from controller.market_controller import get_all_markets, get_market_based_on_client
from controller.secure_controller import cipher_response_message
from db.database import get_db
from db.orm.exceptions_orm import not_authorized_exception, only_available_client_exception
from schemas.market_complex import MarketSimpleListDisplay, MarketCreditClient
from schemas.secure_base import SecureBase
from schemas.token_base import TokenSummary
from schemas.type_user import TypeUser

router = APIRouter(
    tags=['market']
)


@router.get(
    path='/market',
    response_model=Union[SecureBase, MarketSimpleListDisplay],
    status_code=status.HTTP_200_OK
)
async def get_markets(
        secure: bool = Query(True),
        exc_system: bool = Query(False),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    response = get_all_markets(db, exc_system)

    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.get(
    path='/market/{id_market}/client/{id_user}',
    response_model=Union[SecureBase, MarketCreditClient],
    status_code=status.HTTP_200_OK
)
async def get_market_based_client(
        id_market: str = Path(..., min_length=12, max_length=49),
        id_user: int = Path(..., gt=0),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if id_user != current_token.id_user:
        raise not_authorized_exception

    if current_token.type_user != TypeUser.client.value:
        raise only_available_client_exception

    response = get_market_based_on_client(db, id_market, current_token.id_type)

    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response
