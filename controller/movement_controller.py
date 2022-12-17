from datetime import datetime, timedelta
from typing import List, Union, Optional

from fastapi import HTTPException
from redis.client import Redis
from sqlalchemy.orm import Session

from controller.characteristic_point_controller import save_minutiae_and_core_points_secure_in_cache
from controller.deposit_controller import create_deposit_formatted, create_deposit_movement, \
    save_type_auth_deposit_in_cache, get_type_of_required_authorization_to_deposit, execute_deposit, \
    save_paypal_id_order_into_deposit
from controller.fingerprint_controller import get_minutiae_and_core_points_from_sample
from controller.general_controller import save_value_in_cache_with_formatted_name, AUTH_OK, delete_values_in_cache, \
    check_auth_movement_result, get_type_auth_movement_cache
from controller.payment_controller import create_payment_formatted, create_payment_movement, \
    save_type_auth_payment_in_cache, get_type_of_required_authorization_to_payment, execute_payment, \
    save_paypal_id_order_into_payment
from controller.secure_controller import cipher_minutiae_and_core_points
from controller.user_controller import get_email_based_on_id_type
from controller.withdraw_controller import create_withdraw_formatted, create_withdraw_movement, \
    save_type_auth_withdraw_in_cache, get_type_of_required_authorization_to_withdraw, execute_withdraw
from db.models.deposits_db import DbDeposit
from db.models.movements_db import DbMovement
from db.models.payments_db import DbPayment
from db.models.transfers_db import DbTransfer
from db.models.withdraws_db import DbWithdraw
from db.orm.deposits_orm import get_deposits_by_id_destination_credit, get_deposit_by_id_movement
from db.orm.exceptions_orm import NotFoundException, wrong_data_sent_exception, option_not_found_exception, \
    type_of_value_not_compatible, unexpected_error_exception, compile_exception, cache_exception, \
    operation_need_authorization_exception, not_values_sent_exception
from db.orm.movements_orm import get_movements_by_id_credit_and_type, get_movement_by_id_movement, \
    get_movements_by_id_requester_and_type, force_termination_movement
from db.orm.payments_orm import get_payment_by_id_movement, get_payments_by_id_market
from db.orm.transfers_orm import get_transfer_by_id_movement, get_transfers_by_id_destination_credit
from db.orm.withdraws_orm import get_withdraw_by_id_movement
from schemas.fingerprint_model import FingerprintB64
from schemas.movement_base import UserDataMovement, MovementTypeRequest
from schemas.movement_complex import BasicExtraMovement, ExtraMovement, MovementExtraRequest
from schemas.payment_base import PaymentComplexList
from schemas.type_auth_movement import TypeAuthFrom, TypeAuthMovement
from schemas.type_money import TypeMoney
from schemas.type_movement import TypeMovement, NatureMovement
from schemas.type_transfer import TypeTransfer
from schemas.type_user import TypeUser


async def get_movement_using_its_id(db: Session, id_movement: int) -> DbMovement:
    movement_db = get_movement_by_id_movement(db, id_movement)

    return movement_db


async def get_id_requester_from_movement(db: Session, id_movement: int) -> Optional[str]:
    movement_db = await get_movement_using_its_id(db, id_movement)

    return movement_db.id_requester


async def check_if_time_of_movement_is_valid(movement: DbMovement, minutes: int = 60) -> bool:
    if movement.created_time + timedelta(minutes=minutes) >= datetime.utcnow():
        return True
    else:
        return False


async def get_all_movements_of_credit(db: Session, id_credit: int) -> List[BasicExtraMovement]:
    deposits = await get_deposit_movements_of_credit(db, id_credit)
    payments = await get_payment_movements_of_credit(db, id_credit)
    transfers = await get_transfer_movements_of_credit(db, id_credit)
    withdraws = await get_withdraw_movements_of_credit(db, id_credit)

    return deposits + payments + transfers + withdraws


