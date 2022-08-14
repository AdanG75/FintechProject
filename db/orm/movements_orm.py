from datetime import datetime

from sqlalchemy.orm import Session

from db.models.movements_db import DbMovement
from db.orm.clients_orm import get_client_by_id_client
from db.orm.credits_orm import get_credit_by_id_credit
from db.orm.exceptions_orm import wrong_data_sent_exception, not_identified_client_exception, \
    not_credit_of_client_exception, NotFoundException, option_not_found_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.users_orm import get_user_by_id
from schemas.movement_base import MovementRequest


@multiple_attempts
@full_database_exceptions
def create_movement(
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
            if credit.id_client != request.id_requester:
                raise not_credit_of_client_exception

    except NotFoundException as nfe:
        raise nfe
    except Exception as e:
        print(e)
        raise e

    # TODO: We have to evaluate each type of movement in order to make the correct procedure
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
        successful=False,
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
