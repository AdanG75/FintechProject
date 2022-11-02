from typing import Union

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from starlette import status

from controller.login_controller import get_current_token
from controller.market_controller import get_all_markets
from controller.secure_controller import cipher_response_message
from db.database import get_db
from schemas.market_complex import MarketSimpleListDisplay
from schemas.secure_base import SecureBase
from schemas.token_base import TokenSummary

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