async def get_deposit_movements_of_credit(db: Session, id_credit: int) -> List[BasicExtraMovement]:
    try:
        deposits: List[DbDeposit] = get_deposits_by_id_destination_credit(db, id_credit)
    except NotFoundException:
        return []

    if len(deposits) > 0:
        movements = []
        for deposit in deposits:
            try:
                movement: DbMovement = get_movement_by_id_movement(db, deposit.id_movement)
            except NotFoundException:
                pass
            else:
                extra_information = parse_DbDeposit_to_ExtraMovement(deposit)
                extra_movement = parse_DbMovement_to_BasicExtraMovement(movement, extra_information)
                movements.append(extra_movement)

        return movements

    return deposits


async def get_payment_movements_of_credit(db: Session, id_credit: int) -> List[BasicExtraMovement]:
    movements: List[DbMovement] = get_movements_by_id_credit_and_type(
        db=db,
        id_credit=id_credit,
        type_movement=str(TypeMovement.payment.value)
    )

    if len(movements) > 0:
        extra_movements = []
        for movement in movements:
            try:
                payment: DbPayment = get_payment_by_id_movement(db, movement.id_movement)
            except NotFoundException:
                pass
            else:
                extra_information = parse_DbPayment_to_ExtraMovement(payment)
                extra_movement = parse_DbMovement_to_BasicExtraMovement(movement, extra_information)
                extra_movements.append(extra_movement)

        return extra_movements

    return movements


def get_payments_of_client(db: Session, id_client: str) -> PaymentComplexList:
    movements = get_movements_by_id_requester_and_type(db, id_client, str(TypeMovement.payment.value))

    if len(movements) > 0:
        extra_movements = []
        for movement in movements:
            try:
                payment: DbPayment = get_payment_by_id_movement(db, movement.id_movement)
            except NotFoundException:
                pass
            else:
                extra_information = parse_DbPayment_to_ExtraMovement(payment)
                extra_movement = parse_DbMovement_to_BasicExtraMovement(movement, extra_information)
                extra_movements.append(extra_movement)

    else:
        extra_movements = movements

    return PaymentComplexList(
        payments=extra_movements
    )


def get_payments_of_market(db: Session, id_market: str) -> PaymentComplexList:
    payments = get_payments_by_id_market(db, id_market)

    if len(payments) > 0:
        extra_movements = []
        for payment in payments:
            try:
                movement = get_movement_by_id_movement(db, payment.id_movement)
            except NotFoundException:
                pass
            else:
                extra_information = parse_DbPayment_to_ExtraMovement(payment, str(NatureMovement.income.value))
                extra_movement = parse_DbMovement_to_BasicExtraMovement(movement, extra_information)
                extra_movements.append(extra_movement)

    else:
        extra_movements = payments

    return PaymentComplexList(
        payments=extra_movements
    )


async def get_transfer_movements_of_credit(db: Session, id_credit: int) -> List[BasicExtraMovement]:
    income_transfers = await get_income_transfers_of_credit(db, id_credit)
    outgoings_transfers = await get_outgoings_transfers_of_credit(db, id_credit)

    return income_transfers + outgoings_transfers


async def get_income_transfers_of_credit(db: Session, id_credit: int) -> List[BasicExtraMovement]:
    try:
        transfers: List[DbTransfer] = get_transfers_by_id_destination_credit(db, id_credit)
    except NotFoundException:
        return []

    if len(transfers) > 0:
        extra_movements = []
        for transfer in transfers:
            try:
                movement: DbMovement = get_movement_by_id_movement(db, transfer.id_movement)
            except NotFoundException:
                pass
            else:
                extra_information = parse_DbTransfer_to_ExtraMovement(transfer, str(NatureMovement.income.value))
                extra_movement = parse_DbMovement_to_BasicExtraMovement(movement, extra_information)
                extra_movements.append(extra_movement)

        return extra_movements

    return transfers


