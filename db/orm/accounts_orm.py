from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from db.models.accounts_db import DbAccount
from db.models.users_db import DbUser  # Don't erase because it is used by relationship
from db.orm.exceptions_orm import element_not_found_exception, email_exception, \
    not_main_element_exception, option_not_found_exception, NotFoundException, type_of_value_not_compatible, \
    operation_need_a_precondition_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.users_orm import get_user_by_id
from schemas.account_base import AccountRequest
from schemas.basic_response import BasicResponse
from secure.cipher_secure import cipher_data


@multiple_attempts
@full_database_exceptions
def create_account(db: Session, request: AccountRequest, execute: str = 'now') -> DbAccount:
    user = get_user_by_id(db, request.id_user)
    if user.type_user == 'admin':
        raise type_of_value_not_compatible

    # Clean user
    user = None

    if len(request.paypal_email) >= 80 or request.paypal_email is None:
        raise email_exception

    try:
        past_main_account = get_main_account_of_user(db, request.id_user)
        if request.main_account:
            past_main_account.main_account = False
    except NotFoundException:
        # If not is findit it is because there an active account
        request.main_account = True

    new_account = DbAccount(
        id_user=request.id_user,
        alias_account=request.alias_account,
        paypal_email=request.paypal_email,
        paypal_id_client=cipher_data(request.paypal_id_client),
        paypal_secret=cipher_data(request.paypal_secret),
        type_owner=request.type_owner.value,
        main_account=request.main_account,
        created_time=datetime.utcnow(),
        dropped=False
    )

    try:
        db.add(new_account)
        if execute == 'now':
            db.commit()
            db.refresh(new_account)
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return new_account


@full_database_exceptions
def get_account_by_id(db: Session, id_account: int, mode: str = 'active') -> DbAccount:
    try:
        if mode == 'active':
            account = db.query(DbAccount).where(
                DbAccount.id_account == id_account,
                DbAccount.dropped == False
            ).one_or_none()
        elif mode == 'all':
            account = db.query(DbAccount).where(
                DbAccount.id_account == id_account
            ).one_or_none()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    if account is None:
        raise element_not_found_exception

    return account


@full_database_exceptions
def get_accounts_by_paypal_email(db: Session, paypal_account: str) -> List[DbAccount]:
    try:
        accounts = db.query(DbAccount).where(
            DbAccount.paypal_email == paypal_account,
            DbAccount.dropped == False
        ).all()

    except Exception as e:
        print(e)
        raise e

    if accounts is None or len(accounts) < 1:
        raise element_not_found_exception

    return accounts


@full_database_exceptions
def get_accounts_by_user(db: Session, id_user: int, mode: str = 'active') -> List[DbAccount]:
    try:
        if mode == 'active':
            accounts = db.query(DbAccount).where(
                DbAccount.id_user == id_user,
                DbAccount.dropped == False
            ).all()
        elif mode == 'all':
            accounts = db.query(DbAccount).where(
                DbAccount.id_user == id_user
            ).all()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    if accounts is None or len(accounts) < 1:
        raise element_not_found_exception

    return accounts


@full_database_exceptions
def get_accounts_by_user_and_alias(db: Session, id_user: int, alias: str) -> List[DbAccount]:
    try:
        accounts = db.query(DbAccount).where(
            DbAccount.id_user == id_user,
            DbAccount.alias_account == alias,
            DbAccount.dropped == False
        ).all()
    except Exception as e:
        print(e)
        raise e

    if accounts is None or len(accounts) < 1:
        raise element_not_found_exception

    return accounts


@full_database_exceptions
def get_main_account_of_user(db: Session, id_user: int) -> DbAccount:
    try:
        account = db.query(DbAccount).where(
            DbAccount.id_user == id_user,
            DbAccount.main_account == True,
            DbAccount.dropped == False
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if account is None:
        raise element_not_found_exception

    return account


@full_database_exceptions
def get_a_secondary_account_of_user(db: Session, id_user: int) -> DbAccount:
    try:
        account = db.query(DbAccount).where(
            DbAccount.id_user == id_user,
            DbAccount.main_account == False,
            DbAccount.dropped == False
        ).first()
    except Exception as e:
        print(e)
        raise e

    if account is None:
        raise element_not_found_exception

    return account


@multiple_attempts
@full_database_exceptions
def update_account(
        db: Session,
        request: AccountRequest,
        id_account: int,
        execute: str = 'now'
) -> DbAccount:
    if len(request.paypal_email) >= 80 or request.paypal_email is None:
        raise email_exception

    past_main_account = get_main_account_of_user(db, request.id_user)
    if request.main_account:
        if past_main_account.id_account != id_account:
            past_main_account.main_account = False
    else:
        if past_main_account.id_account == id_account:
            raise not_main_element_exception

    updated_account = get_account_by_id(db, id_account)

    if request.paypal_id_client is not None:
        updated_account.paypal_id_client = cipher_data(request.paypal_id_client)

    if request.paypal_secret is not None:
        updated_account.paypal_secret = cipher_data(request.paypal_secret)

    updated_account.alias_account = request.alias_account
    updated_account.paypal_email = request.paypal_email
    updated_account.main_account = request.main_account
    updated_account.dropped = False

    if execute == 'now':
        try:
            db.commit()
            db.refresh(updated_account)
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    elif execute == 'wait':
        pass
    else:
        raise option_not_found_exception

    return updated_account


@multiple_attempts
@full_database_exceptions
def change_main_account(db: Session, id_user: int, id_account: int, execute: str = 'now') -> bool:
    try:
        db.query(DbAccount).where(
            DbAccount.id_account != id_account,
            DbAccount.id_user == id_user,
            DbAccount.dropped == False
        ).update(
            {DbAccount.main_account: False},
            synchronize_session=False
        )
        db.query(DbAccount).where(
            DbAccount.id_account == id_account,
            DbAccount.dropped == False
        ).update(
            {DbAccount.main_account: True},
            synchronize_session=False
        )
    except Exception as e:
        db.rollback()
        print(e)
        raise e

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

    return True


@multiple_attempts
@full_database_exceptions
def delete_account(db: Session, id_account: int, execute: str = 'now') -> BasicResponse:
    account = get_account_by_id(db, id_account)

    if account.main_account:
        try:
            new_main_account = get_a_secondary_account_of_user(db, account.id_user)
            new_main_account.main_account = True
        except NotFoundException:
            user = get_user_by_id(db, account.id_user, mode='all')
            if user.type_user == 'market' and not user.dropped:
                raise not_main_element_exception

    account.main_account = False
    account.dropped = True

    if execute == 'now':
        try:
            db.commit()
            db.refresh(account)
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


@multiple_attempts
@full_database_exceptions
def delete_accounts_by_id_user(db: Session, id_user: int, execute: str = 'now') -> BasicResponse:
    user = get_user_by_id(db, id_user, mode='all')
    if user.type_user == 'market' and not user.dropped:
        # It is necessary that the user of type market is erased to drop all associated accounts
        raise operation_need_a_precondition_exception

    accounts = get_accounts_by_user(db, id_user)
    for account in accounts:
        account.main_account = False
        account.dropped = True

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

    return BasicResponse(
        operation="batch delete",
        successful=True
    )
