from typing import Union

from sqlalchemy.orm import Session

from db.models.users_db import DbUser
from db.orm import users_orm, admins_orm
from db.orm.exceptions_orm import type_of_value_not_compatible, wrong_data_sent_exception
from schemas.admin_complex import AdminFullRequest, AdminFullDisplay
from schemas.type_user import TypeUser


async def sign_up_admin(
        db: Session,
        admin: AdminFullRequest
) -> AdminFullDisplay:
    if not isinstance(admin, AdminFullRequest):
        raise type_of_value_not_compatible

    try:
        new_user: DbUser = users_orm.create_user(db, admin.user, execute='wait')
        nested = db.begin_nested()
        db.refresh(new_user)
        # Correct id of user
        admin.admin.id_user = new_user.id_user
        new_admin = admins_orm.create_admin(db, admin.admin, execute='wait')
        nested.commit()
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    return AdminFullDisplay(
        user=new_user,
        admin=new_admin
    )


def get_user_type(
        data: Union[dict, AdminFullRequest]
) -> TypeUser:
    if isinstance(data, dict):
        type_user = data['user']['type_user']
        try:
            type_user_object = TypeUser(type_user)
            return type_user_object
        except ValueError:
            raise wrong_data_sent_exception
    else:
        try:
            return data.user.type_user
        except AttributeError:
            raise type_of_value_not_compatible


async def route_user_to_sign_up(
        db: Session,
        request: Union[dict, AdminFullRequest],
        type_user: TypeUser
) -> Union[AdminFullDisplay]:
    if type_user.value == 'admin':
        admin_request = AdminFullRequest.parse_obj(request) if isinstance(request, dict) else request
        response = await sign_up_admin(db, admin_request)
    elif type_user.value == 'market':
        pass

    return response
