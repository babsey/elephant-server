import flask
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

import inspect

from werkzeug.exceptions import abort
from werkzeug.wrappers import Response

import elephant
import neo
import numpy as np
import quantities as pq


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
        calls = dir(getattr(elephant, module))
    else:
        calls = dir(elephant)
    calls = list(filter(lambda x: not x.startswith('_'), calls))
    calls.sort()
    return jsonify(calls)


@app.route('/api/<module>/<call>', methods=['GET', 'POST'])
@cross_origin()
def route_api_call(module, call):
    """ Route to call function in Elephant module.
    """
    args, kwargs = get_arguments(request)
    call = getattr(getattr(elephant, module), call)
    response = api_client(call, args, kwargs)
    return jsonify(response)


# ----------------------
# Helpers for the server
# ----------------------

def get_arguments(request):
    """ Get arguments from the request.
    """
    args, kwargs = [], {}
    if request.is_json:
        json = request.get_json()
        if isinstance(json, list):
            args = json
        elif isinstance(json, dict):
            kwargs = json
            if 'args' in kwargs:
                args = kwargs.pop('args')
    elif len(request.form) > 0:
        if 'args' in request.form:
            args = request.form.getlist('args')
        else:
            kwargs = request.form.to_dict()
    elif len(request.args) > 0:
        if 'args' in request.args:
            args = request.args.getlist('args')
        else:
            kwargs = request.args.to_dict()
    return list(args), kwargs


def get_or_error(func):
    """ Wrapper to get data and status.
    """
    def func_wrapper(call, args, kwargs):
        try:
            return func(call, args, kwargs)
        except Exception as e:
            abort(Response(str(e), 400))
    return func_wrapper


def to_spike_train(arg):
    if isinstance(arg, (list,tuple)):
        try:
            return neo.SpikeTrain(*arg)
        except:
            return np.array(arg)
    elif isinstance(arg, dict):
        return neo.SpikeTrain(**arg)


def to_analog_signal(arg):
    if isinstance(arg, (list,tuple)):
        return neo.AnalogSignal(*arg)
    elif isinstance(arg, dict):
        return neo.AnalogSignal(**arg)


def serialize(call, args, kwargs):
    """ Serialize arguments with keywords for call functions in Elephant.
    """
    paramKeys = list(inspect.signature(call).parameters.keys())

    for (idx, arg) in enumerate(args):
        if paramKeys[idx] == 'signal':
            args[idx] = to_analog_signal(arg)
        elif paramKeys[idx] == 'spiketrain':
            args[idx] = to_spike_train(arg)
        elif paramKeys[idx] == 'spiketrains':
            args[idx] = [to_spike_train(a) for a in arg]
        elif paramKeys[idx] in ['binsize', 't_start', 't_stop']:
            args[idx] = arg['value'] * getattr(pq, arg['unit'])

    for (key, value) in kwargs.items():
        if key == 'signal':
            kwargs[key] = to_analog_signal(value)
        if key == 'spiketrain':
            kwargs[key] = to_spike_train(value)
        elif key == 'spiketrains':
            kwargs[key] = [to_spike_train(v) for v in value]
        elif key in ['binsize', 't_start', 't_stop']:
            kwargs[key] = value['value'] * getattr(pq, value['unit'])
    return args, kwargs


@get_or_error
def api_client(call, args, kwargs):
    """ API Client to call function in Elephant.
    """
    if callable(call):
        if 'inspect' in kwargs:
            response = {
                'data': getattr(inspect, kwargs['inspect'])(call)
            }
        else:
            args, kwargs = serialize(call, args, kwargs)
            response = call(*args, **kwargs).data.tolist()
    else:
        response = call
    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
