from typing import Union, Tuple

from redis.client import Redis
from sqlalchemy.orm import Session

from controller.credit_controller import check_funds_of_credit
from controller.general_controller import save_type_auth_movement_cache, save_finish_movement_cache, \
    get_paypal_money_cache
from controller.paypal_controller import MINIMUM_PAYPAL_AMOUNT, calculate_net_amount_based_on_movement_amount
from core.config import settings
from core.utils import money_str_to_float
from db.models.credits_db import DbCredit
from db.models.movements_db import DbMovement
from db.models.transfers_db import DbTransfer
from db.orm.credits_orm import get_credit_by_id_credit, do_amount_movement, start_credit_in_process, \
    finish_credit_in_process
from db.orm.exceptions_orm import type_of_value_not_compatible, not_authorized_exception, type_of_user_not_compatible, \
    not_sufficient_funds_exception, minimum_amount_exception, system_credit_exception, unexpected_error_exception, \
    circular_transaction_exception, not_implemented_exception, type_of_movement_not_compatible_exception, \
    option_not_found_exception
from db.orm.movements_orm import make_movement, authorized_movement, finish_movement
from db.orm.outstanding_payments_orm import get_outstanding_payment_by_id_market, add_amount
from db.orm.transfers_orm import get_type_of_transfer, create_transfer, get_transfer_by_id_movement, put_paypal_id_order
from schemas.movement_base import MovementTypeRequest, UserDataMovement, MovementRequest
from schemas.movement_complex import MovementExtraRequest, ExtraMovementRequest, BasicExtraMovement, ExtraMovement
from schemas.transfer_base import TransferRequest
from schemas.type_auth_movement import TypeAuthMovement
from schemas.type_credit import TypeCredit
from schemas.type_movement import NatureMovement, TypeMovement
from schemas.type_transfer import TypeTransfer
from schemas.type_user import TypeUser


async def create_transfer_formatted(
        db: Session,
        request: MovementTypeRequest,
        data_user: UserDataMovement
) -> MovementExtraRequest:
    result, type_transfer = await check_valid_transfer(db, request, data_user)
    if not result:
        raise unexpected_error_exception

    return MovementExtraRequest(
        id_credit=request.id_credit,
        id_performer=data_user.id_performer,
        id_requester=data_user.id_requester,
        type_movement=request.type_movement,
        amount=request.amount,
        type_user=data_user.type_user,
        extra=ExtraMovementRequest(
            type_submov=str(type_transfer.value),
            destination_credit=request.destination_credit,
            id_market=None,
            depositor_name=None,
            depositor_email=None,
            paypal_order=None
        )
    )


async def create_transfer_movement(
        db: Session,
        request: MovementExtraRequest,
        data_user: UserDataMovement
) -> BasicExtraMovement:
    result, type_transfer = await check_valid_transfer(db, request, data_user)
    if not result:
        raise unexpected_error_exception

    request.extra.type_submov = str(type_transfer.value)

    movement_request, transfer_request = get_movement_and_transfer_request_from_movement_extra_request(request)
    movement_db, transfer_db = make_transfer_movement(db, movement_request, transfer_request)
    movement_response = create_extra_movement_response_from_db_models(movement_db, transfer_db)

    return movement_response


async def check_valid_transfer(
        db: Session,
        request: Union[MovementTypeRequest, MovementExtraRequest],
        data_user: UserDataMovement
) -> Tuple[bool, TypeTransfer]:
    id_origin_c = request.id_credit

    if isinstance(request, MovementTypeRequest):
        id_destination_c = request.destination_credit

    elif isinstance(request, MovementExtraRequest):
        if data_user.id_performer != request.id_performer:
            raise not_authorized_exception

        if data_user.id_requester != request.id_requester:
            raise not_authorized_exception

        id_destination_c = request.extra.destination_credit

    else:
        raise type_of_value_not_compatible

    if id_origin_c == id_destination_c:
        raise circular_transaction_exception

    type_transfer = get_type_of_transfer(
        db=db,
        id_origin_credit=id_origin_c,
        id_destination_credit=id_destination_c
    )
    origin_credit = get_credit_by_id_credit(db, id_origin_c)
    destination_credit = get_credit_by_id_credit(db, id_destination_c)

    if type_transfer == TypeTransfer.local_to_local:
        result = validate_local_to_local(db, request.amount, origin_credit, destination_credit, data_user)
    elif type_transfer == TypeTransfer.local_to_global:
        result = validate_local_to_global(db, request.amount, origin_credit, destination_credit, data_user)
    elif type_transfer == TypeTransfer.global_to_local:
        result = validate_global_to_local(db, request.amount, origin_credit, destination_credit, data_user)
    elif type_transfer == TypeTransfer.global_to_global:
        result = validate_global_to_global(db, request.amount, origin_credit, destination_credit, data_user)
    else:
        raise type_of_value_not_compatible

    return result, type_transfer


