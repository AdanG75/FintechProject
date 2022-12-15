import json
from typing import Union, Tuple

from redis.client import Redis
from sqlalchemy.orm import Session

from controller.general_controller import save_paypal_order_cache, get_paypal_order_cache, delete_paypal_order_cache
from core.paypal_service import create_paypal_access_token, MEXICAN_CURRENCY, create_order_object, \
    create_paypal_order, parse_paypal_order_to_base_response
from core.utils import iter_object_to_become_serializable
from db.models.accounts_db import DbAccount
from db.models.credits_db import DbCredit
from db.models.deposits_db import DbDeposit
from db.models.movements_db import DbMovement
from db.models.payments_db import DbPayment
from db.models.transfers_db import DbTransfer
from db.orm.accounts_orm import get_account_by_id
from db.orm.credits_orm import get_credit_by_id_credit, get_main_id_account_of_market
from db.orm.deposits_orm import get_deposit_by_id_movement
from db.orm.exceptions_orm import type_of_movement_not_compatible_exception, type_of_value_not_compatible
from db.orm.movements_orm import get_movement_by_id_movement
from db.orm.payments_orm import get_payment_by_id_movement
from db.orm.transfers_orm import get_transfer_by_id_movement
from schemas.paypal_base import CreatePaypalOrderResponse, CreatePaypalOrderMinimalResponse, ItemInner, UnitAmountInner
from schemas.type_movement import TypeMovement
from secure.cipher_secure import cipher_data, decipher_data


BASE_QUANTITY = '1'


async def generate_paypal_order(
        db: Session,
        id_movement: int
) -> Union[CreatePaypalOrderResponse, CreatePaypalOrderMinimalResponse]:
    movement: DbMovement = get_movement_by_id_movement(db, id_movement)
    sub_type_movement = get_sub_type_object_of_movement(db, movement)
    paypal_id_client, paypal_secret = get_paypal_id_and_paypay_secret(db, sub_type_movement)

    paypal_client = create_paypal_access_token(paypal_id_client, paypal_secret)
    amount_order = get_amount_in_paypal_format(movement.amount)
    paypal_item = ItemInner(
        name='Transacción Monetaria',
        description=str(movement.type_movement).upper(),
        quantity=BASE_QUANTITY,
        unit_amount=UnitAmountInner(currency_code=MEXICAN_CURRENCY, value=amount_order)
    )

    request = await create_order_object(items=[paypal_item])
    order_response = await create_paypal_order(await paypal_client, request)
    response = parse_paypal_order_to_base_response(order_response)

    return await response


def get_sub_type_object_of_movement(
        db: Session,
        movement: DbMovement
) -> Union[DbDeposit, DbPayment, DbTransfer]:
    if movement.type_movement == TypeMovement.deposit.value:
        sub_type_movement = get_deposit_by_id_movement(db, movement.id_movement)
    elif movement.type_movement == TypeMovement.payment.value:
        sub_type_movement = get_payment_by_id_movement(db, movement.id_movement)
    elif movement.type_movement == TypeMovement.transfer.value:
        sub_type_movement = get_transfer_by_id_movement(db, movement.id_movement)
    else:
        raise type_of_movement_not_compatible_exception

    return sub_type_movement


def get_paypal_id_and_paypay_secret(
        db: Session,
        sub_movement: Union[DbDeposit, DbPayment, DbTransfer]
) -> Tuple[str, str]:
    if isinstance(sub_movement, DbDeposit):
        credit: DbCredit = get_credit_by_id_credit(db, sub_movement.id_destination_credit)
        account: DbAccount = get_account_by_id(db, credit.id_account)
    elif isinstance(sub_movement, DbPayment):
        id_account_market = get_main_id_account_of_market(db, sub_movement.id_market)
        account: DbAccount = get_account_by_id(db, id_account_market)
    elif isinstance(sub_movement, DbTransfer):
        credit: DbCredit = get_credit_by_id_credit(db, sub_movement.id_destination_credit)
        account: DbAccount = get_account_by_id(db, credit.id_account)
    else:
        raise type_of_value_not_compatible

    return decipher_data(account.paypal_id_client), decipher_data(account.paypal_secret)


def get_amount_in_paypal_format(amount: Union[int, float, str]) -> str:
    if isinstance(amount, str):
        return amount.replace('$', '').replace(',', '')

    if isinstance(amount, int) or isinstance(amount, float):
        return str(amount)

    raise type_of_value_not_compatible


async def save_paypal_order_in_cache(
        r: Redis,
        id_movement: int,
        paypal_order: Union[CreatePaypalOrderResponse, CreatePaypalOrderMinimalResponse]
) -> bool:
    order_dict = paypal_order.dict().copy()
    iter_object_to_become_serializable(order_dict)
    order_json = json.dumps(order_dict, indent=4, ensure_ascii=False)
    order_str = order_json.encode('utf-8')
    order_secure = cipher_data(order_str)

    return await save_paypal_order_cache(r, id_movement, order_secure)


async def get_paypal_order_object_from_cache(
        r: Redis,
        id_movement: int
) -> Union[CreatePaypalOrderResponse, CreatePaypalOrderMinimalResponse, None]:
    order_cache = await get_paypal_order_cache(r, id_movement)
    if order_cache is None:
        return None

    order_json = decipher_data(order_cache)
    order_dict = json.loads(order_json)

    try:
        # If key 'intent' exist means that response is the type CreatePaypalOrderResponse,
        # in other case will be the type CreatePaypalOrderMinimalResponse
        intent = order_dict['intent']
        return CreatePaypalOrderResponse.parse_obj(order_dict)
    except KeyError:
        return CreatePaypalOrderMinimalResponse.parse_obj(order_dict)


async def delete_paypal_order_in_cache(r: Redis, id_movement: int) -> bool:
    return await delete_paypal_order_cache(r, id_movement)
