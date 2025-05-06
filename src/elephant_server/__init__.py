from importlib import metadata as _metadata # noqa

__version__ = _metadata.version("elephant-server")
del _metadata