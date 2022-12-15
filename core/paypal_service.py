from typing import List, Union

from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from paypalhttp import HttpError, HttpResponse
from starlette import status

from core.config import ON_CLOUD
from core.logs import write_data_log, LogSeverity
from db.orm.exceptions_orm import not_same_currency_exception, paypal_error_exception, first_approve_order_exception, \
    type_of_value_not_compatible
from schemas.paypal_base import ItemInner, PaypalComplexOrderRequest, AmountInner, UnitAmountInner, ItemTotalInner, \
    PurchaseUnitInner, UrlInner, CapturePaypalOrderResponse, PayerInner, CaptureInner, LinkInner, \
    CreatePaypalOrderResponse, PayeeInner, CreatePaypalOrderMinimalResponse, RealPaypalAmounts

PAYPAL_CAPTURE_ORDER: str = 'CAPTURE'
PAYPAL_RETURN: str = 'return=representation'
PAYPAL_FULL_RESPONSE: bool = True
MEXICAN_CURRENCY: str = 'MXN'


async def create_paypal_access_token(paypal_client_id: str, paypal_client_secret: str) -> PayPalHttpClient:
    # Creating an environment
    environment = SandboxEnvironment(client_id=paypal_client_id, client_secret=paypal_client_secret)
    client = PayPalHttpClient(environment)

    return client


async def create_paypal_order(
        paypal_client: PayPalHttpClient,
        order_request: PaypalComplexOrderRequest
) -> HttpResponse:

    request = OrdersCreateRequest()
    if PAYPAL_FULL_RESPONSE:
        request.prefer(PAYPAL_RETURN)

    request.request_body(order_request.dict())

    try:
        response = paypal_client.execute(request)
        if response.status_code == status.HTTP_201_CREATED:
            return response

    except IOError as ioe:
        if isinstance(ioe, HttpError):
            msg_error = f'{ioe.status_code}-{ioe.message}'
            if ON_CLOUD:
                write_data_log(msg_error, str(LogSeverity.ALERT.value))
            else:
                print(msg_error)

        raise paypal_error_exception

    return response


async def capture_paypal_order(paypal_client: PayPalHttpClient, id_order: str) -> HttpResponse:
    request = OrdersCaptureRequest(id_order)
    if PAYPAL_FULL_RESPONSE:
        request.prefer(PAYPAL_RETURN)

    try:
        # Return the minimal capture response
        response = paypal_client.execute(request)
        if response.status_code == status.HTTP_201_CREATED:
            return response

    except IOError as ioe:
        if isinstance(ioe, HttpError):
            if ioe.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
                raise first_approve_order_exception

            msg_error = f'{ioe.status_code}-{ioe.message}'
            if ON_CLOUD:
                write_data_log(msg_error, str(LogSeverity.ALERT.value))
            else:
                print(msg_error)

        raise paypal_error_exception

    return response


async def create_order_object(items: List[ItemInner]) -> PaypalComplexOrderRequest:
    base_currency: str = ''
    total: float = 0.0

    for item in items:
        total = total + (int(item.quantity) * float(item.unit_amount.value))

        if base_currency == '':
            base_currency = item.unit_amount.currency_code
        else:
            if base_currency != item.unit_amount.currency_code:
                raise not_same_currency_exception

    # Build PayPal order request
    amount_unit = UnitAmountInner(
        currency_code=base_currency,
        value=str(total)
    )
    item_total = ItemTotalInner(
        item_total=amount_unit
    )
    amount = AmountInner(
        currency_code=base_currency,
        value=str(total),
        breakdown=item_total
    )
    unit_purchase = PurchaseUnitInner(
        items=items,
        amount=amount
    )

    base_url = get_paypal_base_url()
    paypal_context = UrlInner(
        return_url=base_url + 'successful-transaction',
        cancel_url=base_url + 'cancel-transaction'
    )
    order_request = PaypalComplexOrderRequest(
        intent=PAYPAL_CAPTURE_ORDER,
        purchase_units=[unit_purchase],
        application_context=paypal_context
    )

    return order_request


def get_paypal_base_url():
    if ON_CLOUD:
        base_url = 'https://www.fintech75.app/'
    else:
        base_url = 'http://127.0.0.1:8000/'

    return base_url


async def parse_paypal_order_to_base_response(
        order_response: HttpResponse
) -> Union[CreatePaypalOrderResponse, CreatePaypalOrderMinimalResponse]:
    if PAYPAL_FULL_RESPONSE:
        return parse_full_order_response_to_base_model_response(order_response)
    else:
        return parse_minimal_order_response_to_base_model_response(order_response)


async def parse_paypal_capture_to_base_response(
        capture_response: HttpResponse
) -> CapturePaypalOrderResponse:
    if PAYPAL_FULL_RESPONSE:
        return parse_full_capture_response_to_base_model_response(capture_response)
    else:
        return parse_minimal_capture_response_to_base_model_response(capture_response)


