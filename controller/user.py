
from sqlalchemy.orm import Session

from db.orm.admins_orm import get_admin_by_id_user
from db.orm.clients_orm import get_client_by_id_user
from db.orm.exceptions_orm import option_not_found_exception
from db.orm.markets_orm import get_market_by_id_user
from schemas.type_user import TypeUser


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
