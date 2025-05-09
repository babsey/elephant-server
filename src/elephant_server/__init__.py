from importlib import metadata # noqa

try:
    __version__ = metadata.version("elephant-server")
except metadata.PackageNotFoundError:
    pass

del metadata
