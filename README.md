# Elephant Server

A Flask server for [Elephant](https://github.com/NeuralEnsemble/elephant) (Electrophysiology Analysis Toolkit).


The API server provides a direct access to Elephant functionalities through GET/POST requests.

The basic functional of the request url to Elephant Server is `<hostname>/api/<module>/<call>`


### Installation

Clone working copy from github repository.

```
git clone https://github.com/babsey/elephant-server
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

### Demo

Once you started the elephant server, run demo notebook with

```
jupyter notebook demo.ipynb
```

### Quick test

Using curl in bash
```
curl localhost:5000/api/<module>/<call>
```

E.g. To see a list of calls in statistics module
```
curl localhost:5000/api/statistics
```
