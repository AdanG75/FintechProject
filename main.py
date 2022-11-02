# -*- coding: utf-8 -*-
import os
from typing import Union

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.config import charge_settings
from db.orm.exceptions_orm import DBException, NotFoundException
from routers import credit_router, fingerprint_router, home, icon, market_router, start_router, static, user_router
from routers.test import test_account, test_address, test_admin, test_branch, test_client, test_core, test_credit, \
    test_deposit, test_fingerprint, test_functions, test_login_attempt, test_market, test_minutia, test_movement, \
    test_outstanding_payment, test_password_recovery, test_payment, test_session, test_transfer, test_user, \
    test_withdraw

app = FastAPI(
    title=os.environ.get("PROJECT_NAME"),
    version=os.environ.get("PROJECT_VERSION")
)


@app.on_event("startup")
async def startup_event():
    settings = charge_settings()

    # Icon endpoint
    if not settings.is_on_cloud():
        app.include_router(router=icon.router)

# Main endpoints
app.include_router(router=credit_router.router)
app.include_router(router=fingerprint_router.router)
app.include_router(router=home.router)
app.include_router(router=market_router.router)
app.include_router(router=start_router.router)
app.include_router(router=static.router)
app.include_router(router=user_router.router)


# test endpoints
app.include_router(router=test_account.router)
app.include_router(router=test_address.router)
app.include_router(router=test_admin.router)
app.include_router(router=test_branch.router)
app.include_router(router=test_client.router)
app.include_router(router=test_core.router)
app.include_router(router=test_credit.router)
app.include_router(router=test_deposit.router)
app.include_router(router=test_fingerprint.router)
app.include_router(router=test_functions.router)
app.include_router(router=test_login_attempt.router)
app.include_router(router=test_market.router)
app.include_router(router=test_minutia.router)
app.include_router(router=test_movement.router)
app.include_router(router=test_outstanding_payment.router)
app.include_router(router=test_password_recovery.router)
app.include_router(router=test_payment.router)
app.include_router(router=test_session.router)
app.include_router(router=test_transfer.router)
app.include_router(router=test_user.router)
app.include_router(router=test_withdraw.router)


@app.exception_handler(DBException)
@app.exception_handler(NotFoundException)
async def cast_dbexception_to_http_exception(request: Request, exc: Union[DBException, NotFoundException]):
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message}
    )