def validate_local_to_local(
        db: Session,
        amount: Union[str, float],
        origin_credit: DbCredit,
        destination_credit: DbCredit,
        data_user: UserDataMovement
) -> bool:
    if data_user.type_user != TypeUser.market:
        raise type_of_user_not_compatible

    if origin_credit.id_client != data_user.id_requester:
        raise not_authorized_exception

    id_market = data_user.id_type_performer
    if origin_credit.id_market != id_market or destination_credit.id_market != id_market:
        raise not_authorized_exception

    if not check_funds_of_credit(db, credit_obj=origin_credit, amount=amount):
        raise not_sufficient_funds_exception

    return True


def validate_local_to_global(
        db: Session,
        amount: Union[str, float],
        origin_credit: DbCredit,
        destination_credit: DbCredit,
        data_user: UserDataMovement
) -> bool:
    if data_user.type_user != TypeUser.market:
        raise type_of_user_not_compatible

    if origin_credit.id_client != data_user.id_requester:
        raise not_authorized_exception

    if origin_credit.id_market != data_user.id_type_performer:
        raise not_authorized_exception

    if destination_credit.id_market != settings.get_market_system():
        raise system_credit_exception

    amount = money_str_to_float(amount) if isinstance(amount, str) else amount
    if amount < MINIMUM_PAYPAL_AMOUNT:
        raise minimum_amount_exception

    if not check_funds_of_credit(db, credit_obj=origin_credit, amount=amount):
        raise not_sufficient_funds_exception

    return True


def validate_global_to_local(
        db: Session,
        amount: Union[str, float],
        origin_credit: DbCredit,
        destination_credit: DbCredit,
        data_user: UserDataMovement
) -> bool:
    if data_user.type_user != TypeUser.client:
        raise type_of_user_not_compatible

    oc_client = origin_credit.id_client
    if oc_client != data_user.id_requester or oc_client != data_user.id_type_performer:
        raise not_authorized_exception

    if origin_credit.id_market != settings.get_market_system():
        raise system_credit_exception

    if destination_credit.type_credit != TypeCredit.local.value:
        raise unexpected_error_exception

    amount = money_str_to_float(amount) if isinstance(amount, str) else amount
    if amount < MINIMUM_PAYPAL_AMOUNT:
        raise minimum_amount_exception

    if not check_funds_of_credit(db, credit_obj=origin_credit, amount=amount):
        raise not_sufficient_funds_exception

    return True


def validate_global_to_global(
        db: Session,
        amount: Union[str, float],
        origin_credit: DbCredit,
        destination_credit: DbCredit,
        data_user: UserDataMovement
) -> bool:
    if data_user.type_user != TypeUser.client:
        raise type_of_user_not_compatible

    oc_client = origin_credit.id_client
    if oc_client != data_user.id_requester or oc_client != data_user.id_type_performer:
        raise not_authorized_exception

    if origin_credit.id_market != settings.get_market_system():
        raise system_credit_exception

    if destination_credit.id_market != settings.get_market_system():
        raise system_credit_exception

    if not check_funds_of_credit(db, credit_obj=origin_credit, amount=amount):
        raise not_sufficient_funds_exception

    return True


def get_movement_and_transfer_request_from_movement_extra_request(
        movement_extra: MovementExtraRequest
) -> Tuple[MovementRequest, TransferRequest]:
    movement_request = MovementRequest(
        id_credit=movement_extra.id_credit,
        id_performer=movement_extra.id_performer,
        id_requester=movement_extra.id_requester,
        type_movement=movement_extra.type_movement,
        amount=movement_extra.amount,
        type_user=movement_extra.type_user
    )

    transfer_request = TransferRequest(
        id_movement=1,
        id_destination_credit=movement_extra.extra.destination_credit,
        type_transfer=movement_extra.extra.type_submov,
        paypal_id_order=movement_extra.extra.paypal_order
    )

    return movement_request, transfer_request


