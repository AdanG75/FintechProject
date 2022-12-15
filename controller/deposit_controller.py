from typing import Union, Tuple, Optional

from redis.client import Redis
from sqlalchemy.orm import Session

from controller.credit_controller import get_credit_using_its_id
from controller.general_controller import save_type_auth_movement_cache, get_paypal_money_cache, \
    save_finish_movement_cache, delete_paypal_money_cache
from controller.paypal_controller import calculate_net_amount_based_on_movement_amount
from controller.user_controller import get_name_of_client, get_email_of_user
from core.utils import money_str_to_float
from db.models.credits_db import DbCredit
from db.models.deposits_db import DbDeposit
from db.models.movements_db import DbMovement
from db.orm.credits_orm import get_credit_by_id_credit, do_amount_movement, start_credit_in_process, \
    finish_credit_in_process
from db.orm.deposits_orm import create_deposit, get_deposit_by_id_movement, put_paypal_id_order
from db.orm.exceptions_orm import type_of_user_not_compatible, not_authorized_exception, not_values_sent_exception, \
    type_of_value_not_compatible, unexpected_error_exception, minimum_amount_exception
from db.orm.movements_orm import make_movement, authorized_movement, finish_movement
from schemas.deposit_base import DepositRequest
from schemas.movement_base import MovementTypeRequest, UserDataMovement, MovementRequest
from schemas.movement_complex import BasicExtraMovement, ExtraMovement, MovementExtraRequest, ExtraMovementRequest
from schemas.type_auth_movement import TypeAuthMovement
from schemas.type_money import TypeMoney
from schemas.type_movement import TypeMovement, NatureMovement
from schemas.type_user import TypeUser


MINIMUM_AMOUNT: int = 5


async def create_deposit_formatted(
        db: Session,
        request: MovementTypeRequest,
        data_user: UserDataMovement
) -> MovementExtraRequest:
    if not await check_valid_deposit(db, request, data_user):
        raise unexpected_error_exception

    if data_user.type_user == TypeUser.client:
        data_user.id_requester = data_user.id_type_performer

    return MovementExtraRequest(
        id_credit=None,
        id_performer=data_user.id_performer,
        id_requester=data_user.id_requester,
        type_movement=request.type_movement,
        amount=request.amount,
        type_user=data_user.type_user,
        extra=ExtraMovementRequest(
            type_submov=str(request.type_submov.value),
            destination_credit=request.destination_credit,
            id_market=None,
            depositor_name=request.depositor_name,
            depositor_email=request.depositor_email,
            paypal_order=None
        )
    )


async def create_deposit_movement(
        db: Session,
        request: MovementExtraRequest,
        data_user: UserDataMovement
) -> BasicExtraMovement:
    if not await check_valid_deposit(db, request, data_user):
        raise unexpected_error_exception

    movement_request, deposit_request = get_movement_and_deposit_request_from_movement_extra_request(request)
    movement_db, deposit_db = make_deposit_movement(db, movement_request, deposit_request)
    movement_response = create_extra_movement_response_from_db_models(movement_db, deposit_db)

    return movement_response


def make_deposit_movement(
        db: Session,
        movement_request: MovementRequest,
        deposit_request: DepositRequest
) -> Tuple[DbMovement, DbDeposit]:
    try:
        # Save movement
        movement_db = make_movement(db, movement_request, execute='wait')
        nested = db.begin_nested()
        db.refresh(movement_db)

        # Save deposit
        deposit_request.id_movement = movement_db.id_movement
        deposit_db = create_deposit(db, deposit_request, execute='wait')
        nested.commit()

        # Save all register
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    return movement_db, deposit_db


async def save_type_auth_deposit_in_cache(
        r: Redis,
        id_movement: int,
        type_money: TypeMoney,
        performer_data: UserDataMovement
) -> bool:
    if type_money == TypeMoney.paypal and performer_data.type_user == TypeUser.client:
        return await save_type_auth_movement_cache(r, id_movement, str(TypeAuthMovement.paypal.value), 3600)
    elif type_money == TypeMoney.cash:
        if performer_data.type_user == TypeUser.market or performer_data.type_user == TypeUser.system:
            return await save_type_auth_movement_cache(r, id_movement, str(TypeAuthMovement.without.value), 3600)
        else:
            return False
    else:
        return False


def get_type_of_required_authorization_to_deposit(db: Session, movement: DbMovement) -> TypeAuthMovement:
    if movement.type_movement == TypeMovement.deposit.value:
        deposit_db = get_deposit_by_id_movement(db, movement.id_movement)
        if deposit_db.type_deposit == TypeMoney.cash.value:
            return TypeAuthMovement.without
        elif deposit_db.type_deposit == TypeMoney.paypal.value:
            return TypeAuthMovement.paypal
        else:
            raise type_of_value_not_compatible
    else:
        raise type_of_value_not_compatible


def save_paypal_id_order_into_deposit(db: Session, id_movement: int, paypal_id_order: str) -> bool:
    deposit = put_paypal_id_order(db, paypal_id_order, id_movement=id_movement)

    return deposit.paypal_id_order is not None


