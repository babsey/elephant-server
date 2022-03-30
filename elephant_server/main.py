#!/usr/bin/env python3

from functools import wraps
from http import HTTPStatus
import importlib
import os

import elephant
from flask import Flask, request, jsonify, abort
from flask_cors import CORS, cross_origin

# local imports
from .serialize import deserialize, serialize, Units
from .exceptions import *

HOST = os.environ.get('ELEPHANT_SERVER_HOST', '127.0.0.1')
PORT = os.environ.get('ELEPHANT_SERVER_PORT', '5000')

__all__ = [
    'app'
]

app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def index():
    return jsonify({'elephant': elephant.__version__})


# --------------------------
# RESTful API
# --------------------------

@app.route('/api', methods=['GET'])
@app.route('/api/<module>', methods=['GET'])
@cross_origin()
def route_api(module=''):
    """ Route to list call functions in Elephant or its module.
    """
    if module:
        module = importlib.import_module(f"elephant.{module}")
    else:
        module = elephant
    # TODO: calls = module.__all__
    calls = dir(module)
    calls = list(filter(lambda x: not x.startswith('_'), calls))
    calls.sort()
    return jsonify(calls)


def on_error_handler(func):
    """
    Elephant-related errors handler.
    For Flask internal errors, `@app.errorhandler(<code>)` should be used.
    """
    @wraps(func)
    def func_wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ElephantError as error:
            return abort(HTTPStatus.BAD_REQUEST, description=repr(error))
        except Exception as error:
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR,
                         description=repr(error))

    return func_wrapped


@app.route('/api/<module>/<call>', methods=['GET', 'POST'])
@cross_origin()
@on_error_handler
def route_api_call(module, call):
    """ Route to call function in Elephant module.
    """
    # We don't allow storing the main payload in request.args (the part in the
    # URL after the question mark), which may serve useful in the future as
    # custom flag options.
    # We also don't consider request.files and request.form
    # Flask.request object explained:
    #   https://stackoverflow.com/a/16664376/2840134
    # TODO Q: Do clients (NEST D., Insite) send forms?

    # get module function
    try:
        module = importlib.import_module(f"elephant.{module}")
        call = getattr(module, call)
    except (ModuleNotFoundError, AttributeError) as error:
        raise InvalidRequest(repr(error))

    # deserialize request data
    json_data = request.get_json()
    try:
        units_dict = json_data.get("units", {})
        units = Units(**units_dict)
        call_dict = deserialize(json_data)
    except Exception as error:
        raise DeserializeError(repr(error))

    # compute request
    try:
        if 'spiketrain' in call.__code__.co_varnames and 'spiketrains' in call_dict.keys():
            result = [call(spiketrain) for spiketrain in call_dict['spiketrains']]
        else:
            result = call(**call_dict)
    except Exception as error:
        raise ElephantRuntimeError(repr(error))

    # serialize result to lists and dicts for JSON
    try:
        response = serialize(result, units=units)
    except Exception as error:
        raise SerializeError(repr(error))

    return jsonify(response)


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