def make_transfer_movement(
        db: Session,
        movement_request: MovementRequest,
        transfer_request: TransferRequest
) -> Tuple[DbMovement, DbTransfer]:
    try:
        # Save movement
        movement_db = make_movement(db, movement_request, execute='wait')
        nested = db.begin_nested()
        db.refresh(movement_db)

        # Save transfer
        transfer_request.id_movement = movement_db.id_movement
        transfer_db = create_transfer(db, transfer_request, execute='wait')
        nested.commit()

        # Save all register
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    return movement_db, transfer_db


def create_extra_movement_response_from_db_models(
        movement_db: DbMovement,
        transfer_db: DbTransfer
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
            type_submov=transfer_db.type_transfer,
            destination_credit=transfer_db.id_destination_credit,
            id_market=None,
            depositor_name=None,
            paypal_order=transfer_db.paypal_id_order,
            id_detail=transfer_db.id_transfer,
            movement_nature=str(NatureMovement.outgoings.value)
        )
    )


async def save_type_auth_transfer_in_cache(
        r: Redis,
        id_movement: int,
        type_transfer: TypeTransfer,
        performer_data: UserDataMovement
) -> bool:
    is_market = performer_data.type_user == TypeUser.market or performer_data.type_user == TypeUser.system

    if type_transfer == TypeTransfer.local_to_local and is_market:
        return await save_type_auth_movement_cache(r, id_movement, str(TypeAuthMovement.local.value), 3600)
    elif type_transfer == TypeTransfer.local_to_global and is_market:
        return await save_type_auth_movement_cache(r, id_movement, str(TypeAuthMovement.localPaypal.value), 3600)
    elif (type_transfer == TypeTransfer.global_to_local or type_transfer == TypeTransfer.global_to_global) and \
            performer_data.type_user == TypeUser.client:
        return await save_type_auth_movement_cache(r, id_movement, str(TypeAuthMovement.local.value), 3600)
    else:
        return False


def get_type_of_required_authorization_to_transfer(db: Session, movement: DbMovement) -> TypeAuthMovement:
    if movement.type_movement == TypeMovement.transfer.value:
        transfer_db = get_transfer_by_id_movement(db, movement.id_movement)
        t_type = transfer_db.type_transfer

        if t_type == TypeTransfer.local_to_global.value:
            return TypeAuthMovement.localPaypal
        elif t_type == TypeTransfer.local_to_local.value or t_type == TypeTransfer.global_to_local.value or \
                t_type == TypeTransfer.global_to_global.value:
            return TypeAuthMovement.local
        else:
            raise type_of_value_not_compatible

    else:
        raise type_of_value_not_compatible


def save_paypal_id_order_into_transfer(db: Session, id_movement: int, paypal_id_order: str) -> bool:
    transfer = put_paypal_id_order(db, paypal_id_order, id_movement=id_movement)

    return transfer.paypal_id_order is not None


async def execute_transfer(db: Session, movement: DbMovement, r: Redis, from_paypal: bool) -> BasicExtraMovement:
    transfer_db = get_transfer_by_id_movement(db, movement.id_movement)

    if transfer_db.type_transfer == TypeTransfer.local_to_local.value:
        movement_db = execute_transfer_local_to_local(db, movement, transfer_db, r, from_paypal)
    elif transfer_db.type_transfer == TypeTransfer.local_to_global.value:
        movement_db = execute_transfer_local_to_global(db, movement, transfer_db, r, from_paypal)
    elif transfer_db.type_transfer == TypeTransfer.global_to_local.value:
        movement_db = execute_transfer_global_to_local(db, movement, transfer_db, r, from_paypal)
    elif transfer_db.type_transfer == TypeTransfer.global_to_global.value:
        movement_db = execute_transfer_global_to_global(db, movement, transfer_db, r, from_paypal)
    else:
        raise option_not_found_exception

    return create_extra_movement_response_from_db_models(await movement_db, transfer_db)


async def execute_transfer_local_to_local(
        db: Session,
        movement: DbMovement,
        transfer: DbTransfer,
        r: Redis,
        from_paypal: bool
) -> DbMovement:
    if from_paypal:
        raise not_implemented_exception

    else:
        return await make_transfer_from_credit(db, movement, transfer, r, generate_outstanding=False, from_paypal=False)


async def execute_transfer_local_to_global(
        db: Session,
        movement: DbMovement,
        transfer: DbTransfer,
        r: Redis,
        from_paypal: bool
) -> DbMovement:
    if not from_paypal:
        raise type_of_movement_not_compatible_exception

    return await make_transfer_from_credit(
        db=db,
        movement=movement,
        transfer=transfer,
        r=r,
        generate_outstanding=False,
        from_paypal=from_paypal
    )


