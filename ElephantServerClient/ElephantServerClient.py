import requests
from werkzeug.exceptions import BadRequest


__all__ = [
    'ElephantClientAPI',
]


def encode(response):
    if response.ok:
        return response.json()
    elif response.status_code == 400:
        raise BadRequest(response.text)


class ElephantClientAPI(object):

    def __init__(self, host='localhost', port=5000, module=''):
        self.host = host
        self.port = port
        self.module = module
        self.headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    def _elephant_api_call(self, call, params={}):
        hostname = f"http://{self.host}:{self.port}/api"
        url = '/'.join([hostname, self.module, call])
        response = requests.post(url, json=params, headers=self.headers)
        return encode(response)

    def __getattr__(self, name):
        if self.module == '':
            return self._module(name)
        else:
            def method(*args, **kwargs):
                kwargs.update({'args': args})
                return self._elephant_api_call(name, kwargs)
            return method

    @classmethod
    def _module(cls, name):
        return cls(module=name)
