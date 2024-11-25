import requests
from werkzeug.exceptions import BadRequest

def encode(response):
    if response.ok:
        return response.json()
    elif response.status_code == 400:
        print(response.text)


class ElephantClientAPI(object):

    def __init__(self, url='http://localhost:5000', module='',
                headers={'Content-type': 'application/json', 'Accept': 'text/plain'}):
        self.url = url
        self.module = module
        self.headers = headers

    def _elephant_api_call(self, call, params={}):
        hostname = f"{self.url}/api"
        url = '/'.join([hostname, self.module, call])
        response = requests.post(url, json=params, headers=self.headers)
        return encode(response)

    def __getattr__(self, name):
        if self.module == '':
            return self._module(name)
        else:
            def method(*args, **kwargs):
                return self._elephant_api_call(name, kwargs)
            return method

    @classmethod
    def _module(cls, name):
        return cls(module=name)