async def execute_transfer_global_to_local(
        db: Session,
        movement: DbMovement,
        transfer: DbTransfer,
        r: Redis,
        from_paypal: bool
) -> DbMovement:
    if from_paypal:
        raise type_of_movement_not_compatible_exception

    return await make_transfer_from_credit(
        db=db,
        movement=movement,
        transfer=transfer,
        r=r,
        generate_outstanding=True,
        from_paypal=from_paypal
    )


async def execute_transfer_global_to_global(
        db: Session,
        movement: DbMovement,
        transfer: DbTransfer,
        r: Redis,
        from_paypal: bool
) -> DbMovement:
    if from_paypal:
        raise type_of_movement_not_compatible_exception

    return await make_transfer_from_credit(
        db=db,
        movement=movement,
        transfer=transfer,
        r=r,
        generate_outstanding=False,
        from_paypal=from_paypal
    )


async def make_transfer_from_credit(
        db: Session,
        movement: DbMovement,
        transfer: DbTransfer,
        r: Redis,
        generate_outstanding: bool,
        from_paypal: bool
) -> DbMovement:
    amount_float = money_str_to_float(movement.amount) if isinstance(movement.amount, str) else movement.amount

    ori_credit_db = get_credit_by_id_credit(db, movement.id_credit)
    des_credit_db = get_credit_by_id_credit(db, transfer.id_destination_credit)

    if not check_funds_of_credit(db, credit_obj=ori_credit_db, amount=amount_float):
        raise not_sufficient_funds_exception

    ori_current_credit = money_str_to_float(ori_credit_db.amount) if isinstance(ori_credit_db.amount, str) \
        else ori_credit_db.amount
    des_current_credit = money_str_to_float(des_credit_db.amount) if isinstance(ori_credit_db.amount, str) \
        else des_credit_db.amount

    # Calculate new credits' amount
    ori_new_amount = ori_current_credit - amount_float
    if from_paypal:
        amount_paypal = await get_paypal_money_cache(r, movement.id_movement)
        if amount_paypal is None:
            amount_paypal = calculate_net_amount_based_on_movement_amount(movement.amount)

        des_new_amount = des_current_credit + amount_paypal
    else:
        des_new_amount = des_current_credit + amount_float

    try:
        movement = authorized_movement(db, movement_object=movement, execute='wait')

        # Check again funds to be sure about the successful realization of the transaction
        db.refresh(ori_credit_db)
        if not check_funds_of_credit(db, credit_obj=ori_credit_db, amount=amount_float):
            raise not_sufficient_funds_exception

        ori_credit = do_amount_movement(db, ori_new_amount, credit_object=ori_credit_db, execute='wait')
        ori_credit = start_credit_in_process(db, credit_object=ori_credit, execute='wait')

        des_credit = do_amount_movement(db, des_new_amount, credit_object=des_credit_db, execute='wait')
        des_credit = start_credit_in_process(db, credit_object=des_credit, execute='wait')

        db.commit()
    except Exception as e:
        db.rollback()
        finish_credit_in_process(db, credit_object=ori_credit_db, execute='wait')
        finish_credit_in_process(db, credit_object=des_credit_db, execute='wait')
        finish_movement(db, was_successful=False, movement_object=movement, execute='wait')
        db.commit()
        await save_finish_movement_cache(r, movement.id_movement)
        raise e

    db.refresh(ori_credit)
    db.refresh(des_credit)
    db.refresh(movement)

    # if we arrive here it's because all process was OK, so we can finnish the movement
    try:
        finish_credit_in_process(db, credit_object=ori_credit, execute='wait')
        finish_credit_in_process(db, credit_object=des_credit, execute='wait')
        movement = finish_movement(db, was_successful=True, movement_object=movement, execute='wait')

        if generate_outstanding:
            outstanding_payment = get_outstanding_payment_by_id_market(db, des_credit.id_market)
            add_amount(db, amount=amount_float, outstanding_payment=outstanding_payment, execute='wait')

        db.commit()
    except Exception as e:
        db.rollback()
        finish_credit_in_process(db, credit_object=ori_credit_db, execute='wait')
        finish_credit_in_process(db, credit_object=des_credit_db, execute='wait')
        finish_movement(db, was_successful=False, movement_object=movement, execute='wait')
        db.commit()
        raise e
    finally:
        await save_finish_movement_cache(r, movement.id_movement)

    return movement
