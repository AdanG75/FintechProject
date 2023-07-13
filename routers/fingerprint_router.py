from typing import Union

from fastapi import APIRouter, Path, Query, Depends
from sqlalchemy.orm import Session
from starlette import status

from controller.fingerprint_controller import check_if_user_have_fingerprint_registered
from controller.login_controller import get_current_token
from controller.secure_controller import cipher_response_message
from db.database import get_db
from db.orm.exceptions_orm import not_authorized_exception
from schemas.basic_response import BasicResponse
from schemas.secure_base import SecureBase
from schemas.token_base import TokenSummary

router = APIRouter(
    tags=['fingerprint']
)


@router.get(
    path='/fingerprint/{id_user}/have',
    response_model=Union[SecureBase, BasicResponse],
    status_code=status.HTTP_200_OK
)
async def have_user_had_a_fingerprint_registered(
        id_user: int = Path(..., gt=0),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if id_user != current_token.id_user:
        raise not_authorized_exception

    result = check_if_user_have_fingerprint_registered(db, current_token.type_user, current_token.id_type)
    response = BasicResponse(
        operation='User have a fingerprint registered',
        successful=result
    )

    if secure:
        secure_response = cipher_response_message(db=db, id_user=id_user, response=response)
        return secure_response

    return response
