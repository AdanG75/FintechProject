from typing import List

from sqlalchemy.orm import Session

from db.models.deposits_db import DbDeposit
from db.models.movements_db import DbMovement
from db.models.payments_db import DbPayment
from db.models.transfers_db import DbTransfer
from db.models.withdraws_db import DbWithdraw
from db.orm.deposits_orm import get_deposits_by_id_destination_credit
from db.orm.exceptions_orm import NotFoundException
from db.orm.movements_orm import get_movements_by_id_credit_and_type, get_movement_by_id_movement, \
    get_movements_by_id_requester_and_type
from db.orm.payments_orm import get_payment_by_id_movement, get_payments_by_id_market
from db.orm.transfers_orm import get_transfer_by_id_movement, get_transfers_by_id_destination_credit
from db.orm.withdraws_orm import get_withdraw_by_id_movement
from schemas.movement_complex import BasicExtraMovement, ExtraMovement
from schemas.payment_base import PaymentComplexList
from schemas.type_movement import TypeMovement, NatureMovement


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
        type_movement=TypeMovement.payment.value
    )

    if len(movements) > 0:
        extra_movements = []
        for movement in movements:
            try:
                payment: DbPayment = get_payment_by_id_movement(db, movement.id_movement)
            except NotFoundException:
                pass
            else:
                extra_information = pasrse_DbPayment_to_ExtraMovement(payment)
                extra_movement = parse_DbMovement_to_BasicExtraMovement(movement, extra_information)
                extra_movements.append(extra_movement)

        return extra_movements

    return movements


def get_payments_of_client(db: Session, id_client: str) -> PaymentComplexList:
    movements = get_movements_by_id_requester_and_type(db, id_client, TypeMovement.payment.value)

    if len(movements) > 0:
        extra_movements = []
        for movement in movements:
            try:
                payment: DbPayment = get_payment_by_id_movement(db, movement.id_movement)
            except NotFoundException:
                pass
            else:
                extra_information = pasrse_DbPayment_to_ExtraMovement(payment)
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
                extra_information = pasrse_DbPayment_to_ExtraMovement(payment, NatureMovement.income.value)
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
                extra_information = pasrse_DbTransfer_to_ExtraMovement(transfer, NatureMovement.income.value)
                extra_movement = parse_DbMovement_to_BasicExtraMovement(movement, extra_information)
                extra_movements.append(extra_movement)

        return extra_movements

    return transfers


async def get_outgoings_transfers_of_credit(db: Session, id_credit: int) -> List[BasicExtraMovement]:
    movements: List[DbMovement] = get_movements_by_id_credit_and_type(
        db=db,
        id_credit=id_credit,
        type_movement=TypeMovement.transfer.value
    )

    if len(movements) > 0:
        extra_movements = []
        for movement in movements:
            try:
                transfer: DbTransfer = get_transfer_by_id_movement(db, movement.id_movement)
            except NotFoundException:
                pass
            else:
                extra_information = pasrse_DbTransfer_to_ExtraMovement(transfer, NatureMovement.outgoings.value)
                extra_movement = parse_DbMovement_to_BasicExtraMovement(movement, extra_information)
                extra_movements.append(extra_movement)

        return extra_movements

    return movements


async def get_withdraw_movements_of_credit(db: Session, id_credit: int) -> List[BasicExtraMovement]:
    movements: List[DbMovement] = get_movements_by_id_credit_and_type(
        db=db,
        id_credit=id_credit,
        type_movement=TypeMovement.withdraw.value
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
        id_market=None,
        paypal_order=deposit.paypal_id_order
    )


def pasrse_DbPayment_to_ExtraMovement(
        payment: DbPayment,
        nature_movement: str = NatureMovement.outgoings.value
) -> ExtraMovement:
    return ExtraMovement(
        id_detail=payment.id_payment,
        movement_nature=nature_movement,
        type_submov=payment.type_payment,
        destination_credit=None,
        id_market=payment.id_market,
        paypal_order=payment.paypal_id_order
    )


def pasrse_DbTransfer_to_ExtraMovement(transfer: DbTransfer, movement_nature: str) -> ExtraMovement:
    return ExtraMovement(
        id_detail=transfer.id_transfer,
        movement_nature=movement_nature,
        type_submov=transfer.type_transfer,
        destination_credit=transfer.id_destination_credit,
        id_market=None,
        paypal_order=transfer.paypal_id_order
    )


def parse_DbWithdraw_to_ExtraMovement(withdraw: DbWithdraw) -> ExtraMovement:
    return ExtraMovement(
        id_detail=withdraw.id_movement,
        movement_nature=NatureMovement.outgoings.value,
        type_submov=withdraw.type_withdraw,
        destination_credit=None,
        id_market=None,
        paypal_order=None
    )
