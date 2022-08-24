import uuid
from typing import List

from sqlalchemy.orm import Session

from db.models.transfers_db import DbTransfer
from db.orm.exceptions_orm import NotFoundException, wrong_data_sent_exception, option_not_found_exception, \
    not_unique_value, element_not_found_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.movements_orm import check_type_and_status_of_movement
from schemas.transfer_base import TransferRequest


@multiple_attempts
@full_database_exceptions
def create_transfer(db: Session, request: TransferRequest, execute: str = 'now') -> DbTransfer:
    check_type_and_status_of_movement(db, request.id_movement, 'transfer')

    try:
        get_transfer_by_id_movement(db, request.id_movement)
    except NotFoundException:
        if request.paypal_id_order is None and (request.type_transfer.value == 'localL' or 'localG'):
            raise wrong_data_sent_exception

        transfer_uuid = uuid.uuid4().hex
        id_transfer = "TRS" + transfer_uuid

        new_transfer = DbTransfer(
            id_transfer=id_transfer,
            id_movement=request.id_movement,
            id_destination_credit=request.id_destination_credit,
            type_transfer=request.type_transfer.value,
            paypal_id_order=request.paypal_id_order
        )

        try:
            db.add(new_transfer)
            if execute == 'now':
                db.commit()
                db.refresh(new_transfer)
            elif execute == 'wait':
                pass
            else:
                raise option_not_found_exception
        except Exception as e:
            db.rollback()
            print(e)
            raise e

        return new_transfer

    raise not_unique_value



@multiple_attempts
@full_database_exceptions
def get_transfer_by_id_transfer(db: Session, id_transfer: str) -> DbTransfer:
    try:
        transfer = db.query(DbTransfer).where(
            DbTransfer.id_transfer == id_transfer
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if transfer is None:
        raise element_not_found_exception

    return transfer


@multiple_attempts
@full_database_exceptions
def get_transfer_by_id_movement(db: Session, id_movement: int) -> DbTransfer:
    try:
        transfer = db.query(DbTransfer).where(
            DbTransfer.id_movement == id_movement
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if transfer is None:
        raise element_not_found_exception

    return transfer


@multiple_attempts
@full_database_exceptions
def get_transfers_by_id_destination_credit(db: Session, id_destination_credit: int) -> List[DbTransfer]:
    try:
        transfers = db.query(DbTransfer).where(
            DbTransfer.id_destination_credit == id_destination_credit
        ).all()
    except Exception as e:
        print(e)
        raise e

    if transfers is None:
        raise element_not_found_exception

    return transfers