async def execute_deposit(db: Session, movement: DbMovement, r: Redis, from_paypal: bool) -> BasicExtraMovement:
    if from_paypal:
        amount = await get_paypal_money_cache(r, movement.id_movement)
    else:
        amount = money_str_to_float(movement.amount) if isinstance(movement.amount, str) else movement.amount

    # Amount can be None if money saved in cache was deleted. In that case we need to calculate the net amount
    if amount is None:
        amount = calculate_net_amount_based_on_movement_amount(movement.amount)

    deposit_db = get_deposit_by_id_movement(db, movement.id_movement)
    credit_db = get_credit_by_id_credit(db, deposit_db.id_destination_credit)
    current_credit = money_str_to_float(credit_db.amount) if isinstance(credit_db.amount, str) else credit_db.amount
    new_amount = current_credit + amount

    try:
        movement = authorized_movement(db, movement_object=movement, execute='wait')
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

    # if we arrive here it's because all process was OK, so we can finnish the movement
    try:
        finish_credit_in_process(db, credit_object=credit, execute='wait')
        movement = finish_movement(db, was_successful=True, movement_object=movement, execute='wait')
        db.commit()
    except Exception as e:
        db.rollback()
        finish_credit_in_process(db, credit_object=credit_db, execute='wait')
        finish_movement(db, was_successful=False, movement_object=movement, execute='wait')
        db.commit()
        raise e
    finally:
        await save_finish_movement_cache(r, movement.id_movement)
        await delete_paypal_money_cache(r, movement.id_movement)

    return create_extra_movement_response_from_db_models(movement, deposit_db)


def get_movement_and_deposit_request_from_movement_extra_request(
        movement_extra: MovementExtraRequest
) -> Tuple[MovementRequest, DepositRequest]:
    movement_request = MovementRequest(
        id_credit=movement_extra.id_credit,
        id_performer=movement_extra.id_performer,
        id_requester=movement_extra.id_requester,
        type_movement=movement_extra.type_movement,
        amount=movement_extra.amount,
        type_user=movement_extra.type_user
    )

    deposit_request = DepositRequest(
        id_movement=1,
        id_destination_credit=movement_extra.extra.destination_credit,
        depositor_name=movement_extra.extra.depositor_name,
        depositor_email=movement_extra.extra.depositor_email,
        type_deposit=movement_extra.extra.type_submov,
        paypal_id_order=movement_extra.extra.paypal_order
    )

    return movement_request, deposit_request


async def check_valid_deposit(
        db: Session,
        request: Union[MovementTypeRequest, MovementExtraRequest],
        data_user: UserDataMovement
) -> bool:
    amount = money_str_to_float(request.amount) if isinstance(request.amount, str) else request.amount
    if amount < MINIMUM_AMOUNT:
        raise minimum_amount_exception

    if isinstance(request, MovementTypeRequest):
        credit = check_destination_credit(db, request.destination_credit)

        request.depositor_name, request.depositor_email = await validate_depositor_email_and_name(
            db=db,
            type_submov=request.type_submov,
            depositor_name=request.depositor_name,
            depositor_email=request.depositor_email,
            data_user=data_user
        )

    elif isinstance(request, MovementExtraRequest):
        if data_user.id_performer != request.id_performer:
            raise not_authorized_exception

        credit = check_destination_credit(db, request.extra.destination_credit)

        request.extra.depositor_name, request.extra.depositor_email = await validate_depositor_email_and_name(
            db=db,
            type_submov=TypeMoney(request.extra.type_submov),
            depositor_name=request.extra.depositor_name,
            depositor_email=request.extra.depositor_email,
            data_user=data_user
        )

    else:
        raise type_of_value_not_compatible

    if not can_performer_deposit_to_destination_credit(credit, data_user):
        raise not_authorized_exception

    return True


def check_destination_credit(db: Session, id_credit: int) -> DbCredit:
    return get_credit_using_its_id(db, id_credit)


async def validate_depositor_email_and_name(
        db: Session,
        type_submov: TypeMoney,
        depositor_name: Optional[str],
        depositor_email: Optional[str],
        data_user: UserDataMovement
) -> Tuple[str, str]:
    if type_submov == TypeMoney.paypal:
        if data_user.type_user != TypeUser.client:
            raise type_of_user_not_compatible

        depositor_name = await get_name_of_client(db, data_user.id_type_performer)
        depositor_email = await get_email_of_user(db, data_user.id_performer)

        return depositor_name, depositor_email

    elif type_submov == TypeMoney.cash:
        if not (data_user.type_user == TypeUser.market or data_user.type_user == TypeUser.system):
            raise type_of_user_not_compatible

        if depositor_email is None or depositor_name is None:
            raise not_values_sent_exception

        return depositor_name, depositor_email

    else:
        raise type_of_value_not_compatible


def can_performer_deposit_to_destination_credit(credit: DbCredit, data_user: UserDataMovement) -> bool:
    if data_user.type_user == TypeUser.market or data_user.type_user == TypeUser.system:
        if credit.id_market == data_user.id_type_performer:
            return True
        else:
            return False
    elif data_user.type_user == TypeUser.client:
        return True
    else:
        return False


def create_extra_movement_response_from_db_models(
        movement_db: DbMovement,
        deposit_db: DbDeposit
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
            type_submov=deposit_db.type_deposit,
            destination_credit=deposit_db.id_destination_credit,
            id_market=None,
            depositor_name=deposit_db.depositor_name,
            paypal_order=deposit_db.paypal_id_order,
            id_detail=deposit_db.id_deposit,
            movement_nature=str(NatureMovement.income.value)
        )
    )
