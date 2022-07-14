# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.config import settings
from db.orm.exceptions_orm import DBException, db_exception
from routers import admin_router, home, icon, static
from routers.test import test_user, test_functions

app = FastAPI(
    title=settings.get_project_name(),
    version=settings.get_project_version()
)

# Main endpoints
app.include_router(router=home.router)
app.include_router(router=static.router)
# app.include_router(router=admin_router.router)

# test endpoints
app.include_router(router=test_functions.router)
app.include_router(router=test_user.router)

# Icon endpoint
if not settings.is_on_cloud():
    app.include_router(router=icon.router)


@app.exception_handler(DBException)
async def cast_dbexception_to_http_exception(request: Request, exc: DBException):
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message}
    )
