from typing import Union, Tuple

from redis.client import Redis
from sqlalchemy.orm import Session

from controller.credit_controller import check_funds_of_credit, check_owners_of_credit
from controller.general_controller import save_type_auth_movement_cache, save_finish_movement_cache
from core.utils import money_str_to_float
from db.models.movements_db import DbMovement
from db.models.withdraws_db import DbWithdraw
from db.orm.credits_orm import get_credit_by_id_credit, do_amount_movement, start_credit_in_process, \
    finish_credit_in_process
from db.orm.exceptions_orm import not_sufficient_funds_exception, not_authorized_exception, not_values_sent_exception, \
    unexpected_error_exception, type_of_value_not_compatible
from db.orm.movements_orm import make_movement, authorized_movement, finish_movement
from db.orm.withdraws_orm import create_withdraw, get_withdraw_by_id_movement
from schemas.movement_base import UserDataMovement, MovementTypeRequest, MovementRequest
from schemas.movement_complex import ExtraMovementRequest, MovementExtraRequest, ExtraMovement, BasicExtraMovement
from schemas.type_auth_movement import TypeAuthMovement
from schemas.type_money import TypeMoney
from schemas.type_movement import TypeMovement, NatureMovement
from schemas.type_user import TypeUser
from schemas.withdraw_base import WithdrawRequest


async def create_withdraw_formatted(
        db: Session,
        request: MovementTypeRequest,
        data_user: UserDataMovement
) -> MovementExtraRequest:
    if not check_valid_withdraw(db, request, data_user):
        raise unexpected_error_exception

    return MovementExtraRequest(
        id_credit=request.id_credit,
        id_performer=data_user.id_performer,
        id_requester=data_user.id_requester,
        type_movement=request.type_movement,
        amount=request.amount,
        type_user=data_user.type_user,
        extra=ExtraMovementRequest(
            type_submov=str(request.type_submov.value),
            destination_credit=None,
            id_market=None,
            depositor_name=None,
            depositor_email=None,
            paypal_order=None
        )
    )


async def create_withdraw_movement(
        db: Session,
        request: MovementExtraRequest,
        data_user: UserDataMovement
) -> BasicExtraMovement:
    if not check_valid_withdraw(db, request, data_user):
        raise unexpected_error_exception

    movement_request, withdraw_request = get_movement_and_withdraw_request_from_movement_extra_request(request)
    movement_db, withdraw_db = make_withdraw_movement(db, movement_request, withdraw_request)
    movement_response = create_extra_movement_response_from_db_models(movement_db, withdraw_db)

    return movement_response


def check_valid_withdraw(
        db: Session,
        request: Union[MovementTypeRequest, MovementExtraRequest],
        data_user: UserDataMovement
) -> bool:
    if request.id_credit is None:
        raise not_values_sent_exception

    if not (data_user.type_user == TypeUser.market or data_user.type_user == TypeUser.system):
        raise not_authorized_exception

    # This transaction only can be done by a user of type market or system, for that reason el id_market correspond to
    # user_data.id_type_performer
    if not check_owners_of_credit(db, request.id_credit, data_user.id_requester, data_user.id_type_performer):
        raise not_authorized_exception

    if isinstance(request, MovementExtraRequest):
        if request.id_performer != data_user.id_performer:
            raise not_authorized_exception

    if not check_funds_of_credit(db, id_credit=request.id_credit, amount=request.amount):
        raise not_sufficient_funds_exception

    return True


async def save_type_auth_withdraw_in_cache(
        r: Redis,
        id_movement: int,
        type_money: TypeMoney,
        performer_data: UserDataMovement
) -> bool:
    if type_money == TypeMoney.cash and performer_data.type_user == TypeUser.market:
        return await save_type_auth_movement_cache(r, id_movement, str(TypeAuthMovement.local.value), 3600)
    else:
        raise type_of_value_not_compatible


def get_movement_and_withdraw_request_from_movement_extra_request(
        movement_extra: MovementExtraRequest
) -> Tuple[MovementRequest, WithdrawRequest]:
    movement_request = MovementRequest(
        id_credit=movement_extra.id_credit,
        id_performer=movement_extra.id_performer,
        id_requester=movement_extra.id_requester,
        type_movement=movement_extra.type_movement,
        amount=movement_extra.amount,
        type_user=movement_extra.type_user
    )

    withdraw_request = WithdrawRequest(
        id_movement=1,
        type_withdraw=movement_extra.extra.type_submov
    )

    return movement_request, withdraw_request


def make_withdraw_movement(
        db: Session,
        movement_request: MovementRequest,
        withdraw_request: WithdrawRequest
) -> Tuple[DbMovement, DbWithdraw]:
    try:
        # Save movement
        movement_db = make_movement(db, movement_request, execute='wait')
        nested = db.begin_nested()
        db.refresh(movement_db)

        # Save withdraw
        withdraw_request.id_movement = movement_db.id_movement
        withdraw_db = create_withdraw(db, withdraw_request, execute='wait')
        nested.commit()

        # Save all register
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    return movement_db, withdraw_db


async def execute_withdraw(db: Session, movement: DbMovement, r: Redis) -> BasicExtraMovement:
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
        db.commit()
    except Exception as e:
        db.rollback()
        finish_credit_in_process(db, credit_object=credit_db, execute='wait')
        finish_movement(db, was_successful=False, movement_object=movement, execute='wait')
        db.commit()
        raise e
    finally:
        await save_finish_movement_cache(r, movement.id_movement)

    # Return a BasicExtraMovement object
    withdraw = get_withdraw_by_id_movement(db, movement.id_movement)

    return create_extra_movement_response_from_db_models(movement, withdraw)


def get_type_of_required_authorization_to_withdraw(movement: DbMovement) -> TypeAuthMovement:
    if movement.type_movement == TypeMovement.withdraw.value:
        return TypeAuthMovement.local

    raise type_of_value_not_compatible


def create_extra_movement_response_from_db_models(
        movement_db: DbMovement,
        withdraw_db: DbWithdraw
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
            type_submov=withdraw_db.type_withdraw,
            destination_credit=None,
            id_market=None,
            depositor_name=None,
            paypal_order=None,
            id_detail=withdraw_db.id_withdraw,
            movement_nature=str(NatureMovement.outgoings.value)
        )
    )
