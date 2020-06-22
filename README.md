# Elephant Server
A server for Elephant (Electrophysiology Analysis Toolkit)


The API server provides a direct access to Elephant functionalities through GET/POST requests.

The basic functional of the request url to Elephant Server is `<hostname>/api/<module>/<call>`


For more information of the Elephant: https://github.com/NeuralEnsemble/elephant

### Installation

Clone working copy from github repository.

```
git clone https://github.com/INM-6/elephant-server
cd elephant-server
```

Install requirements for running elephant server on host
```
pip3 install -r requirements.txt
```


### Start

Starting the server on host system
```
python3 elephant_server/main.py
```

Or start with Docker
```
docker run -i -p 5000:5000 -t elephant-server
```

### Usage

Using curl in bash
```
curl localhost:5000/api/<module>/<call>
```

E.g. To see a list of calls in statistucs module
```
curl localhost:5000/api/statistics
```

Using requests in Python (`ipython`)
```
import requests
requests.post('http://localhost:5000/api/statistics/isi', json={'spiketrain': [1,2,4,7,11]}).json()
```

Use ElephantClientAPI object in Python (`ipython`)
```
from ElephantServerClient.ElephantServerClient import ElephantClientAPI
elapi = ElephantClientAPI()
elapi.statistics.isi(spiketrain=[1,2,4,7,11]) # or elapi.statistics.isi([1,2,4,7,11])
```
