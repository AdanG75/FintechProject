import uuid
from typing import Optional

from sqlalchemy.orm import Session


from db.models.markets_db import DbMarket
from db.models.addresses_db import DbAddress  # Don't erase, it's used by relationship from SQLAlchemy
from db.models.branches_db import DbBranch  # Don't erase, it's used by relationship from SQLAlchemy
from db.models.clients_db import DbClient  # Don't erase, it's used by relationship from SQLAlchemy
from db.models.fingerprints_db import DbFingerprint  # Don't erase, it's used by relationship from SQLAlchemy
from db.models.users_db import DbUser
from db.orm.exceptions_orm import element_not_found_exception, type_of_value_not_compatible
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.users_orm import get_user_by_id
from schemas.basic_response import BasicResponse
from schemas.market_base import MarketRequest


@multiple_attempts
@full_database_exceptions
def create_market(db: Session, request: MarketRequest) -> DbMarket:
    user: Optional[DbUser] = get_user_by_id(db, request.id_user)
    if user.type_user != 'market':
        raise type_of_value_not_compatible

    # Clear user object to save space
    user = None

    market_uuid = uuid.uuid4().hex
    id_market = f"MKT-{market_uuid}"

    new_market = DbMarket(
        id_market=id_market,
        id_user=request.id_user,
        type_market=request.type_market,
        web_page=request.web_page,
        rfc=request.rfc
    )

    try:
        db.add(new_market)
        db.commit()
        db.refresh(new_market)
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return new_market


@full_database_exceptions
def get_market_by_id_market(db: Session, id_market: str) -> DbMarket:
    try:
        market = db.query(DbMarket).where(
            DbMarket.id_market == id_market
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if market is None:
        raise element_not_found_exception

    return market


@full_database_exceptions
def get_market_by_id_user(db: Session, id_user: int) -> DbMarket:
    try:
        market = db.query(DbMarket).where(
            DbMarket.id_user == id_user
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if market is None:
        raise element_not_found_exception

    return market


@multiple_attempts
@full_database_exceptions
def update_market(db: Session, request: MarketRequest, id_market: str) -> DbMarket:
    updated_market = get_market_by_id_market(db, id_market)

    updated_market.type_market = request.type_market
    updated_market.web_page = request.web_page
    updated_market.rfc = request.rfc

    try:
        db.commit()
        db.refresh(updated_market)
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return updated_market


@multiple_attempts
@full_database_exceptions
def delete_market(db: Session, id_market: str) -> BasicResponse:
    market = get_market_by_id_market(db, id_market)

    try:
        db.delete(market)
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return BasicResponse(
        operation="delete",
        successful=True
    )
