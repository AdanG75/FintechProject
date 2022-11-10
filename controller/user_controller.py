from typing import Union

from sqlalchemy.orm import Session

from db.models.users_db import DbUser
from db.orm.admins_orm import get_admin_by_id_user
from db.orm.clients_orm import get_client_by_id_user, get_client_by_id_client
from db.orm.exceptions_orm import option_not_found_exception, wrong_public_pem_format_exception
from db.orm.markets_orm import get_market_by_id_user, get_market_by_id_market
from db.orm.users_orm import get_public_key_pem, set_public_key, get_user_by_id, get_user_by_email
from schemas.admin_complex import AdminFullDisplay
from schemas.client_complex import ClientProfileDisplay
from schemas.market_complex import MarketProfileDisplay
from schemas.type_user import TypeUser
from schemas.user_base import UserBasicDisplay
from secure.cipher_secure import is_pem_correct_formatted


def return_type_id_based_on_type_of_user(db: Session, id_user: int, type_user: str) -> str:
    if type_user == TypeUser.market.value or type_user == TypeUser.system.value:
        market = get_market_by_id_user(db, id_user)
        id_type = market.id_market
    elif type_user == TypeUser.client.value:
        client = get_client_by_id_user(db, id_user)
        id_type = client.id_client
    elif type_user == TypeUser.admin.value:
        admin = get_admin_by_id_user(db, id_user)
        id_type = admin.id_admin
    else:
        raise option_not_found_exception

    return id_type


def check_public_key_of_user(db: Session, id_user: int, pem: str) -> bool:
    if not is_pem_correct_formatted(pem):
        raise wrong_public_pem_format_exception

    user_pem = get_public_key_pem(db, id_user)

    if user_pem is None:
        set_public_key(db, id_user, pem)
    else:
        if user_pem != pem:
            set_public_key(db, id_user, pem)

    return True


def get_profile_of_user(
        db: Session,
        id_user: int,
        type_user: str
) -> Union[UserBasicDisplay, AdminFullDisplay, MarketProfileDisplay, ClientProfileDisplay]:
    if type_user == TypeUser.system.value:
        system_data = get_user_by_id(db, id_user)
        user_profile = UserBasicDisplay.from_orm(system_data)

    elif type_user == TypeUser.admin.value:
        user_data = get_user_by_id(db, id_user)
        admin_data = get_admin_by_id_user(db, id_user)
        user_profile = AdminFullDisplay(
            user=user_data,
            admin=admin_data
        )

    elif type_user == TypeUser.market.value:
        user_data = get_user_by_id(db, id_user)
        market_data = get_market_by_id_user(db, id_user)
        user_profile = MarketProfileDisplay(
            user=user_data,
            market=market_data
        )

    elif type_user == TypeUser.client.value:
        user_data = get_user_by_id(db, id_user)
        client_data = get_client_by_id_user(db, id_user)
        user_profile = ClientProfileDisplay(
            user=user_data,
            client=client_data
        )

    else:
        raise option_not_found_exception

    return user_profile


def get_user_using_email(db: Session, user_email: str) -> DbUser:
    return get_user_by_email(db, user_email)


def get_user_using_id_client(db: Session, id_client: str) -> DbUser:
    client = get_client_by_id_client(db, id_client)
    user = get_user_by_id(db, client.id_user)

    return user


def get_user_using_id_market(db: Session, id_market: str) -> DbUser:
    market = get_market_by_id_market(db, id_market)
    user = get_user_by_id(db, market.id_user)

    return user


async def get_name_of_client(db: Session, id_client: str) -> str:
    client = get_client_by_id_client(db, id_client)
    user = get_user_by_id(db, client.id_user)

    return f'{user.name} {client.last_name}'


async def get_name_of_market(db: Session, id_market: str) -> str:
    user = get_user_using_id_market(db, id_market)

    return user.name