async def get_outgoings_transfers_of_credit(db: Session, id_credit: int) -> List[BasicExtraMovement]:
    movements: List[DbMovement] = get_movements_by_id_credit_and_type(
        db=db,
        id_credit=id_credit,
        type_movement=str(TypeMovement.transfer.value)
    )

    if len(movements) > 0:
        extra_movements = []
        for movement in movements:
            try:
                transfer: DbTransfer = get_transfer_by_id_movement(db, movement.id_movement)
            except NotFoundException:
                pass
            else:
                extra_information = parse_DbTransfer_to_ExtraMovement(transfer, str(NatureMovement.outgoings.value))
                extra_movement = parse_DbMovement_to_BasicExtraMovement(movement, extra_information)
                extra_movements.append(extra_movement)

        return extra_movements

    return movements


async def get_withdraw_movements_of_credit(db: Session, id_credit: int) -> List[BasicExtraMovement]:
    movements: List[DbMovement] = get_movements_by_id_credit_and_type(
        db=db,
        id_credit=id_credit,
        type_movement=str(TypeMovement.withdraw.value)
    )

    if len(movements) > 0:
        extra_movements = []
        for movement in movements:
            try:
                withdraw: DbWithdraw = get_withdraw_by_id_movement(db, movement.id_movement)
            except NotFoundException:
                pass
            else:
                extra_information = parse_DbWithdraw_to_ExtraMovement(withdraw)
                extra_movement = parse_DbMovement_to_BasicExtraMovement(movement, extra_information)
                extra_movements.append(extra_movement)

        return extra_movements

    return movements


async def create_summary_of_movement(
        db: Session,
        request: MovementTypeRequest,
        user_data: UserDataMovement,
        type_movement: Union[str, TypeMovement]
) -> MovementExtraRequest:
    t_movement_obj = cast_str_to_movement_type(type_movement) if isinstance(type_movement, str) else type_movement

    if t_movement_obj == TypeMovement.deposit:
        if validate_deposit_data_types(request):
            summary = await create_deposit_formatted(db, request, user_data)
        else:
            raise unexpected_error_exception
    elif t_movement_obj == TypeMovement.payment:
        if validate_payment_data_types(request):
            summary = await create_payment_formatted(db, request, user_data)
        else:
            raise unexpected_error_exception
    elif t_movement_obj == TypeMovement.transfer:
        pass
    elif t_movement_obj == TypeMovement.withdraw:
        if validate_withdraw_data_types(request):
            summary = await create_withdraw_formatted(db, request, user_data)
        else:
            raise unexpected_error_exception
    else:
        raise option_not_found_exception

    return summary


async def make_movement_based_on_type(
        db: Session,
        request: MovementExtraRequest,
        data_user: UserDataMovement,
        type_movement: Union[str, TypeMovement]
) -> BasicExtraMovement:
    t_movement_obj = cast_str_to_movement_type(type_movement) if isinstance(type_movement, str) else type_movement

    if t_movement_obj == TypeMovement.deposit:
        if validate_deposit_data_types(request):
            movement = await create_deposit_movement(db, request, data_user)
        else:
            raise unexpected_error_exception
    elif t_movement_obj == TypeMovement.payment:
        if validate_payment_data_types(request):
            movement = await create_payment_movement(db, request, data_user)
        else:
            raise unexpected_error_exception
    elif t_movement_obj == TypeMovement.transfer:
        pass
    elif t_movement_obj == TypeMovement.withdraw:
        if validate_withdraw_data_types(request):
            movement = await create_withdraw_movement(db, request, data_user)
        else:
            raise unexpected_error_exception
    else:
        raise option_not_found_exception

    return movement


def validate_deposit_data_types(request: Union[MovementTypeRequest, MovementExtraRequest]) -> bool:
    request.id_credit = None

    if not check_type_of_movement(request.type_movement, TypeMovement.deposit):
        raise type_of_value_not_compatible

    if isinstance(request, MovementTypeRequest):
        if not (check_type_of_money(request.type_submov, TypeMoney.cash) or
                check_type_of_money(request.type_submov, TypeMoney.paypal)):
            raise type_of_value_not_compatible

        if request.destination_credit is None or request.depositor_name is None or request.depositor_email is None:
            raise not_values_sent_exception

    elif isinstance(request, MovementExtraRequest):
        if not (check_type_of_money(request.extra.type_submov, TypeMoney.cash) or
                check_type_of_money(request.extra.type_submov, TypeMoney.paypal)):
            raise type_of_value_not_compatible

        request.extra.paypal_order = None
        if (request.extra.destination_credit is None or request.extra.depositor_name is None or
                request.extra.depositor_email is None):
            raise not_values_sent_exception
    else:
        return False

    return True


