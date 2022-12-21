from typing import Union, Tuple

from redis.client import Redis
from sqlalchemy.orm import Session

from controller.credit_controller import check_funds_of_credit
from controller.general_controller import save_type_auth_movement_cache, save_finish_movement_cache
from core.utils import money_str_to_float
from db.models.credits_db import DbCredit
from db.models.markets_db import DbMarket
from db.models.movements_db import DbMovement
from db.models.payments_db import DbPayment
from db.orm.credits_orm import get_credit_by_id_credit, do_amount_movement, start_credit_in_process, \
    finish_credit_in_process
from db.orm.exceptions_orm import type_of_value_not_compatible, not_authorized_exception, type_of_user_not_compatible, \
    minimum_amount_exception, not_sufficient_funds_exception, unexpected_error_exception
from db.orm.markets_orm import get_market_by_id_market
from db.orm.movements_orm import make_movement, authorized_movement, finish_movement
from db.orm.outstanding_payments_orm import add_amount, get_outstanding_payment_by_id_market
from db.orm.payments_orm import create_payment, get_payment_by_id_movement, put_paypal_id_order
from schemas.movement_base import UserDataMovement, MovementTypeRequest, MovementRequest
from schemas.movement_complex import MovementExtraRequest, ExtraMovementRequest, BasicExtraMovement, ExtraMovement
from schemas.payment_base import PaymentRequest
from schemas.type_auth_movement import TypeAuthMovement
from schemas.type_credit import TypeCredit
from schemas.type_money import TypeMoney
from schemas.type_movement import TypeMovement, NatureMovement
from schemas.type_user import TypeUser

MINIMUM_PAYPAL_AMOUNT: int = 5


async def create_payment_formatted(
        db: Session,
        request: MovementTypeRequest,
        data_user: UserDataMovement
) -> MovementExtraRequest:
    result, sub_movement = await check_valid_payment(db, request, data_user)
    if not result:
        raise unexpected_error_exception

    if data_user.type_user == TypeUser.client:
        data_user.id_requester = data_user.id_type_performer

    return MovementExtraRequest(
        id_credit=request.id_credit,
        id_performer=data_user.id_performer,
        id_requester=data_user.id_requester,
        type_movement=request.type_movement,
        amount=request.amount,
        type_user=data_user.type_user,
        extra=ExtraMovementRequest(
            type_submov=str(sub_movement.value),
            destination_credit=None,
            id_market=request.id_market,
            depositor_name=None,
            depositor_email=None,
            paypal_order=None
        )
    )


async def create_payment_movement(
        db: Session,
        request: MovementExtraRequest,
        data_user: UserDataMovement
) -> BasicExtraMovement:
    result, sub_movement = await check_valid_payment(db, request, data_user)
    if not result:
        raise unexpected_error_exception

    request.extra.type_submov = str(sub_movement.value)

    if data_user.type_user == TypeUser.client:
        request.id_requester = data_user.id_type_performer

    movement_request, payment_request = get_movement_and_payment_request_from_movement_extra_request(request)
    movement_db, payment_db = make_payment_movement(db, movement_request, payment_request)
    movement_response = create_extra_movement_response_from_db_models(movement_db, payment_db)

    return movement_response


async def check_valid_payment(
        db: Session,
        request: Union[MovementTypeRequest, MovementExtraRequest],
        data_user: UserDataMovement
) -> Tuple[bool, TypeMoney]:

    if isinstance(request, MovementTypeRequest):
        sub_movement = request.type_submov
        id_market = request.id_market

    elif isinstance(request, MovementExtraRequest):
        if data_user.id_performer != request.id_performer:
            raise not_authorized_exception

        sub_movement = TypeMoney(request.extra.type_submov)
        id_market = request.extra.id_market

    else:
        raise type_of_value_not_compatible

    market = get_market(db, id_market)
    if sub_movement == TypeMoney.paypal:
        validate_paypal_payment(request, data_user)
    else:
        credit = get_credit(db, request.id_credit)
        validate_credit_payment(db, market, credit, request, data_user)
        sub_movement = TypeMoney(credit.type_credit)

    return True, sub_movement


def get_market(db: Session, id_market: str) -> DbMarket:
    return get_market_by_id_market(db, id_market)


def get_credit(db: Session, id_credit: int) -> DbCredit:
    return get_credit_by_id_credit(db, id_credit)


