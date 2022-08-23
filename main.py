# -*- coding: utf-8 -*-
from typing import Union

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.config import settings
from db.orm.exceptions_orm import DBException, NotFoundException
from routers import admin_router, home, icon, static
from routers.test import test_account, test_address, test_admin, test_branch, test_client, test_credit, test_fingerprint, test_login_attempt, test_market, test_movement, test_password_recovery, test_session, test_user, test_functions

app = FastAPI(
    title=settings.get_project_name(),
    version=settings.get_project_version()
)

# Main endpoints
app.include_router(router=home.router)
app.include_router(router=static.router)
# app.include_router(router=admin_router.router)

# test endpoints
app.include_router(router=test_account.router)
app.include_router(router=test_address.router)
app.include_router(router=test_admin.router)
app.include_router(router=test_branch.router)
app.include_router(router=test_client.router)
app.include_router(router=test_credit.router)
app.include_router(router=test_fingerprint.router)
app.include_router(router=test_functions.router)
app.include_router(router=test_login_attempt.router)
app.include_router(router=test_market.router)
app.include_router(router=test_movement.router)
app.include_router(router=test_password_recovery.router)
app.include_router(router=test_session.router)
app.include_router(router=test_user.router)

# Icon endpoint
if not settings.is_on_cloud():
    app.include_router(router=icon.router)


@app.exception_handler(DBException)
@app.exception_handler(NotFoundException)
async def cast_dbexception_to_http_exception(request: Request, exc: Union[DBException, NotFoundException]):
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message}
    )



