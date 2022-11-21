from typing import Union

from fastapi import APIRouter, Query
from starlette import status

from core.paypal_service import create_paypal_access_token, create_paypal_order, create_order_object, \
    capture_paypal_order, parse_paypal_capture_to_base_response, parse_paypal_order_to_base_response, \
    MEXICAN_CURRENCY, get_paypal_amounts
from schemas.basic_response import BasicResponse
from schemas.paypal_base import ItemInner, UnitAmountInner, CreatePaypalOrderResponse, CapturePaypalOrderResponse, \
    CreatePaypalOrderMinimalResponse

router = APIRouter(
    prefix='/test/paypal',
    tags=['tests', 'paypal']
)


money_pattern = r'^\d{1,12}(\.\d{1,2})?$'


@router.post(
    path='/order',
    response_model=Union[CreatePaypalOrderResponse, CreatePaypalOrderMinimalResponse, BasicResponse],
    status_code=status.HTTP_201_CREATED
)
async def create_order(
        paypal_id_client: str = Query(..., min_length=5, max_length=90),
        paypal_secret: str = Query(..., min_length=8, max_length=90),
        amount: str = Query('0.00', regex=money_pattern),
        name: str = Query('Movement', min_length=1, max_length=79),
        description: str = Query('A simple transaction', min_length=2, max_length=499),
        quantity: int = Query(1, gt=0)
):
    paypal_client = await create_paypal_access_token(paypal_id_client, paypal_secret)
    paypal_item = ItemInner(
        name=name,
        description=description,
        quantity=str(quantity),
        unit_amount=UnitAmountInner(currency_code=MEXICAN_CURRENCY, value=amount)
    )
    request = await create_order_object(items=[paypal_item])
    order_response = await create_paypal_order(paypal_client, request)
    response = await parse_paypal_order_to_base_response(order_response)

    return response


@router.post(
    path='/order/capture',
    response_model=Union[BasicResponse, CapturePaypalOrderResponse],
    status_code=status.HTTP_201_CREATED
)
async def capture_order(
        paypal_id_client: str = Query(..., min_length=5, max_length=90),
        paypal_secret: str = Query(..., min_length=8, max_length=90),
        id_order: str = Query(None, min_length=8, max_length=25)
):
    paypal_client = await create_paypal_access_token(paypal_id_client, paypal_secret)

    if id_order is None:
        return BasicResponse(
            operation="Capture PayPal order",
            successful=False
        )

    capture_response = await capture_paypal_order(paypal_client, id_order)
    response = await parse_paypal_capture_to_base_response(capture_response)
    amounts = get_paypal_amounts(capture_response)
    print(f'paypal fee: ${amounts.paypal_fee.value} ({amounts.paypal_fee.currency_code})')
    print(f'Net amount: ${amounts.net_amount.value} ({amounts.net_amount.currency_code})')

    return response
