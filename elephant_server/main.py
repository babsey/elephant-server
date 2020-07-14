import importlib
from functools import wraps
from http import HTTPStatus

import elephant
from flask import Flask, request, jsonify, abort
from flask_cors import CORS, cross_origin

from elephant_server.serialize import deserialize, serialize, Units
from elephant_server.exceptions import *

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

    # get function
    try:
        module = importlib.import_module(f"elephant.{module}")
        call = getattr(module, call)
    except (ModuleNotFoundError, AttributeError) as error:
        raise InvalidRequest(repr(error))

    # get function kwargs
    json_data = request.get_json()
    try:
        units_dict = json_data.get("units", {})
        units = Units(**units_dict)
        call_dict = deserialize(json_data)
    except Exception as error:
        raise DeserializeError(repr(error))

    # compute the result
    try:
        result = call(**call_dict)
    except Exception as error:
        raise ElephantRuntimeError(repr(error))

    # serialize to lists and dicts
    try:
        response = serialize(result, units=units)
    except Exception as error:
        raise SerializeError(repr(error))

    return jsonify(response)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    # request params example
    # >>> dict(kwargs=dict(spiketrain=[1, 1.5, 2.7], bin_size=3, t_start=0), units=('ms', 'mV'))
    # {'data': {'bin_size': 3,
    #             'spiketrain': [1, 1.5, 2.7],
    #             't_start': 0,
    #  'units': {'time': 'ms', 'volt': 'mV'}
    #  'chunk_id' : 2
    #  }
    # *signal[s]
    # *spiketrain[s]
    # *units
    # *bin_size
    # *t_start
    # *t_stop

