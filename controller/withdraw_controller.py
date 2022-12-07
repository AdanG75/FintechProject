from sqlalchemy.orm import Session

from controller.credit_controller import check_funds_of_credit, check_owners_of_credit
from db.orm.exceptions_orm import not_sufficient_funds_exception, not_authorized_exception, not_values_sent_exception
from schemas.movement_base import UserDataMovement, MovementTypeRequest
from schemas.movement_complex import ExtraMovementRequest, MovementExtraRequest
from schemas.type_user import TypeUser


async def create_withdraw_formatted(
        db: Session,
        request: MovementTypeRequest,
        user_data: UserDataMovement
) -> MovementExtraRequest:
    if request.id_credit is None:
        raise not_values_sent_exception

    if not (user_data.type_user == TypeUser.market or user_data.type_user == TypeUser.system):
        raise not_authorized_exception

    # This transaction only can be done by a user of type market or system, for that reason el id_market correspond to
    # user_data.id_type_performer
    if not check_owners_of_credit(db, request.id_credit, user_data.id_requester, user_data.id_type_performer):
        raise not_authorized_exception

    if not check_funds_of_credit(db, request.id_credit, request.amount):
        raise not_sufficient_funds_exception

    return MovementExtraRequest(
        id_credit=request.id_credit,
        id_performer=user_data.id_performer,
        id_requester=user_data.id_requester,
        type_movement=request.type_movement,
        amount=request.amount,
        type_user=user_data.type_user,
        extra=ExtraMovementRequest(
            type_submov=str(request.type_submov.value),
            destination_credit=None,
            id_market=None,
            depositor_name=None,
            depositor_email=None,
            paypal_order=None
        )
    )
