from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from core.config import settings
from core.utils import money_str_to_float
from db.models.credits_db import DbCredit
from db.orm.accounts_orm import get_main_account_of_user, get_account_by_id
from db.orm.clients_orm import get_client_by_id_client
from db.orm.exceptions_orm import element_not_found_exception, option_not_found_exception, \
    existing_credit_exception, not_void_credit_exception, account_does_not_belong_to_market_exception, \
    global_credit_exception, movement_in_process_exception, NotFoundException
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.markets_orm import get_market_by_id_market
from schemas.basic_response import BasicResponse
from schemas.credit_base import CreditRequest


@multiple_attempts
@full_database_exceptions
def create_credit(
        db: Session,
        request: CreditRequest,
        type_performer: str,
        execute: str = 'now'
) -> DbCredit:
    try:
        get_market_by_id_market(db, request.id_market)
        get_client_by_id_client(db, request.id_client)
    except NotFoundException as e:
        raise e

    existing_credit = get_credit_by_id_market_and_id_client(db, request.id_market, request.id_client, mode='all')

    if existing_credit is None:

        if request.type_credit.value == 'global':
            is_market_of_system(db, request.id_market)

        if request.is_approved is None:
            request.is_approved = False if type_performer == 'client' else True

        if request.id_account is None:
            request.id_account = get_main_id_account_of_market(db, request.id_market)
        else:
            if not check_account_belongs_market(db, request.id_market, request.id_account):
                raise account_does_not_belong_to_market_exception

        new_credit = DbCredit(
            id_client=request.id_client,
            id_market=request.id_market,
            id_account=request.id_account,
            alias_credit=request.alias_credit,
            type_credit=request.type_credit.value,
            amount=request.amount,
            past_amount=0,
            is_approved=request.is_approved,
            in_process=False,
            created_time=datetime.utcnow(),
            dropped=False
        )

        try:
            db.add(new_credit)
            if execute == 'now':
                db.commit()
                db.refresh(new_credit)
            elif execute == 'wait':
                pass
            else:
                raise option_not_found_exception
        except Exception as e:
            db.rollback()
            print(e)
            raise e

        return new_credit
    else:
        if existing_credit.dropped:
            return update_credit(db, existing_credit.id_credit, request, mode='all', execute=execute)
        else:
            raise existing_credit_exception


@full_database_exceptions
def get_credit_by_id_credit(db: Session, id_credit: int, mode: str = 'active') -> DbCredit:
    try:
        if mode == 'active':
            credit = db.query(DbCredit).where(
                DbCredit.id_credit == id_credit,
                DbCredit.dropped == False
            ).one_or_none()
        elif mode == 'all':
            credit = db.query(DbCredit).where(
                DbCredit.id_credit == id_credit
            ).one_or_none()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    if credit is None:
        raise element_not_found_exception

    return credit


@full_database_exceptions
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
        print(e)
        raise e

    return credit


@full_database_exceptions
def get_credits_by_id_client(db: Session, id_client: str, mode: str = 'active') -> Optional[List[DbCredit]]:
    try:
        if mode == 'active':
            client_credits = db.query(DbCredit).where(
                DbCredit.id_client == id_client,
                DbCredit.dropped == False
            ).all()
        elif mode == 'all':
            client_credits = db.query(DbCredit).where(
                DbCredit.id_client == id_client
            ).all()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    return client_credits


@full_database_exceptions
def get_credits_by_id_market(db: Session, id_market: str, mode: str = 'active') -> Optional[List[DbCredit]]:
    try:
        if mode == 'active':
            market_credits = db.query(DbCredit).where(
                DbCredit.id_market == id_market,
                DbCredit.dropped == False
            ).all()
        elif mode == 'all':
            market_credits = db.query(DbCredit).where(
                DbCredit.id_market == id_market
            ).all()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    return market_credits


@full_database_exceptions
def get_credits_by_id_account(db: Session, id_account: int, mode: str = 'active') -> Optional[List[DbCredit]]:
    try:
        if mode == 'active':
            account_credits = db.query(DbCredit).where(
                DbCredit.id_account == id_account,
                DbCredit.dropped == False
            ).all()
        elif mode == 'all':
            account_credits = db.query(DbCredit).where(
                DbCredit.id_account == id_account
            ).all()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    return account_credits


@multiple_attempts
@full_database_exceptions
def update_credit(
        db: Session,
        id_credit: int,
        request: CreditRequest,
        mode: str = 'active',
        execute: str = 'now'
) -> DbCredit:
    updated_credit = get_credit_by_id_credit(db, id_credit, mode)

    if request.id_account is not None:
        if check_account_belongs_market(db, updated_credit.id_market, request.id_account):
            updated_credit.id_account = request.id_account
        else:
            raise account_does_not_belong_to_market_exception

    if request.is_approved is not None:
        updated_credit.is_approved = request.is_approved

    updated_credit.alias_credit = request.alias_credit
    updated_credit.in_process = False

    if updated_credit.dropped:
        updated_credit.past_amount = updated_credit.amount
        updated_credit.amount = request.amount

    updated_credit.dropped = False

    try:
        if execute == 'now':
            db.commit()
            db.refresh(updated_credit)
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return updated_credit


