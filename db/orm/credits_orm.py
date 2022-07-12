from typing import Optional, List

from sqlalchemy.orm import Session

from db.models.credits_db import DbCredit
from db.orm.exceptions_orm import db_exception, element_not_found_exception, option_not_found_exception, \
    existing_credit_exception
from db.orm.functions_orm import multiple_attempts
from schemas.basic_response import BasicResponse
from schemas.credit_base import CreditRequest


@multiple_attempts
def create_account(db: Session, request: CreditRequest) -> DbCredit:

    existing_credit = get_credit_by_id_market_and_id_client(db, request.id_market, request.id_client, mode='all')

    if existing_credit is None:
        new_credit = DbCredit(
            id_client=request.id_client,
            id_market=request.id_market,
            id_account=request.id_account,
            alias_credit=request.alias_credit,
            type_credit=request.type_credit.value,
            amount=request.amount,
            past_amount=0,
            is_approved=request.is_approved,
            in_process=False
        )

        try:
            db.add(new_credit)
            db.commit()
            db.refresh(new_credit)
        except Exception as e:
            db.rollback()
            raise db_exception

        return new_credit
    else:
        if existing_credit.dropped:
            return update_credit(db, existing_credit.id_credit, request, mode='recover')
        else:
            raise existing_credit_exception


def get_credit_by_id_credit(db: Session, id_credit: int) -> DbCredit:
    try:
        credit = db.query(DbCredit).where(
            DbCredit.id_credit == id_credit,
            DbCredit.dropped == False
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if credit is None:
        raise element_not_found_exception

    return credit


def get_credit_by_id_market_and_id_client(
        db: Session,
        id_market: str,
        id_client: str,
        mode: str = 'active'
) -> Optional[DbCredit]:
    try:
        if mode == 'active':
            credit = db.query(DbCredit).where(
                DbCredit.id_client == id_client,
                DbCredit.id_market == id_market,
                DbCredit.dropped == False
            ).one_or_none()
        elif mode == 'all':
            credit = db.query(DbCredit).where(
                DbCredit.id_client == id_client,
                DbCredit.id_market == id_market
            ).one_or_none()
        else:
            raise option_not_found_exception
    except Exception as e:
        raise db_exception

    return credit


def get_credits_by_id_client(db: Session, id_client: str) -> Optional[List[DbCredit]]:
    try:
        client_credits = db.query(DbCredit).where(
            DbCredit.id_client == id_client,
            DbCredit.dropped == False
        ).all()
    except Exception as e:
        raise db_exception

    return client_credits


def get_credits_by_id_market(db: Session, id_market: str) -> Optional[List[DbCredit]]:
    try:
        market_credits = db.query(DbCredit).where(
            DbCredit.id_market == id_market,
            DbCredit.dropped == False
        ).all()
    except Exception as e:
        raise db_exception

    return market_credits


def get_credits_by_id_account(db: Session, id_account: int) -> Optional[List[DbCredit]]:
    try:
        account_credits = db.query(DbCredit).where(
            DbCredit.id_account == id_account,
            DbCredit.dropped == False
        ).all()
    except Exception as e:
        raise db_exception

    return account_credits


@multiple_attempts
def update_credit(
        db: Session,
        id_credit: int,
        request: CreditRequest,
        mode: str = 'update'
) -> DbCredit:
    updated_credit = get_credit_by_id_credit(db, id_credit)

    updated_credit.alias_credit = request.alias_credit
    updated_credit.dropped = False

    if mode == 'recover':
        updated_credit.past_amount = updated_credit.amount
        updated_credit.amount = request.amount

    try:
        db.commit()
        db.refresh(updated_credit)
    except Exception as e:
        db.rollback()
        raise db_exception

    return updated_credit


@multiple_attempts
def do_amount_movement(db: Session, id_credit: int, amount: float) -> DbCredit:
    updated_credit = get_credit_by_id_credit(db, id_credit)

    updated_credit.past_amount = updated_credit.amount
    updated_credit.amount = amount

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return updated_credit


@multiple_attempts
def approve_credit(db: Session, id_credit: int) -> DbCredit:
    approved_credit = get_credit_by_id_credit(db, id_credit)

    approved_credit.is_approved = True

    try:
        db.commit()
        db.refresh(approved_credit)
    except Exception as e:
        db.rollback()
        raise db_exception

    return approved_credit


@multiple_attempts
def start_credit_in_process(db: Session, id_credit: int) -> DbCredit:
    credit = get_credit_by_id_credit(db, id_credit)

    credit.in_process = True

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return credit


@multiple_attempts
def finish_credit_in_process(db: Session, id_credit: int) -> DbCredit:
    credit = get_credit_by_id_credit(db, id_credit)

    credit.in_process = False

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return credit


@multiple_attempts
def delete_credit(db: Session, id_credit: int) -> BasicResponse:
    credit = get_credit_by_id_credit(db, id_credit)
    credit.dropped = True

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )


@multiple_attempts
def delete_credits_by_id_client(db: Session, id_client: str) -> BasicResponse:
    client_credits = get_credits_by_id_client(db, id_client)

    if client_credits is not None:
        for credit in client_credits:
            credit.dropped = True

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise db_exception

    return BasicResponse(
        operation="batch delete",
        successful=True
    )


@multiple_attempts
def delete_credits_by_id_market(db: Session, id_market: str) -> BasicResponse:
    market_credits = get_credits_by_id_market(db, id_market)

    if market_credits is not None:
        for credit in market_credits:
            credit.dropped = True

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise db_exception

    return BasicResponse(
        operation="batch delete",
        successful=True
    )


@multiple_attempts
def delete_credits_by_id_account(db: Session, id_account: int) -> BasicResponse:
    account_credits = get_credits_by_id_account(db, id_account)

    if account_credits is not None:
        for credit in account_credits:
            credit.dropped = True

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise db_exception

    return BasicResponse(
        operation="batch delete",
        successful=True
    )