def validate_payment_data_types(request: Union[MovementTypeRequest, MovementExtraRequest]) -> bool:
    if not check_type_of_movement(request.type_movement, TypeMovement.payment):
        raise type_of_value_not_compatible

    if isinstance(request, MovementTypeRequest):
        sub_movement = request.type_submov
        id_market = request.id_market
    elif isinstance(request, MovementExtraRequest):
        sub_movement = request.extra.type_submov
        id_market = request.extra.id_market
        request.extra.paypal_order = None
    else:
        return False

    if check_type_of_money(sub_movement, TypeMoney.credit) or check_type_of_money(sub_movement, TypeMoney.local) \
            or check_type_of_money(sub_movement, TypeMoney.globalC):
        if request.id_credit is None:
            raise not_values_sent_exception

    elif check_type_of_money(sub_movement, TypeMoney.paypal):
        request.id_credit = None

    elif check_type_of_money(sub_movement, TypeMoney.cash) or check_type_of_money(sub_movement, TypeMoney.card):
        raise type_of_value_not_compatible

    else:
        raise type_of_value_not_compatible

    if id_market is None:
        raise not_values_sent_exception

    return True


def validate_withdraw_data_types(request: Union[MovementTypeRequest, MovementExtraRequest]) -> bool:
    if not check_type_of_movement(request.type_movement, TypeMovement.withdraw):
        raise type_of_value_not_compatible

    if isinstance(request, MovementTypeRequest):
        if not check_type_of_money(request.type_submov, TypeMoney.cash):
            raise type_of_value_not_compatible

    elif isinstance(request, MovementExtraRequest):
        if not check_type_of_money(request.extra.type_submov, TypeMoney.cash):
            raise type_of_value_not_compatible
    else:
        return False

    return True


async def save_type_authentication_in_cache(
        r: Redis,
        id_movement: int,
        type_movement: Union[str, TypeMovement],
        type_sub_movement: Union[str, TypeMoney, TypeTransfer],
        performer_data: UserDataMovement
) -> bool:
    act_type_mov = cast_str_to_movement_type(type_movement) if isinstance(type_movement, str) else type_movement
    if act_type_mov == TypeMovement.transfer:
        act_ts_movement = cast_str_to_transfer_type(type_sub_movement) \
            if isinstance(type_sub_movement, str) else type_sub_movement
    else:
        act_ts_movement = cast_str_to_money_type(type_sub_movement) \
            if isinstance(type_sub_movement, str) else type_sub_movement

    if act_type_mov == TypeMovement.withdraw:
        result = await save_type_auth_withdraw_in_cache(r, id_movement, act_ts_movement, performer_data)

    elif act_type_mov == TypeMovement.deposit:
        result = await save_type_auth_deposit_in_cache(r, id_movement, act_ts_movement, performer_data)
        if result:
            deposit_type_auth = await get_type_auth_movement_cache(r, id_movement)
            if deposit_type_auth == TypeAuthMovement.without.value:
                saved = await save_authentication_movement_result_in_cache(r, id_movement, TypeAuthFrom.without)
                result = result and saved

    elif act_type_mov == TypeMovement.payment:
        result = await save_type_auth_payment_in_cache(r, id_movement, act_ts_movement, performer_data)

    elif act_type_mov == TypeMovement.transfer:
        # result = await save_type_auth_transfer_in_cache(r, id_movement, act_ts_movement, performer_data)
        pass
    else:
        raise option_not_found_exception

    return result


