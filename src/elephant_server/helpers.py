#!/usr/bin/env python
# helpers.py

import RestrictedPython # noqa
import importlib # noqa

import elephant # noqa

from .exceptions import call_or_error
from .logger import logger
from .serialize import Units, deserialize_data, serialize_data
from .utils import (
    Capturing,
    clean_code,
    get_boolean_environ,
    get_modules_from_env,
    get_restricted_globals,
)


RESTRICTION_DISABLED = get_boolean_environ("ELEPHANT_SERVER_DISABLE_RESTRICTION")

if RESTRICTION_DISABLED:
    msg = "Elephant Server runs without a RestrictedPython trusted environment."
    print(f"***\n*** WARNING: {msg}\n***")


def do_api_call(module, call, json_data):
    logger.debug("Do api call")
    # get module function
    call = do_get_function(module, call)

    # deserialize request data
    units_dict = json_data.get("units", {})
    units = Units(**units_dict)
    call_dict = deserialize_data(json_data)

    # compute request
    if "spiketrain" in call.__code__.co_varnames and "spiketrains" in call_dict.keys():
        data = [call_or_error(call)(spiketrain) for spiketrain in call_dict["spiketrains"]]
    else:
        data = call_or_error(call)(**call_dict)

    # serialize data to lists and dicts for JSON
    response = serialize_data(data, units=units)
    return response


def do_exec(request):
    logger.debug('Do exec')
    if len(request.source) == 0: return
    source_cleaned = clean_code(request.source)

    locals_ = dict()
    response = dict()
    if RESTRICTION_DISABLED:
        with Capturing() as stdout:
            globals_ = globals().copy()
            globals_.update(get_modules_from_env())
            call_or_error(exec)(source_cleaned, globals_, locals_)
        if len(stdout) > 0:
            response["stdout"] = "\n".join(stdout)
    else:
        code = RestrictedPython.compile_restricted(source_cleaned, "<inline>", "exec")  # noqa
        globals_ = get_restricted_globals()
        globals_.update(get_modules_from_env())
        call_or_error(exec)(code, globals_, locals_)
        if "_print" in locals_:
            response["stdout"] = "".join(locals_["_print"].txt)

    if request.response_keys:
        if isinstance(request.response_keys, list):
            data = dict()
            for key in request.response_keys:
                data[key] = locals_.get(key, None)
        else:
            data = locals_.get(request.response_keys, None)
        response["data"] = serialize_data(data)
    return response


@call_or_error
def do_get_function(module, call):
    module = importlib.import_module(f"elephant.{module}")
    return getattr(module, call)


def do_list_calls(module):
    if module:
        module = importlib.import_module(f"elephant.{module}")
    else:
        module = elephant
    # TODO: calls = module.__all__
    calls = dir(module)
    calls = list(filter(lambda x: not x.startswith("_"), calls))
    calls.sort()

    return calls
