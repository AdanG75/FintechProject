from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models.movements_db import DbMovement
from db.orm.clients_orm import get_client_by_id_client
from db.orm.credits_orm import get_credit_by_id_credit
from db.orm.exceptions_orm import wrong_data_sent_exception, not_identified_client_exception, \
    not_credit_of_client_exception, NotFoundException, option_not_found_exception, element_not_found_exception, \
    movement_in_process_exception, movement_finish_exception, movement_not_authorized_exception, \
    type_of_value_not_compatible, movement_already_linked_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.users_orm import get_user_by_id
from schemas.movement_base import MovementRequest
from schemas.type_movement import TypeMovement


@multiple_attempts
@full_database_exceptions
def make_movement(
        db: Session,
        request: MovementRequest,
        execute: str = 'now'
) -> DbMovement:
    try:
        user = get_user_by_id(db, request.id_performer)
        if request.type_user.value != user.type_user:
            raise wrong_data_sent_exception

        if request.id_requester is None:
            if request.type_movement.value == 'transfer' or request.type_movement.value == 'withdraw':
                raise not_identified_client_exception

        else:
            get_client_by_id_client(db, request.id_requester)

        if request.id_credit is not None:
            credit = get_credit_by_id_credit(db, request.id_credit)
            if credit.id_client != request.id_requester and request.type_movement.value != 'deposit':
                raise not_credit_of_client_exception

            if request.type_movement.value == 'deposit':
                request.id_credit = None

    except NotFoundException as nfe:
        raise nfe
    except Exception as e:
        print(e)
        raise e

    # We have to evaluate each type of movement in order to make the correct procedure
    return add_movement(db, request, execute)


@multiple_attempts
@full_database_exceptions
def add_movement(db: Session, request: MovementRequest, execute: str = 'now') -> DbMovement:
    new_movement = DbMovement(
        id_credit=request.id_credit,
        id_performer=request.id_performer,
        id_requester=request.id_requester,
        type_movement=request.type_movement.value,
        amount=request.amount,
        authorized=False,
        type_user=request.type_user.value,
        in_process=False,
        successful=None,
        created_time=datetime.utcnow()
    )

    try:
        db.add(new_movement)
        if execute == 'now':
            db.commit()
            db.refresh(new_movement)
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    return new_movement


@multiple_attempts
@full_database_exceptions
def get_movement_by_id_movement(db: Session, id_movement: int) -> DbMovement:
    movement = db.query(DbMovement).where(
        DbMovement.id_movement == id_movement
    ).one_or_none()

    if movement is None:
        raise element_not_found_exception

    return movement


@multiple_attempts
@full_database_exceptions
def get_movements_by_id_credit(db: Session, id_credit: Optional[int]) -> List[DbMovement]:
    movements = db.query(DbMovement).where(
        DbMovement.id_credit == id_credit
    ).all()

    if movements is None or len(movements) < 1:
        raise element_not_found_exception

    return movements


@multiple_attempts
@full_database_exceptions
def get_movements_by_id_performer(db: Session, id_performer: int) -> List[DbMovement]:
    movements = db.query(DbMovement).where(
        DbMovement.id_performer == id_performer
    ).all()

    if movements is None:
        return []

    return movements


@multiple_attempts
@full_database_exceptions
def get_movements_by_id_requester(db: Session, id_requester: Optional[str]) -> List[DbMovement]:
    movements = db.query(DbMovement).where(
        DbMovement.id_requester == id_requester
    ).all()

    if movements is None:
        return []

    return movements


@multiple_attempts
@full_database_exceptions
def get_movements_by_type(db: Session, type_movement: str) -> List[DbMovement]:
    try:
        TypeMovement(type_movement)
    except ValueError:
        raise wrong_data_sent_exception

    movements = db.query(DbMovement).where(
        DbMovement.type_movement == type_movement
    ).all()

    if movements is None:
        return []

    return movements


@multiple_attempts
@full_database_exceptions
def get_movements_by_id_credit_and_type(db: Session, id_credit: Optional[int], type_movement: str) -> List[DbMovement]:
    try:
        TypeMovement(type_movement)
    except ValueError:
        raise wrong_data_sent_exception

    movements = db.query(DbMovement).where(
        DbMovement.id_credit == id_credit,
        DbMovement.type_movement == type_movement
    ).all()

    if movements is None:
        return []

    return movements


@multiple_attempts
@full_database_exceptions
def get_movements_by_id_requester_and_type(
        db: Session,
        id_requester: Optional[str] = None,
        type_movement: str = 'payment'
) -> List[DbMovement]:
    try:
        TypeMovement(type_movement)
    except ValueError:
        raise wrong_data_sent_exception

    movements = db.query(DbMovement).where(
        DbMovement.id_requester == id_requester,
        DbMovement.type_movement == type_movement
    ).all()

    if movements is None:
        return []

    return movements


@multiple_attempts
@full_database_exceptions
def authorized_movement(
        db: Session,
        id_movement: Optional[int] = None,
        movement_object: Optional[DbMovement] = None,
        execute: str = 'now'
) -> DbMovement:
    if movement_object is None:
        if id_movement is not None:
            movement_object = get_movement_by_id_movement(db, id_movement)
        else:
            raise wrong_data_sent_exception

    if movement_object.successful is not None:
        raise movement_finish_exception

    if not movement_object.in_process:
        movement_object.authorized = True
        movement_object.in_process = True
    else:
        raise movement_in_process_exception

    try:
        if execute == 'now':
            db.commit()
            db.refresh(movement_object)
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return movement_object


@multiple_attempts
@full_database_exceptions
def finish_movement(
        db: Session,
        was_successful: bool,
        id_movement: Optional[int] = None,
        movement_object: Optional[DbMovement] = None,
        execute: str = 'now'
) -> DbMovement:
    if movement_object is None:
        if id_movement is not None:
            movement_object = get_movement_by_id_movement(db, id_movement)
        else:
            raise wrong_data_sent_exception

    if movement_object.successful is not None:
        raise movement_finish_exception

    if movement_object.in_process and movement_object.authorized:
        movement_object.in_process = False
        movement_object.successful = was_successful
    else:
        raise movement_not_authorized_exception

    try:
        if execute == 'now':
            db.commit()
            db.refresh(movement_object)
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return movement_object


@multiple_attempts
@full_database_exceptions
def force_termination_movement(
        db: Session,
        id_movement: Optional[int] = None,
        movement_object: Optional[DbMovement] = None,
        execute: str = 'now'
) -> bool:
    if movement_object is None:
        if id_movement is not None:
            movement_object = get_movement_by_id_movement(db, id_movement)
        else:
            return False

    if movement_object.successful is not None:
        return False
    else:
        movement_object.in_process = False
        movement_object.successful = False

        try:
            if execute == 'now':
                db.commit()
                db.refresh(movement_object)
            elif execute == 'wait':
                pass
            else:
                raise option_not_found_exception
        except Exception as e:
            db.rollback()
            print(e)
            raise e

        return True


def check_type_and_status_of_movement(db: Session, id_movement: int, type_movement: str) -> None:
    try:
        movement = get_movement_by_id_movement(db, id_movement)

        if movement.type_movement != type_movement:
            raise type_of_value_not_compatible

        if movement.in_process or movement.successful is not None:
            raise movement_already_linked_exception
    except HTTPException as httpe:
        raise httpe
    except NotFoundException as nfe:
        raise nfe
    except Exception as e:
        print(e)
        raise e