async def execute_movement_from_controller(db: Session, r: Redis, id_movement: int) -> BasicExtraMovement:
    movement_db: DbMovement = await get_movement_using_its_id(db, id_movement)

    if movement_db.type_movement == TypeMovement.deposit.value:
        type_auth = get_type_of_required_authorization_to_deposit(db, movement_db)
        if await is_movement_authorized(r, id_movement, type_auth):
            from_paypal = (type_auth == TypeAuthMovement.paypal)
            movement = execute_deposit(db, movement_db, r, from_paypal)
            await delete_authorized_data_based_on_type_auth(r, id_movement, type_auth)
        else:
            raise operation_need_authorization_exception

    elif movement_db.type_movement == TypeMovement.payment.value:
        type_auth = get_type_of_required_authorization_to_payment(db, movement_db)
        if await is_movement_authorized(r, id_movement, type_auth):
            from_paypal = (type_auth == TypeAuthMovement.paypal)
            movement = execute_payment(db, movement_db, r, from_paypal)
            await delete_authorized_data_based_on_type_auth(r, id_movement, type_auth)
        else:
            raise operation_need_authorization_exception

    elif movement_db.type_movement == TypeMovement.transfer.value:
        # execute_transfer
        pass
    elif movement_db.type_movement == TypeMovement.withdraw.value:
        type_auth = get_type_of_required_authorization_to_withdraw(movement_db)
        if await is_movement_authorized(r, id_movement, type_auth):
            movement = execute_withdraw(db, movement_db, r)
            await delete_authorized_data_based_on_type_auth(r, id_movement, type_auth)
        else:
            raise operation_need_authorization_exception

    else:
        raise option_not_found_exception

    return await movement


def save_paypal_order_into_sub_movement(db: Session, id_movement: int, paypal_order: str) -> bool:
    movement_db = get_movement_by_id_movement(db, id_movement)

    if movement_db.type_movement == TypeMovement.deposit.value:
        return save_paypal_id_order_into_deposit(db, id_movement, paypal_order)
    elif movement_db.type_movement == TypeMovement.payment.value:
        return save_paypal_id_order_into_payment(db, id_movement, paypal_order)
    elif movement_db.type_movement == TypeMovement.transfer.value:
        pass
    else:
        raise type_of_value_not_compatible


def check_type_of_movement(
        actual_type: Union[str, TypeMovement],
        wished_type: Union[str, TypeMovement]
) -> bool:
    act_type_obj = cast_str_to_movement_type(actual_type) if isinstance(actual_type, str) else actual_type
    whs_type_obj = cast_str_to_movement_type(wished_type) if isinstance(wished_type, str) else wished_type

    if act_type_obj == whs_type_obj:
        return True
    else:
        return False


def check_type_of_money(
        actual_money: Union[str, TypeMoney],
        wished_money: Union[str, TypeMoney]
) -> bool:
    act_money_obj = cast_str_to_money_type(actual_money) if isinstance(actual_money, str) else actual_money
    whs_money_obj = cast_str_to_money_type(wished_money) if isinstance(wished_money, str) else wished_money

    if act_money_obj == whs_money_obj:
        return True
    else:
        return False


def check_type_of_transfer(
        actual_transfer: Union[str, TypeTransfer],
        wished_transfer: Union[str, TypeTransfer]
) -> bool:
    act_transfer_obj = cast_str_to_transfer_type(actual_transfer) \
        if isinstance(actual_transfer, str) else actual_transfer
    whs_transfer_obj = cast_str_to_transfer_type(wished_transfer) \
        if isinstance(wished_transfer, str) else wished_transfer

    if act_transfer_obj == whs_transfer_obj:
        return True
    else:
        return False


async def save_movement_fingerprint(r: Redis, id_movement: int, fingerprint_object: FingerprintB64) -> bool:
    minutiae, c_points = await get_minutiae_and_core_points_from_sample(fingerprint_object.fingerprint)

    # Cipher minutiae and core points
    minutiae_secure, core_points_secure = await cipher_minutiae_and_core_points(minutiae, c_points)

    # Save cipher data into Redis
    save_minutiae_and_core_points_secure_in_cache(r, minutiae_secure, core_points_secure, id_movement, 'MOV')

    return True


