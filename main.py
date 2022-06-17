# -*- coding: utf-8 -*-

from fastapi import FastAPI

from core.config import settings
from routers import test_functions, admin_router, home, icon, static

app = FastAPI(
    title=settings.get_project_name(),
    version=settings.get_project_version()
)

app.include_router(router=home.router)
app.include_router(router=admin_router.router)
app.include_router(router=test_functions.router)
app.include_router(router=static.router)
if not settings.is_on_cloud():
    app.include_router(router=icon.router)






