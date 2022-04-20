# -*- coding: utf-8 -*-

from fastapi import FastAPI

from core.config import settings
from routers import test_functions

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
settings.start()
app.include_router(router=test_functions.router)
# print(sys.path)


@app.get(
    path='/'
)
def get():
    """
    Return a friendly HTTP greeting
    :return: a dictionary with this format {hello: world}
    """
    return {'hello': ' cruel world'}

