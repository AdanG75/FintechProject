# -*- coding: utf-8 -*-
import os
from typing import Union

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.config import charge_settings, ON_CLOUD
from core.router_manager import add_main_routers, add_test_routers
from db.orm.exceptions_orm import DBException, NotFoundException
from routers import icon

app = FastAPI(
    title=os.environ.get("PROJECT_NAME"),
    version=os.environ.get("PROJECT_VERSION")
)

add_main_routers(app)
add_test_routers(app)


@app.on_event("startup")
async def startup_event():
    settings = charge_settings()

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


if not ON_CLOUD:
    origins = [
        "http://localhost:3000"
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
