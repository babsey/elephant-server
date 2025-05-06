#!/usr/bin/env python
# utils.py

import ast
import importlib
import io
import os
import re
import sys
import time

import RestrictedPython

MODULES = os.environ.get(
    "ELEPHANT_SERVER_MODULES",
    ";".join(
        [
            "import numpy as np",
            "import elephant",
            "import neo",
            "import quantities as pq",
            "import pandas as pd",
        ]
    ),
)


class Capturing(list):
    """Monitor stdout contents i.e. print."""

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = io.StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


def clean_code(source):
    codes = re.split("\n|; ", source)
    codes_cleaned = []  # noqa
    for code in codes:
        if code.startswith("import") or code.startswith("from"):
            codes_cleaned.append("#" + code)
        else:
            codes_cleaned.append(code)
    return "\n".join(codes_cleaned)


def get_arguments(request):
    """Get arguments from the request."""
    kwargs = {}
    if request.is_json:
        json = request.get_json()
        if isinstance(json, dict):
            kwargs = json
        # else: TODO: Error

    elif len(request.form) > 0:
        kwargs = request.form.to_dict()
    elif len(request.args) > 0:
        kwargs = request.args.to_dict()
    return kwargs


def get_boolean_environ(env_key, default_value="false"):
    env_value = os.environ.get(env_key, default_value)
    return env_value.lower() in ["yes", "true", "t", "1"]


def get_modules_from_env():
    """Get modules from environment variable ELEPHANT_SERVER_MODULES.

    This function converts the content of the environment variable  ELEPHANT_SERVER_MODULES:
    to a formatted dictionary for updating the Python `globals`.

    Here is an example:
        ` ELEPHANT_SERVER_MODULES="import elephant; import numpy as np; from numpy import random"`
    is converted to the following dictionary:
        `{'elephant': <module 'elephant'> 'np': <module 'numpy'>, 'random': <module 'numpy.random'>}`
    """
    modules = {}
    try:
        parsed = ast.iter_child_nodes(ast.parse(MODULES))
    except (SyntaxError, ValueError):
        raise SyntaxError(
            "The Elephant server module environment variables contains syntax errors."
        )
    for node in parsed:
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules[alias.asname or alias.name] = importlib.import_module(alias.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                modules[alias.asname or alias.name] = importlib.import_module(f"{node.module}.{alias.name}")
    return modules


def get_restricted_globals():
    """Get restricted globals for exec function."""

    def getitem(obj, index):
        typelist = (list, tuple, dict)
        if obj is not None and type(obj) in typelist:
            return obj[index]
        msg = f"Error getting restricted globals: unidentified object '{obj}'."
        raise TypeError(msg)

    restricted_builtins = RestrictedPython.safe_builtins.copy()
    restricted_builtins.update(RestrictedPython.limited_builtins)
    restricted_builtins.update(RestrictedPython.utility_builtins)
    restricted_builtins.update(
        dict(
            max=max,
            min=min,
            sum=sum,
            time=time,
        )
    )

    restricted_globals = dict(
        __builtins__=restricted_builtins,
        _print_=RestrictedPython.PrintCollector,
        _getattr_=RestrictedPython.Guards.safer_getattr,
        _getitem_=getitem,
        _getiter_=iter,
        _unpack_sequence_=RestrictedPython.Guards.guarded_unpack_sequence,
        _write_=RestrictedPython.Guards.full_write_guard,
    )

    return restricted_globals