async def is_movement_authorized(r: Redis, id_movement: int, type_auth: TypeAuthMovement) -> bool:
    authorizes = []
    if type_auth == TypeAuthMovement.local:
        result = check_authentication_movement_result_in_cache(r, id_movement, TypeAuthFrom.fingerprint)
        authorizes.append(await result)
    elif type_auth == TypeAuthMovement.paypal:
        result = check_authentication_movement_result_in_cache(r, id_movement, TypeAuthFrom.paypal)
        authorizes.append(await result)
    elif type_auth == TypeAuthMovement.localPaypal:
        result1 = check_authentication_movement_result_in_cache(r, id_movement, TypeAuthFrom.fingerprint)
        result2 = check_authentication_movement_result_in_cache(r, id_movement, TypeAuthFrom.paypal)
        authorizes.append(await result1)
        authorizes.append(await result2)
    elif type_auth == TypeAuthMovement.without:
        result = check_authentication_movement_result_in_cache(r, id_movement, TypeAuthFrom.without)
        authorizes.append(await result)
    else:
        raise option_not_found_exception

    return not authorizes.count(False) > 0


async def delete_authorized_data_based_on_type_auth(r: Redis, id_movement: int, type_auth: TypeAuthMovement) -> bool:
    authorizes = []
    if type_auth == TypeAuthMovement.local:
        result = delete_authentication_movement_result_in_cache(r, id_movement, TypeAuthFrom.fingerprint)
        authorizes.append(await result)
    elif type_auth == TypeAuthMovement.paypal:
        result = delete_authentication_movement_result_in_cache(r, id_movement, TypeAuthFrom.paypal)
        authorizes.append(await result)
    elif type_auth == TypeAuthMovement.localPaypal:
        result1 = delete_authentication_movement_result_in_cache(r, id_movement, TypeAuthFrom.fingerprint)
        result2 = delete_authentication_movement_result_in_cache(r, id_movement, TypeAuthFrom.paypal)
        authorizes.append(await result1)
        authorizes.append(await result2)
    elif type_auth == TypeAuthMovement.without:
        result = delete_authentication_movement_result_in_cache(r, id_movement, TypeAuthFrom.without)
        authorizes.append(await result)
    else:
        raise option_not_found_exception

    return not authorizes.count(False) > 0


async def save_authentication_movement_result_in_cache(
        r: Redis,
        id_movement: int,
        auth_from: Union[str, TypeAuthFrom]
) -> bool:
    subject = get_auth_subject_based_on_from(auth_from)

    return await save_value_in_cache_with_formatted_name(r, subject, 'MOV', id_movement, AUTH_OK, 3600)


async def check_authentication_movement_result_in_cache(
        r: Redis,
        id_movement: int,
        auth_from: Union[str, TypeAuthFrom]
) -> bool:
    subject = get_auth_subject_based_on_from(auth_from)

    try:
        result = await check_auth_movement_result(r, subject, id_movement, 'MOV')
    except HTTPException:
        return False
    except Exception:
        raise cache_exception

    return result


async def delete_authentication_movement_result_in_cache(
        r: Redis,
        id_movement: int,
        auth_from: Union[str, TypeAuthFrom]
) -> bool:
    subject = get_auth_subject_based_on_from(auth_from)

    return await delete_values_in_cache(r, subject, 'MOV', id_movement)


def get_auth_subject_based_on_from(auth_from: Union[str, TypeAuthFrom]) -> str:
    af_object = cast_str_to_auth_from_type(auth_from) if isinstance(auth_from, str) else auth_from

    if af_object == TypeAuthFrom.fingerprint:
        subject = 'F-AUTH'
    elif af_object == TypeAuthFrom.paypal:
        subject = 'P-AUTH'
    elif af_object == TypeAuthFrom.without:
        subject = 'W-AUTH'
    else:
        raise option_not_found_exception

    return subject


