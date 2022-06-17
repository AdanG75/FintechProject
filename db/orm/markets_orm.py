import uuid

from sqlalchemy.orm import Session


from db.models.markets_db import DbMarket
from db.orm.exceptions_orm import db_exception, element_not_found_exception
from db.orm.functions_orm import multiple_attempts
from schemas.basic_response import BasicResponse
from schemas.market_base import MarketRequest


@multiple_attempts
def create_market(db: Session, request: MarketRequest) -> DbMarket:
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
        raise db_exception

    return new_market


def get_market_by_id_market(db: Session, id_market: str) -> DbMarket:
    try:
        market = db.query(DbMarket).where(
            DbMarket.id_market == id_market
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if market is None:
        raise element_not_found_exception

    return market


def get_market_by_id_user(db: Session, id_user: int) -> DbMarket:
    try:
        market = db.query(DbMarket).where(
            DbMarket.id_user == id_user
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if market is None:
        raise element_not_found_exception

    return market


@multiple_attempts
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
        raise db_exception

    return updated_market


@multiple_attempts
def delete_market(db: Session, id_market: str) -> BasicResponse:
    market = get_market_by_id_market(db, id_market)

    try:
        db.delete(market)
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )
