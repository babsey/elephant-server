import inspect

import flask
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

from werkzeug.exceptions import abort
from werkzeug.wrappers import Response

import elephant
import numpy as np
import quantities as pq


__all__ = [
    'app'
]


# Blacklist of modules according to Bandit (https://bandit.readthedocs.io).
_blacklist_modules = [
    'commands',
    'dsa',
    'jinja2',
    'mako',
    'os',
    'paramiko',
    'popen2',
    'requests',
    'rsa',
    'socket',
    'ssl',
    'subprocess',
    'sys',
]


app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def index():
    return jsonify({'elephant': elephant.__version__})


@app.route('/exec', methods=['GET', 'POST'])
@cross_origin()
def route_exec():
    """ Route to execute script in Python.
    """
    try:
        args, kwargs = get_arguments(request)
        source_code = kwargs.get('source', '')
        source_cleaned = clean_code(source_code)
        byte_code = compile_restricted(source_cleaned, '<inline>', 'exec')
        locals = get_modules(source_code)
        with Capturing() as stdout:
            exec(byte_code, safe_globals, locals)
        response = {
            'stdout': '\n'.join(stdout),
        }
        if 'return' in kwargs:
            if isinstance(kwargs['return'], list):
                data = {}
                for variable in kwargs['return']:
                    data[variable] = locals.get(variable, None)
            else:
                data = locals.get(kwargs['return'], None)
            response['data'] = serializable(data)
        return jsonify(response)
    except Exception as e:
        abort(Response(str(e), 400))

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

class Capturing(list):
    """ Monitor stdout contents i.e. print.
    """
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = io.StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout


def clean_code(source):
    codes = source.split('\n')
    code_cleaned = filter(lambda code: not (code.startswith('import') or code.startswith('from')), codes)
    return '\n'.join(code_cleaned)


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


def get_modules(source):
    modules = {'nest': nest}
    for line in source.split('\n'):
        code = line.split(' ')
        if code[0] == 'import' and code[1] not in _blacklist_modules:
            modules.update({code[-1]: importlib.import_module(code[1])})
    return modules


def get_or_error(func):
    """ Wrapper to get data and status.
    """
    def func_wrapper(call, args, kwargs):
        try:
            return func(call, args, kwargs)
        except Exception as e:
            abort(Response(str(e), 400))
    return func_wrapper


def SpikeTrain(arg):
    if isinstance(arg, (list,tuple)):
        try:
            return elephant.statistics.SpikeTrain(*arg)
        except:
            return np.array(arg)
    elif isinstance(arg, dict):
        return elephant.statistics.SpikeTrain(**arg)


def serialize(call, args, kwargs):
    """ Serialize arguments with keywords for call functions in Elephant.
    """
    paramKeys = list(inspect.signature(call).parameters.keys())

    for (idx, arg) in enumerate(args):
        if paramKeys[idx] == 'spiketrain':
            args[idx] = SpikeTrain(arg)
        elif paramKeys[idx] == 'spiketrains':
            args[idx] = [SpikeTrain(a) for a in arg]
        elif paramKeys[idx] in ['binsize', 't_start', 't_stop']:
            args[idx] = arg['value'] * getattr(pq, arg['unit'])

    for (key, value) in kwargs.items():
        if key == 'spiketrain':
            kwargs[key] = SpikeTrain(value)
        elif key == 'spiketrains':
            kwargs[key] = [SpikeTrain(v) for v in value]
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
