import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from db.models.credits_db import DbCredit
from db.models.movements_db import DbMovement
from db.models.transfers_db import DbTransfer
from db.orm.credits_orm import get_credit_by_id_credit
from db.orm.exceptions_orm import NotFoundException, wrong_data_sent_exception, option_not_found_exception, \
    not_unique_value, element_not_found_exception, not_values_sent_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.movements_orm import check_type_and_status_of_movement, get_movement_by_id_movement
from schemas.transfer_base import TransferRequest
from schemas.type_transfer import TypeTransfer


@multiple_attempts
@full_database_exceptions
def create_transfer(db: Session, request: TransferRequest, execute: str = 'now') -> DbTransfer:
    check_type_and_status_of_movement(db, request.id_movement, 'transfer')

    try:
        get_transfer_by_id_movement(db, request.id_movement)
    except NotFoundException:
        transfer_uuid = uuid.uuid4().hex
        id_transfer = "TRS-" + transfer_uuid

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


@multiple_attempts
@full_database_exceptions
def put_paypal_id_order(
        db: Session,
        paypal_id_order: str,
        id_transfer: Optional[str] = None,
        id_movement: Optional[int] = None,
        transfer_object: Optional[DbTransfer] = None,
        execute: str = 'now'
) -> DbTransfer:
    if transfer_object is None:
        if id_movement is not None:
            transfer_object = get_transfer_by_id_movement(db, id_movement)
        elif id_transfer is not None:
            transfer_object = get_transfer_by_id_transfer(db, id_transfer)
        else:
            raise not_values_sent_exception

    if transfer_object.paypal_id_order is None \
            and (transfer_object.type_transfer.value == 'localL' or transfer_object.type_transfer.value == 'localG'):
        transfer_object.paypal_id_order = paypal_id_order
    else:
        raise wrong_data_sent_exception

    try:
        if execute == 'now':
            db.commit()
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return transfer_object


@multiple_attempts
@full_database_exceptions
def get_type_of_transfer(
        db: Session,
        id_destination_credit: int,
        id_movement: Optional[int] = None,
        movement_object: Optional[DbMovement] = None
) -> TypeTransfer:
    if movement_object is None:
        if id_movement is not None:
            movement_object = get_movement_by_id_movement(db, id_movement)
        else:
            raise not_values_sent_exception

    origin_credit = get_credit_by_id_credit(db, movement_object.id_credit)
    destination_credit = get_credit_by_id_credit(db, id_destination_credit)

    return __return_transfer_type(origin_credit, destination_credit)


def __return_transfer_type(origin_credit: DbCredit, destination_credit: DbCredit) -> TypeTransfer:
    if origin_credit.type_credit == 'local' and destination_credit.type_credit == 'local':
        return TypeTransfer.local_to_local
    elif origin_credit.type_credit == 'local' and destination_credit.type_credit == 'global':
        return TypeTransfer.local_to_global
    elif origin_credit.type_credit == 'global' and destination_credit.type_credit == 'local':
        return TypeTransfer.global_to_local
    elif origin_credit.type_credit == 'global' and destination_credit.type_credit == 'global':
        return TypeTransfer.global_to_global
    else:
        return TypeTransfer.default
