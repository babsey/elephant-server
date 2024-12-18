#!/usr/bin/env python3
# main.py

import os

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import elephant

# local imports
from .exceptions import ErrorHandler
from .helpers import do_api_call, do_exec, do_list_calls
from .utils import get_arguments

HOST = os.environ.get('ELEPHANT_SERVER_HOST', '127.0.0.1')
PORT = os.environ.get('ELEPHANT_SERVER_PORT', '5001')

__all__ = [
    'app'
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# https://fastapi.tiangolo.com/tutorial/handling-errors/?h=erro#use-the-requestvalidationerror-body
@app.exception_handler(ErrorHandler)
async def validation_exception_handler(request: Request, exc: ErrorHandler):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(exc.to_dict()),
    )


@app.get('/')
def index():
    return {'elephant': elephant.__version__}


@app.get('/api')
@app.get('/api/{module}')
def route_api(module=''):
    """ Route to list call functions in Elephant or its module.
    """

    calls = do_list_calls(module)
    return calls

class JSONData(BaseModel):
    args: list
    kwargs: dict


@app.get('/api/{module}/{call}')
@app.post('/api/{module}/{call}')
def route_api_call(module, call, json_data:JSONData):
    """ Route to call function in Elephant module.
    """

    response = do_api_call(module, call, json_data)
    return response

class Data(BaseModel):
    response_keys: str | list = "response"
    source: str = ""

@app.post("/exec")
def route_exec(data: Data):
    """Route to execute script in Python.
    """

    response = do_exec(data)
    return response


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
