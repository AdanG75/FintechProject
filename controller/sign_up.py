from sqlalchemy.orm import Session

from db.models.users_db import DbUser
from db.orm import users_orm, admins_orm
from db.orm.exceptions_orm import type_of_value_not_compatible
from schemas.admin_complex import AdminFullRequest, AdminFullDisplay


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