def validate_paypal_payment(
        request: Union[MovementTypeRequest, MovementExtraRequest],
        data_user: UserDataMovement
) -> bool:
    if data_user.type_user != TypeUser.client:
        raise type_of_user_not_compatible

    amount = money_str_to_float(request.amount) if isinstance(request.amount, str) else request.amount
    if amount < MINIMUM_PAYPAL_AMOUNT:
        raise minimum_amount_exception

    return True


def validate_credit_payment(
        db: Session,
        market: DbMarket,
        credit: DbCredit,
        request: Union[MovementTypeRequest, MovementExtraRequest],
        data_user: UserDataMovement
) -> bool:
    if credit.id_client != data_user.id_requester:
        raise not_authorized_exception

    if not check_funds_of_credit(db, credit_obj=credit, amount=request.amount):
        raise not_sufficient_funds_exception

    if credit.type_credit == TypeCredit.local.value:
        if data_user.type_user == TypeUser.market or data_user.type_user == TypeUser.system:
            if credit.id_market != data_user.id_type_performer or data_user.id_type_performer != market.id_market:
                raise not_authorized_exception

        elif data_user.type_user == TypeUser.client:
            if credit.id_market != market.id_market or credit.id_client != data_user.id_type_performer:
                raise not_authorized_exception

        else:
            raise type_of_user_not_compatible

    elif credit.type_credit == TypeCredit.globalC.value:
        if data_user.type_user == TypeUser.market or data_user.type_user == TypeUser.system:
            if data_user.id_type_performer != market.id_market:
                raise not_authorized_exception

        elif data_user.type_user == TypeUser.client:
            if credit.id_client != data_user.id_type_performer:
                raise not_authorized_exception

        else:
            raise type_of_user_not_compatible

    else:
        raise type_of_value_not_compatible

    return True


def get_movement_and_payment_request_from_movement_extra_request(
        movement_extra: MovementExtraRequest
) -> Tuple[MovementRequest, PaymentRequest]:
    movement_request = MovementRequest(
        id_credit=movement_extra.id_credit,
        id_performer=movement_extra.id_performer,
        id_requester=movement_extra.id_requester,
        type_movement=movement_extra.type_movement,
        amount=movement_extra.amount,
        type_user=movement_extra.type_user
    )

    payment_request = PaymentRequest(
        id_movement=1,
        id_market=movement_extra.extra.id_market,
        type_payment=movement_extra.extra.type_submov,
        paypal_id_order=movement_extra.extra.paypal_order
    )

    return movement_request, payment_request


def make_payment_movement(
        db: Session,
        movement_request: MovementRequest,
        payment_request: PaymentRequest
) -> Tuple[DbMovement, DbPayment]:
    try:
        # Save movement
        movement_db = make_movement(db, movement_request, execute='wait')
        nested = db.begin_nested()
        db.refresh(movement_db)

        # Save Payment
        payment_request.id_movement = movement_db.id_movement
        payment_db = create_payment(db, payment_request, execute='wait')
        nested.commit()

        # Save all register
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    return movement_db, payment_db


async def execute_payment(db: Session, movement: DbMovement, r: Redis, from_paypal: bool) -> BasicExtraMovement:
    if from_paypal:
        movement_db = execute_movement_using_paypal(db, movement, r)
    else:
        movement_db = execute_payment_using_credit(db, movement, r)

    # Return a BasicExtraMovement object
    payment = get_payment_by_id_movement(db, movement.id_movement)

    return create_extra_movement_response_from_db_models(await movement_db, payment)


