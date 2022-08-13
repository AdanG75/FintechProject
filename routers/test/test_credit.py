from typing import Optional, List

from fastapi import APIRouter, Body, Path, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from core.utils import money_str_to_float
from db.database import get_db
from db.orm import credits_orm
from schemas.basic_response import BasicResponse
from schemas.credit_base import CreditDisplay, CreditRequest
from schemas.type_user import TypeUser

router = APIRouter(
    prefix='/test/credit',
    tags=['tests', 'credit']
)


@router.post(
    path='/',
    response_model=CreditDisplay,
    status_code=status.HTTP_201_CREATED
)
async def create_credit(
        request: CreditRequest = Body(...),
        type_performer: Optional[TypeUser] = Query(None),
        db: Session = Depends(get_db)
):
    if type_performer is not None:
        response = credits_orm.create_credit(db, request, type_performer.value)
    else:
        response = credits_orm.create_credit(db, request, 'client')

    return response


@router.get(
    path='/{id_credit}',
    response_model=CreditDisplay,
    status_code=status.HTTP_200_OK
)
async def get_credit(
        id_credit: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = credits_orm.get_credit_by_id_credit(db, id_credit)

    return response


@router.put(
    path='/{id_credit}',
    response_model=CreditDisplay,
    status_code=status.HTTP_200_OK
)
async def update_credit(
        id_credit: int = Path(..., gt=0),
        request: CreditRequest = Body(...),
        db: Session = Depends(get_db)
):
    response = credits_orm.update_credit(db, id_credit, request)

    return response


@router.patch(
    path='/{id_credit}',
    response_model=CreditDisplay,
    status_code=status.HTTP_200_OK
)
async def approve_credit(
        id_credit: int = Path(..., gt=0),
        id_market: Optional[str] = Query(None, min_length=12, max_length=40),
        db: Session = Depends(get_db)
):
    credit = credits_orm.get_credit_by_id_credit(db, id_credit)
    if id_market is None:
        return credit

    if credit.id_market == id_market:
        response = credits_orm.approve_credit(db, id_credit)
        return response
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Only the market that provides the credit can approve it'
        )


@router.delete(
    path='/{id_credit}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_credit(
        id_credit: int = Path(..., gt=0),
        type_performer: Optional[TypeUser] = Query(None),
        db: Session = Depends(get_db)
):
    if type_performer is None:
        response = credits_orm.delete_credit(db=db, id_credit=id_credit, type_performer='market')
    else:
        response = credits_orm.delete_credit(db=db, id_credit=id_credit, type_performer=type_performer.value)

    return response


@router.patch(
    path='/start/{id_credit}',
    response_model=CreditDisplay,
    status_code=status.HTTP_200_OK
)
async def start_credit_movement(
        id_credit: int = Path(..., gt=0),
        amount: Optional[float] = Query(0, ge=0),
        db: Session = Depends(get_db)
):
    credit = credits_orm.start_credit_in_process(db, id_credit, execute='wait')
    if money_str_to_float(str(credit.amount)) < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Insufficient funds'
        )
    else:
        new_amount = money_str_to_float(str(credit.amount)) - amount

    response = credits_orm.do_amount_movement(db, id_credit, new_amount)

    return response


@router.patch(
    path='/cancel/{id_credit}',
    response_model=CreditDisplay,
    status_code=status.HTTP_200_OK
)
async def cancel_credit_movement(
        id_credit: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = credits_orm.cancel_amount_movement(db, id_credit)

    return response


@router.patch(
    path='/finish/{id_credit}',
    response_model=CreditDisplay,
    status_code=status.HTTP_200_OK
)
async def finish_credit_movement(
        id_credit: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    response = credits_orm.finish_credit_in_process(db, id_credit)

    return response


@router.patch(
    path='/{id_credit}/account/{id_account}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def change_account_of_credit(
        id_credit: int = Path(..., gt=0),
        id_account: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    result = credits_orm.change_account_of_credit(db=db, id_credit=id_credit, id_account=id_account)

    return BasicResponse(
        operation="Account change",
        successful=result
    )


@router.get(
    path='/client/{id_client}',
    response_model=List[CreditDisplay],
    status_code=status.HTTP_200_OK
)
async def get_credits_of_client(
        id_client: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db)
):
    response = credits_orm.get_credits_by_id_client(db, id_client)

    return response


@router.get(
    path='/market/{id_market}',
    response_model=List[CreditDisplay],
    status_code=status.HTTP_200_OK
)
async def get_credits_of_market(
        id_market: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db)
):
    response = credits_orm.get_credits_by_id_market(db, id_market)

    return response


@router.delete(
    path='/client/{id_client}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_credits_of_user(
        id_client: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db)
):
    response = credits_orm.delete_credits_by_id_client(db, id_client)

    return response


@router.delete(
    path='/market/{id_market}',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def delete_credits_of_market(
        id_market: str = Path(..., min_length=12, max_length=40),
        db: Session = Depends(get_db)
):
    response = credits_orm.delete_credits_by_id_market(db, id_market)

    return response