def parse_full_order_response_to_base_model_response(order_response: HttpResponse) -> CreatePaypalOrderResponse:
    response = CreatePaypalOrderResponse(
        id=order_response.result.id,
        intent=order_response.result.intent,
        status=order_response.result.status,
        total=UnitAmountInner(
            currency_code=order_response.result.purchase_units[0].amount.currency_code,
            value=order_response.result.purchase_units[0].amount.value
        ),
        payee=PayeeInner(
            email_address=order_response.result.purchase_units[0].payee.email_address,
            merchant_id=order_response.result.purchase_units[0].payee.merchant_id
        ),
        create_time=order_response.result.create_time,
        approve_link=LinkInner(
            href=order_response.result.links[1].href,
            rel=order_response.result.links[1].rel,
            method=order_response.result.links[1].method
        ),
        capture_link=LinkInner(
            href=order_response.result.links[3].href,
            rel=order_response.result.links[3].rel,
            method=order_response.result.links[3].method
        )
    )

    return response


def parse_minimal_order_response_to_base_model_response(
        order_response: HttpResponse
) -> CreatePaypalOrderMinimalResponse:
    response = CreatePaypalOrderMinimalResponse(
        id=order_response.result.id,
        status=order_response.result.status,
        approve_link=LinkInner(
            href=order_response.result.links[1].href,
            rel=order_response.result.links[1].rel,
            method=order_response.result.links[1].method
        ),
        capture_link=LinkInner(
            href=order_response.result.links[3].href,
            rel=order_response.result.links[3].rel,
            method=order_response.result.links[3].method
        )
    )

    return response


def parse_full_capture_response_to_base_model_response(capture_response: HttpResponse) -> CapturePaypalOrderResponse:
    response = CapturePaypalOrderResponse(
        id=capture_response.result.id,
        intent=capture_response.result.intent,
        status=capture_response.result.status,
        create_time=capture_response.result.create_time,
        total=UnitAmountInner(
            currency_code=capture_response.result.purchase_units[0].amount.currency_code,
            value=capture_response.result.purchase_units[0].amount.value
        ),
        payer=PayerInner(
            payer_id=capture_response.result.payer.payer_id,
            name=capture_response.result.payer.name.given_name,
            surname=capture_response.result.payer.name.surname,
            email_address=capture_response.result.payer.email_address
        ),

        capture=CaptureInner(
            id=capture_response.result.purchase_units[0].payments.captures[0].id,
            status=capture_response.result.purchase_units[0].payments.captures[0].status,
            amount=UnitAmountInner(
                currency_code=capture_response.result.purchase_units[0].payments.captures[0].amount.currency_code,
                value=capture_response.result.purchase_units[0].payments.captures[0].amount.value
            ),
            final_capture=capture_response.result.purchase_units[0].payments.captures[0].final_capture
        ),
        refund_link=LinkInner(
            href=capture_response.result.purchase_units[0].payments.captures[0].links[1].href,
            rel=capture_response.result.purchase_units[0].payments.captures[0].links[1].rel,
            method=capture_response.result.purchase_units[0].payments.captures[0].links[1].method
        )
    )

    return response


def parse_minimal_capture_response_to_base_model_response(capture_response: HttpResponse) -> CapturePaypalOrderResponse:
    response = CapturePaypalOrderResponse(
        id=capture_response.result.id,
        intent=PAYPAL_CAPTURE_ORDER,
        status=capture_response.result.status,
        create_time=capture_response.result.purchase_units[0].payments.captures[0].create_time,
        total=UnitAmountInner(
            currency_code=capture_response.result.purchase_units[0].payments.captures[0].amount.currency_code,
            value=capture_response.result.purchase_units[0].payments.captures[0].amount.value
        ),
        payer=PayerInner(
            payer_id=capture_response.result.payer.payer_id,
            name=capture_response.result.payer.name.given_name,
            surname=capture_response.result.payer.name.surname,
            email_address=capture_response.result.payer.email_address
        ),

        capture=CaptureInner(
            id=capture_response.result.purchase_units[0].payments.captures[0].id,
            status=capture_response.result.purchase_units[0].payments.captures[0].status,
            amount=UnitAmountInner(
                currency_code=capture_response.result.purchase_units[0].payments.captures[0].amount.currency_code,
                value=capture_response.result.purchase_units[0].payments.captures[0].amount.value
            ),
            final_capture=capture_response.result.purchase_units[0].payments.captures[0].final_capture
        ),
        refund_link=LinkInner(
            href=capture_response.result.purchase_units[0].payments.captures[0].links[1].href,
            rel=capture_response.result.purchase_units[0].payments.captures[0].links[1].rel,
            method=capture_response.result.purchase_units[0].payments.captures[0].links[1].method
        )
    )

    return response


def get_paypal_amounts(capture_response: HttpResponse) -> RealPaypalAmounts:
    if not PAYPAL_FULL_RESPONSE:
        raise type_of_value_not_compatible

    base_object = capture_response.result.purchase_units[0].payments.captures[0].seller_receivable_breakdown
    return RealPaypalAmounts(
        gross_amount=UnitAmountInner(
            currency_code=base_object.gross_amount.currency_code,
            value=base_object.gross_amount.value
        ),
        paypal_fee=UnitAmountInner(
            currency_code=base_object.paypal_fee.currency_code,
            value=base_object.paypal_fee.value
        ),
        net_amount=UnitAmountInner(
            currency_code=base_object.net_amount.currency_code,
            value=base_object.net_amount.value
        )
    )
