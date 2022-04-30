# -*- coding: utf-8 -*-

from fastapi import FastAPI

from core.config import settings
from routers import test_functions, admin_router, home

app = FastAPI(
    title=settings.get_project_name(),
    version=settings.get_project_version()
)

app.include_router(routers=home.router)
app.include_router(router=admin_router.router)
app.include_router(router=test_functions.router)






