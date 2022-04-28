# -*- coding: utf-8 -*-

from fastapi import FastAPI

from core.config import settings
from routers import test_functions, admin_router

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
app.include_router(router=test_functions.router)
app.include_router(router=admin_router.router)


@app.get(
    path='/'
)
def get():
    """
    Return a friendly HTTP greeting
    :return: a dictionary with this format {hello: world}
    """
    return {'hello': ' cruel world'}

