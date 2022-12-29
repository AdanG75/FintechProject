from typing import Union

from fastapi import APIRouter, Query, Depends, Path, Request, HTTPException
from redis.client import Redis
from sqlalchemy.orm import Session
from starlette import status
from starlette.background import BackgroundTasks
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from controller.login_controller import get_current_token
from controller.outstanding_controller import get_outstanding_payments, get_non_zero_outstanding_payments, \
    save_id_outstanding_in_cache, start_cash_closing_from_controller, cancel_cash_closing_from_controller, \
    delete_id_outstanding_from_cache, get_id_outstanding_from_cache, finish_cash_closing_from_controller
from controller.paypal_controller import generate_paypal_order_from_outstanding, capture_paypal_order_from_outstanding
from controller.secure_controller import cipher_response_message
from controller.user_controller import get_email_based_on_id_type
from core.app_email import send_outstanding_payment_email
from db.cache.cache import get_cache_client
from db.database import get_db
from db.orm.exceptions_orm import not_authorized_exception, cache_exception
from schemas.outstanding_base import ListOPDisplay, OutstandingPaymentDisplay
from schemas.paypal_base import CreatePaypalOrderResponse, CreatePaypalOrderMinimalResponse
from schemas.secure_base import SecureBase
from schemas.token_base import TokenSummary
from schemas.type_user import TypeUser


router = APIRouter(
    tags=['outstanding payment']
)


templates = Jinja2Templates(directory="templates")


@router.get(
    path='/outstanding-payment',
    response_model=Union[SecureBase, ListOPDisplay],
    status_code=status.HTTP_200_OK
)
async def get_all_outstanding_payments(
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if current_token.type_user != TypeUser.system.value:
        raise not_authorized_exception

    response = get_outstanding_payments(db)

    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.get(
    path='/outstanding-payment/non-zero',
    response_model=Union[SecureBase, ListOPDisplay],
    status_code=status.HTTP_200_OK
)
async def get_non_zero_outstanding_payment(
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if current_token.type_user != TypeUser.system.value:
        raise not_authorized_exception

    response = get_non_zero_outstanding_payments(db)

    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.patch(
    path='/outstanding-payment/{id_outstanding}/cash-closing/start',
    response_model=Union[SecureBase, CreatePaypalOrderResponse, CreatePaypalOrderMinimalResponse],
    status_code=status.HTTP_200_OK
)
async def start_cash_closing_of_outstanding_payment(
        id_outstanding: int = Path(..., gt=0),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    if current_token.type_user != TypeUser.system.value:
        raise not_authorized_exception

    paypal_order = await generate_paypal_order_from_outstanding(db, id_outstanding)
    result = save_id_outstanding_in_cache(r, paypal_order.id, id_outstanding)

    if await result:
        start_cash_closing_from_controller(db, id_outstanding)
    else:
        raise cache_exception

    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=paypal_order)
        return secure_response

    return paypal_order


@router.delete(
    path='/outstanding-payment/{id_outstanding}/cash-closing/cancel',
    response_model=Union[SecureBase, OutstandingPaymentDisplay],
    status_code=status.HTTP_200_OK
)
async def cancel_cash_closing_of_outstanding_payment(
        id_outstanding: int = Path(..., gt=0),
        secure: bool = Query(True),
        paypal_id_order: str = Query(None),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    if current_token.type_user != TypeUser.system.value:
        raise not_authorized_exception

    response = cancel_cash_closing_from_controller(db, id_outstanding)

    if paypal_id_order is not None:
        await delete_id_outstanding_from_cache(r, paypal_id_order)

    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.get(
    path='/outstanding-payment/successful-outstanding',
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse
)
async def successful_outstanding(
        request: Request,
        bt: BackgroundTasks,
        token: str = Query(None, min_length=8, max_length=25),
        PayerID: str = Query(None, min_length=6, max_length=19),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client)
):
    PayerID = ' ' if PayerID is None else PayerID
    if token is not None:
        id_outstanding = await get_id_outstanding_from_cache(r, paypal_order=token)
        try:
            response, paypal_net_amount = await capture_paypal_order_from_outstanding(db, id_outstanding, token)
            outstanding = finish_cash_closing_from_controller(db, id_outstanding)
        except HTTPException:
            return templates.TemplateResponse(
                "error_outstanding_payment.html",
                {"request": request}
            )

        email_market = get_email_based_on_id_type(db, outstanding.id_market, str(TypeUser.market.value))
        cash_closing_str = outstanding.last_cash_closing.strftime(r"%Y-%m-%dT%H:%M:%S.%f")
        bt.add_task(
            send_outstanding_payment_email,
            email_user=await email_market,
            paypal_order=token,
            deposit_amount=response.total.value,
            net_amount=paypal_net_amount,
            currency=response.total.currency_code,
            cash_closing=cash_closing_str
        )
        bt.add_task(
            delete_id_outstanding_from_cache,
            r=r,
            paypal_order=token
        )

        return templates.TemplateResponse(
            "successful_outstanding_payment.html",
            {
                "request": request,
                "order": token,
                "payer_id": PayerID,
                "deposit_amount": response.total.value,
                "currency": response.total.currency_code,
                "net_amount": paypal_net_amount,
                "cash_closing": cash_closing_str
            }
        )

    else:
        return templates.TemplateResponse(
            "error_outstanding_payment.html",
            {"request": request}
        )


@router.get(
    path='/outstanding-payment/cancel-outstanding',
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse
)
async def cancel_outstanding(
        request: Request,
        bt: BackgroundTasks,
        token: str = Query(None, min_length=8, max_length=25),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client)
):
    if token is not None:
        id_outstanding = await get_id_outstanding_from_cache(r, paypal_order=token)
        try:
            outstanding = cancel_cash_closing_from_controller(db, id_outstanding)
        except HTTPException:
            return templates.TemplateResponse(
                "error_outstanding_payment.html",
                {"request": request}
            )

        bt.add_task(
            delete_id_outstanding_from_cache,
            r=r,
            paypal_order=token
        )

        return templates.TemplateResponse(
            "cancel_outstanding_payment.html",
            {
                "request": request,
                "order": token,
                "id_outstanding": id_outstanding,
                "amount": outstanding.amount
            }
        )

    else:
        return templates.TemplateResponse(
            "error_outstanding_payment.html",
            {"request": request}
        )
