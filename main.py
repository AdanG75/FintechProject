# -*- coding: utf-8 -*-
import sys

from fastapi import FastAPI

from routers import test_functions

app = FastAPI()
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


