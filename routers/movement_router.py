from typing import Union

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from starlette import status

from controller.login_controller import get_current_token
from controller.movement_controller import get_payments_of_client, get_payments_of_market
from controller.secure_controller import cipher_response_message
from db.database import get_db
from db.orm.exceptions_orm import not_authorized_exception, type_of_value_not_compatible
from schemas.payment_base import PaymentComplexList
from schemas.secure_base import SecureBase
from schemas.token_base import TokenSummary
from schemas.type_user import TypeUser

router = APIRouter(
    tags=['movement']
)


@router.get(
    path='/movement/user/{id_user}/payments',
    response_model=Union[SecureBase, PaymentComplexList],
    status_code=status.HTTP_200_OK
)
async def get_payments_of_user(
        id_user: int = Path(..., gt=0),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if current_token.id_user != id_user:
        raise not_authorized_exception

    if current_token.type_user == TypeUser.client.value:
        response = get_payments_of_client(db, current_token.id_type)
    elif current_token.type_user == TypeUser.market.value or current_token.type_user == TypeUser.system.value:
        response = get_payments_of_market(db, current_token.id_type)
    else:
        raise type_of_value_not_compatible

    if secure:
        secure_response = cipher_response_message(db=db, id_user=id_user, response=response)
        return secure_response

    return response