@multiple_attempts
@full_database_exceptions
def change_account_of_credit(
        db: Session,
        id_credit: Optional[int] = None,
        credit_object: Optional[DbCredit] = None,
        id_account: Optional[int] = None,
        execute: str = 'now'
) -> bool:
    if credit_object is None:
        credit_object = get_credit_by_id_credit(db, id_credit)

    if id_account is None:
        id_account = get_main_id_account_of_market(db, credit_object.id_market)
    else:
        if not check_account_belongs_market(db, credit_object.id_market, id_account):
            raise account_does_not_belong_to_market_exception

    credit_object.id_account = id_account

    try:
        if execute == 'now':
            db.commit()
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    return True


@multiple_attempts
@full_database_exceptions
def do_amount_movement(db: Session, id_credit: int, amount: float, execute: str = 'now') -> DbCredit:
    updated_credit = get_credit_by_id_credit(db, id_credit)

    if updated_credit.in_process:
        raise movement_in_process_exception

    updated_credit.past_amount = updated_credit.amount
    updated_credit.amount = amount

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

    return updated_credit


@multiple_attempts
@full_database_exceptions
def cancel_amount_movement(db: Session, id_credit: int, execute: str = 'now') -> DbCredit:
    credit = get_credit_by_id_credit(db, id_credit)

    if credit.in_process:
        credit.amount = credit.past_amount
        credit.in_process = False

    if execute == 'now':
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    elif execute == 'wait':
        pass
    else:
        raise option_not_found_exception

    return credit


@multiple_attempts
@full_database_exceptions
def approve_credit(db: Session, id_credit: int, execute: str = 'now') -> DbCredit:
    approved_credit = get_credit_by_id_credit(db, id_credit)

    approved_credit.is_approved = True

    try:
        if execute == 'now':
            db.commit()
            db.refresh(approved_credit)
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return approved_credit


@multiple_attempts
@full_database_exceptions
def start_credit_in_process(
        db: Session,
        id_credit: Optional[int] = None,
        credit_object: Optional[DbCredit] = None,
        execute: str = 'now'
) -> DbCredit:

    if credit_object is None:
        credit_object = get_credit_by_id_credit(db, id_credit)

    credit_object.in_process = True

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

    return credit_object


@multiple_attempts
@full_database_exceptions
def finish_credit_in_process(
        db: Session,
        id_credit: Optional[int] = None,
        credit_object: Optional[DbCredit] = None,
        execute: str = 'now'
) -> DbCredit:

    if credit_object is None:
        credit_object = get_credit_by_id_credit(db, id_credit)

    credit_object.in_process = False

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

    return credit_object


@multiple_attempts
@full_database_exceptions
def delete_credit(
        db: Session,
        id_credit: int,
        type_performer: str,
        execute: str = 'now'
) -> BasicResponse:
    credit = get_credit_by_id_credit(db, id_credit)
    if type_performer == 'market' and money_str_to_float(str(credit.amount)) > 0:
        raise not_void_credit_exception

    credit.dropped = True

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

    return BasicResponse(
        operation="delete",
        successful=True
    )


@multiple_attempts
@full_database_exceptions
def delete_credits_by_id_client(db: Session, id_client: str, execute: str = 'now') -> BasicResponse:
    client_credits = get_credits_by_id_client(db, id_client)

    if client_credits is not None:
        for credit in client_credits:
            credit.dropped = True

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

    return BasicResponse(
        operation="Batch delete",
        successful=True
    )


@multiple_attempts
@full_database_exceptions
def delete_credits_by_id_market(db: Session, id_market: str, execute: str = 'now') -> BasicResponse:
    market_credits = get_credits_by_id_market(db, id_market)

    if market_credits is not None:
        for credit in market_credits:
            if money_str_to_float(str(credit.amount)) <= 0:
                credit.dropped = True

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

    return BasicResponse(
        operation="Batch delete",
        successful=True
    )


@multiple_attempts
@full_database_exceptions
def delete_credits_by_id_account(
        db: Session,
        id_account: int,
        execute: str = 'now'
) -> BasicResponse:
    account_credits = get_credits_by_id_account(db, id_account)

    if account_credits is not None:
        if len(account_credits) > 0:
            main_id_account = get_main_id_account_of_market(db, account_credits[0].id_market)

            for credit in account_credits:
                if credit.amount > 0 and main_id_account != credit.id_account:
                    change_account_of_credit(db=db, credit_object=credit, execute='wait')
                else:
                    db.rollback()
                    raise not_void_credit_exception

                credit.dropped = True

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

    return BasicResponse(
        operation="Batch delete",
        successful=True
    )


@multiple_attempts
@full_database_exceptions
def is_market_of_system(db: Session, id_market: str) -> bool:
    market = get_market_by_id_market(db, id_market)
    if not market.id_user == settings.get_id_system():
        raise global_credit_exception

    return True


@multiple_attempts
@full_database_exceptions
def check_account_belongs_market(db: Session, id_market: str, id_account: int) -> bool:
    market = get_market_by_id_market(db, id_market)
    account = get_account_by_id(db, id_account)

    if market.id_user == account.id_user:
        return True
    else:
        return False


@multiple_attempts
def get_main_id_account_of_market(db: Session, id_market: str) -> int:
    market = get_market_by_id_market(db, id_market)
    main_account = get_main_account_of_user(db, market.id_user)
    id_account: int = int(main_account.id_account)

    return id_account
