from importlib import metadata # noqa

try:
    __version__ = metadata.version("elephant-server")
    del metadata
except:
    pass