def cast_str_to_movement_type(movement_str: str) -> TypeMovement:
    try:
        movement_type = TypeMovement(movement_str)
    except ValueError:
        raise wrong_data_sent_exception

    return movement_type


def cast_str_to_money_type(money_str: str) -> TypeMoney:
    try:
        money_type = TypeMoney(money_str)
    except ValueError:
        raise wrong_data_sent_exception

    return money_type


def cast_str_to_transfer_type(transfer_str: str) -> TypeTransfer:
    try:
        transfer_type = TypeTransfer(transfer_str)
    except ValueError:
        raise wrong_data_sent_exception

    return transfer_type


def cast_str_to_auth_from_type(auth_from: str) -> TypeAuthFrom:
    try:
        auth_from_type = TypeAuthFrom(auth_from.lower())
    except ValueError:
        raise wrong_data_sent_exception

    return auth_from_type


def finish_movement_unsuccessfully(
        db: Session,
        id_movement: Optional[int] = None,
        movement_object: Optional[DbMovement] = None
) -> bool:
    if movement_object is None:
        if id_movement is not None:
            movement_object = get_movement_by_id_movement(db, id_movement)
        else:
            raise compile_exception

    result = force_termination_movement(db, movement_object=movement_object, execute='now')
    return result


async def get_email_of_requester_movement(db: Session, id_movement: int) -> str:
    movement = get_movement_by_id_movement(db, id_movement)

    if movement.type_movement == TypeMovement.deposit.value:
        deposit_db = get_deposit_by_id_movement(db, id_movement)
        return deposit_db.depositor_email

    return await get_email_based_on_id_type(db, movement.id_requester, str(TypeUser.client.value))


def parse_DbMovement_to_BasicExtraMovement(
        movement: DbMovement,
        extra: ExtraMovement
) -> BasicExtraMovement:
    return BasicExtraMovement(
        id_movement=movement.id_movement,
        id_credit=movement.id_credit,
        id_performer=movement.id_performer,
        id_requester=movement.id_requester,
        type_movement=movement.type_movement,
        amount=movement.amount,
        authorized=movement.authorized,
        in_process=movement.in_process,
        successful=movement.successful,
        created_time=movement.created_time,
        extra=extra
    )


def parse_DbDeposit_to_ExtraMovement(deposit: DbDeposit) -> ExtraMovement:
    return ExtraMovement(
        id_detail=deposit.id_deposit,
        movement_nature=NatureMovement.income.value,
        type_submov=deposit.type_deposit,
        destination_credit=deposit.id_destination_credit,
        depositor_name=deposit.depositor_name,
        id_market=None,
        paypal_order=deposit.paypal_id_order
    )


def parse_DbPayment_to_ExtraMovement(
        payment: DbPayment,
        nature_movement: str = NatureMovement.outgoings.value
) -> ExtraMovement:
    return ExtraMovement(
        id_detail=payment.id_payment,
        movement_nature=nature_movement,
        type_submov=payment.type_payment,
        destination_credit=None,
        depositor_name=None,
        id_market=payment.id_market,
        paypal_order=payment.paypal_id_order
    )


def parse_DbTransfer_to_ExtraMovement(transfer: DbTransfer, movement_nature: str) -> ExtraMovement:
    return ExtraMovement(
        id_detail=transfer.id_transfer,
        movement_nature=movement_nature,
        type_submov=transfer.type_transfer,
        destination_credit=transfer.id_destination_credit,
        depositor_name=None,
        id_market=None,
        paypal_order=transfer.paypal_id_order
    )


def parse_DbWithdraw_to_ExtraMovement(withdraw: DbWithdraw) -> ExtraMovement:
    return ExtraMovement(
        id_detail=withdraw.id_movement,
        movement_nature=NatureMovement.outgoings.value,
        type_submov=withdraw.type_withdraw,
        destination_credit=None,
        depositor_name=None,
        id_market=None,
        paypal_order=None
    )
