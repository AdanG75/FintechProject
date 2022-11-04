from typing import Union

from fastapi import APIRouter, Path, Depends, Query
from sqlalchemy.orm import Session
from starlette import status

from controller.credit_controller import get_credits, check_owner_credit, get_credit_description
from controller.login_controller import get_current_token
from controller.secure_controller import cipher_response_message
from db.database import get_db
from db.orm.exceptions_orm import not_authorized_exception
from schemas.credit_base import ListCreditsDisplay
from schemas.credit_complex import CreditComplexProfile
from schemas.secure_base import SecureBase
from schemas.token_base import TokenSummary


router = APIRouter(
    tags=['credit']
)


@router.get(
    path='/credit/{id_credit}',
    response_model=Union[SecureBase, CreditComplexProfile],
    status_code=status.HTTP_200_OK
)
async def get_description_of_credit(
        id_credit: int = Path(..., gt=0),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_owner_credit(db, id_credit, current_token.type_user, current_token.id_type):
        raise not_authorized_exception

    response = await get_credit_description(db, id_credit, current_token.type_user)

    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response

@router.get(
    path='/credit/user/{id_user}',
    response_model=Union[SecureBase, ListCreditsDisplay],
    status_code=status.HTTP_200_OK
)
async def get_credits_of_user(
        id_user: int = Path(..., gt=0),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if id_user != current_token.id_user:
        raise not_authorized_exception

    user_credits = get_credits(db, current_token.type_user, current_token.id_type)
    credits_response = ListCreditsDisplay(
        credits=user_credits
    )

    if secure:
        secure_response = cipher_response_message(db=db, id_user=id_user, response=credits_response)
        return secure_response

    return credits_response
