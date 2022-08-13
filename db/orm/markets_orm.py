import uuid
from typing import Optional

from sqlalchemy.orm import Session


from db.models.addresses_db import DbAddress  # Don't erase because it is used by relationship
from db.models.branches_db import DbBranch  # Don't erase because it is used by relationship
from db.models.clients_db import DbClient  # Don't erase because it is used by relationship
from db.models.fingerprints_db import DbFingerprint  # Don't erase because it is used by relationship
from db.models.markets_db import DbMarket
from db.models.users_db import DbUser
from db.orm.exceptions_orm import element_not_found_exception, type_of_value_not_compatible, option_not_found_exception, \
    NotFoundException, not_unique_value, operation_need_a_precondition_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.users_orm import get_user_by_id
from schemas.basic_response import BasicResponse
from schemas.market_base import MarketRequest


@multiple_attempts
@full_database_exceptions
def create_market(
        db: Session,
        request: MarketRequest,
        execute: str = 'now'
) -> DbMarket:
    user: Optional[DbUser] = get_user_by_id(db, request.id_user)
    # Raise an error when user type is different to 'market' or 'system'
    if not (user.type_user == 'market' or user.type_user == 'system'):
        raise type_of_value_not_compatible

    # Clear user object to save space
    user = None

    try:
        market = get_market_by_id_user(db, request.id_user, mode='all')
    except NotFoundException:
        market_uuid = uuid.uuid4().hex
        id_market = f"MKT-{market_uuid}"

        new_market = DbMarket(
            id_market=id_market,
            id_user=request.id_user,
            type_market=request.type_market,
            web_page=request.web_page,
            rfc=request.rfc,
            dropped=False
        )

        try:
            db.add(new_market)
            if execute == 'now':
                db.commit()
                db.refresh(new_market)
            elif execute == 'wait':
                pass
            else:
                raise option_not_found_exception
        except Exception as e:
            db.rollback()
            print(e)
            raise e

        return new_market

    if market.dropped:
        return update_market(
            db,
            request,
            market.id_market,
            mode='all',
            execute=execute
        )

    raise not_unique_value


@full_database_exceptions
def get_market_by_id_market(db: Session, id_market: str, mode: str = 'active') -> DbMarket:
    try:
        if mode == 'active':
            market = db.query(DbMarket).where(
                DbMarket.id_market == id_market,
                DbMarket.dropped == False
            ).one_or_none()
        elif mode == 'all':
            market = db.query(DbMarket).where(
                DbMarket.id_market == id_market
            ).one_or_none()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    if market is None:
        raise element_not_found_exception

    return market


@full_database_exceptions
def get_market_by_id_user(db: Session, id_user: int, mode: str = 'active') -> DbMarket:
    try:
        if mode == 'active':
            market = db.query(DbMarket).where(
                DbMarket.id_user == id_user,
                DbMarket.dropped == False
            ).one_or_none()
        elif mode == 'all':
            market = db.query(DbMarket).where(
                DbMarket.id_user == id_user
            ).one_or_none()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    if market is None:
        raise element_not_found_exception

    return market


@multiple_attempts
@full_database_exceptions
def update_market(
        db: Session,
        request: MarketRequest,
        id_market: str,
        mode: str = 'active',
        execute: str = 'now'
) -> DbMarket:
    updated_market = get_market_by_id_market(db, id_market, mode=mode)

    updated_market.type_market = request.type_market
    updated_market.web_page = request.web_page
    updated_market.rfc = request.rfc
    updated_market.dropped = False

    if execute == 'now':
        try:
            db.commit()
            db.refresh(updated_market)
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    elif execute == 'wait':
        pass
    else:
        raise option_not_found_exception

    return updated_market


@multiple_attempts
@full_database_exceptions
def delete_market(db: Session, id_market: str, execute: str = 'now') -> BasicResponse:
    market = get_market_by_id_market(db, id_market)
    try:
        get_user_by_id(db, market.id_user)
    except NotFoundException:
        # If user was not found that means it was deleted
        pass
    else:
        # It is necessary that the user is erased to drop the market.
        raise operation_need_a_precondition_exception

    market.dropped = True

    if execute == 'now':
        try:
            # No longer necessary
            # db.delete(market)
            db.commit()
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    elif execute == 'wait':
        pass
    else:
        raise option_not_found_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )
