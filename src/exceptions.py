class ElephantError(Exception):
    pass


class InvalidRequest(ElephantError):
    pass


class DeserializeError(InvalidRequest):
    pass


class ElephantRuntimeError(ElephantError):
    pass


class SerializeError(ElephantError):
    pass