async def execute_payment_using_credit(db: Session, movement: DbMovement, r: Redis) -> DbMovement:
    amount_float = money_str_to_float(movement.amount) if isinstance(movement.amount, str) else movement.amount

    credit_db = get_credit_by_id_credit(db, movement.id_credit)
    if not check_funds_of_credit(db, credit_obj=credit_db, amount=amount_float):
        raise not_sufficient_funds_exception

    current_credit = money_str_to_float(credit_db.amount) if isinstance(credit_db.amount, str) else credit_db.amount
    new_amount = current_credit - amount_float

    # Check again funds to be sure about the successful realization of the transaction
    try:
        movement = authorized_movement(db, movement_object=movement, execute='wait')
        db.refresh(credit_db)
        if not check_funds_of_credit(db, credit_obj=credit_db, amount=amount_float):
            raise not_sufficient_funds_exception

        credit = do_amount_movement(db, new_amount, credit_object=credit_db, execute='wait')
        credit = start_credit_in_process(db, credit_object=credit, execute='wait')
        db.commit()
    except Exception as e:
        db.rollback()
        finish_credit_in_process(db, credit_object=credit_db, execute='wait')
        finish_movement(db, was_successful=False, movement_object=movement, execute='wait')
        db.commit()
        await save_finish_movement_cache(r, movement.id_movement)
        raise e

    db.refresh(credit)
    db.refresh(movement)

    # if we arrive here it's because all process was OK, so we can finnish the movement
    try:
        finish_credit_in_process(db, credit_object=credit, execute='wait')
        movement = finish_movement(db, was_successful=True, movement_object=movement, execute='wait')

        if credit.type_credit == TypeCredit.globalC.value:
            payment_db = get_payment_by_id_movement(db, movement.id_movement)
            outstanding_payment = get_outstanding_payment_by_id_market(db, payment_db.id_market)
            add_amount(db, amount=amount_float, outstanding_payment=outstanding_payment, execute='wait')

        db.commit()
    except Exception as e:
        db.rollback()
        finish_credit_in_process(db, credit_object=credit_db, execute='wait')
        finish_movement(db, was_successful=False, movement_object=movement, execute='wait')
        db.commit()
        raise e
    finally:
        await save_finish_movement_cache(r, movement.id_movement)

    return movement


async def execute_movement_using_paypal(db: Session, movement: DbMovement, r: Redis) -> DbMovement:
    try:
        movement = authorized_movement(db, movement_object=movement, execute='wait')
        db.commit()
    except Exception as e:
        db.rollback()
        finish_movement(db, was_successful=False, movement_object=movement, execute='wait')
        db.commit()
        await save_finish_movement_cache(r, movement.id_movement)
        raise e

    db.refresh(movement)

    try:
        movement = finish_movement(db, was_successful=True, movement_object=movement, execute='wait')
        db.commit()
    except Exception as e:
        db.rollback()
        finish_movement(db, was_successful=False, movement_object=movement, execute='wait')
        db.commit()
        raise e
    finally:
        await save_finish_movement_cache(r, movement.id_movement)

    return movement


def save_paypal_id_order_into_payment(db: Session, id_movement: int, paypal_id_order: str) -> bool:
    payment = put_paypal_id_order(db, paypal_id_order, id_movement=id_movement)

    return payment.paypal_id_order is not None


async def save_type_auth_payment_in_cache(
        r: Redis,
        id_movement: int,
        type_money: TypeMoney,
        performer_data: UserDataMovement
) -> bool:
    if type_money == TypeMoney.paypal and performer_data.type_user == TypeUser.client:
        return await save_type_auth_movement_cache(r, id_movement, str(TypeAuthMovement.paypal.value), 3600)
    elif type_money == TypeMoney.local or type_money == TypeMoney.globalC:
        if performer_data.type_user != TypeUser.admin:
            return await save_type_auth_movement_cache(r, id_movement, str(TypeAuthMovement.local.value), 3600)
        else:
            return False
    else:
        return False


def get_type_of_required_authorization_to_payment(db: Session, movement: DbMovement) -> TypeAuthMovement:
    if movement.type_movement == TypeMovement.payment.value:
        payment_db = get_payment_by_id_movement(db, movement.id_movement)
        p_type = payment_db.type_payment

        if p_type == TypeMoney.paypal.value:
            return TypeAuthMovement.paypal
        elif p_type == TypeMoney.local.value or p_type == TypeMoney.globalC.value:
            return TypeAuthMovement.local
        else:
            raise type_of_value_not_compatible

    else:
        raise type_of_value_not_compatible


def create_extra_movement_response_from_db_models(
        movement_db: DbMovement,
        payment_db: DbPayment
) -> BasicExtraMovement:
    return BasicExtraMovement(
        id_credit=movement_db.id_credit,
        id_performer=movement_db.id_performer,
        id_requester=movement_db.id_requester,
        type_movement=TypeMovement(movement_db.type_movement),
        amount=movement_db.amount,
        id_movement=movement_db.id_movement,
        authorized=movement_db.authorized,
        in_process=movement_db.in_process,
        successful=movement_db.successful,
        created_time=movement_db.created_time,
        extra=ExtraMovement(
            type_submov=payment_db.type_payment,
            destination_credit=None,
            id_market=payment_db.id_market,
            depositor_name=None,
            paypal_order=payment_db.paypal_id_order,
            id_detail=payment_db.id_payment,
            movement_nature=str(NatureMovement.outgoings.value)
        )
    )
