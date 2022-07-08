from typing import Optional, List

from sqlalchemy.orm import Session

from db.models.accounts_db import DbAccount
from db.orm.exceptions_orm import db_exception, element_not_found_exception, email_exception
from db.orm.functions_orm import multiple_attempts
from schemas.account_base import AccountRequest
from schemas.basic_response import BasicResponse
from secure.cipher_secure import cipher_data


@multiple_attempts
def create_account(db: Session, request: AccountRequest) -> DbAccount:
    if len(request.paypal_email) >= 80 or request.paypal_email is None:
        raise email_exception

    new_account = DbAccount(
        id_user=request.id_user,
        alias_account=request.alias_account,
        paypal_email=request.paypal_email,
        paypal_id_client=cipher_data(request.paypal_id_client),
        paypal_secret=cipher_data(request.paypal_secret),
        type_owner=request.type_owner.value,
        main_account=request.main_account
    )

    try:
        db.add(new_account)
        db.commit()
        db.refresh(new_account)
    except Exception as e:
        db.rollback()
        raise db_exception

    return new_account


@multiple_attempts
def add_account(db: Session, request: AccountRequest) -> DbAccount:
    new_account = create_account(db, request)

    if new_account.main_account:
        change_main_account(db, new_account.id_user, new_account.id_account)
        db.refresh(new_account)

    return new_account


def get_account_by_id(db: Session, id_account: int) -> Optional[DbAccount]:
    try:
        account = db.query(DbAccount).where(
            DbAccount.id_account == id_account,
            DbAccount.dropped == False
        ).one_or_none()

    except Exception as e:
        raise db_exception

    if account is None:
        raise element_not_found_exception

    return account


def get_accounts_by_paypal_email(db: Session, paypal_account: str) -> Optional[List[DbAccount]]:
    try:
        accounts = db.query(DbAccount).where(
            DbAccount.paypal_email == paypal_account,
            DbAccount.dropped == False
        ).all()

    except Exception as e:
        raise db_exception

    if accounts is None:
        raise element_not_found_exception

    return accounts


def get_accounts_by_user(db: Session, id_user: int) -> Optional[List[DbAccount]]:
    try:
        accounts = db.query(DbAccount).where(
            DbAccount.id_user == id_user,
            DbAccount.dropped == False
        ).all()

    except Exception as e:
        raise db_exception

    if accounts is None:
        raise element_not_found_exception

    return accounts


def get_main_account_of_user(db: Session, id_user: int) -> DbAccount:
    try:
        account = db.query(DbAccount).where(
            DbAccount.id_user == id_user,
            DbAccount.main_account == True,
            DbAccount.dropped == False
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if account is None:
        raise element_not_found_exception

    return account


@multiple_attempts
def update_account(db: Session, request: AccountRequest, id_account: int) -> DbAccount:
    if len(request.paypal_email) >= 80 or request.paypal_email is None:
        raise email_exception

    updated_account = get_account_by_id(db, id_account)

    updated_account.alias_account = request.alias_account
    updated_account.paypal_email = request.paypal_email
    updated_account.paypal_id_client = cipher_data(request.paypal_id_client)
    updated_account.paypal_secret = cipher_data(request.paypal_secret)
    updated_account.main_account = request.main_account

    try:
        if updated_account.main_account:
            change_main_account(db, updated_account.id_user, updated_account.id_account)
        db.commit()
        db.refresh(updated_account)
    except Exception as e:
        db.rollback()
        raise db_exception

    return updated_account


def change_main_account(db: Session, id_user: int, id_account: int) -> bool:
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
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return True


@multiple_attempts
def delete_account(db: Session, id_account: int) -> BasicResponse:
    account = get_account_by_id(db, id_account)
    account.dropped = True

    try:
        db.commit()
        db.refresh(account)
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )


def delete_accounts_by_id_user(db: Session, id_user: int) -> BasicResponse:
    accounts = get_accounts_by_user(db, id_user)

    for account in accounts:
        account.dropped = True

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="batch delete",
        successful=True
    )
