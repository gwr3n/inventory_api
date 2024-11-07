from flask import Flask, request, Response, jsonify
from flask_cors import CORS # https://github.com/corydolphin/flask-cors

import time

from sdp import StochasticLotSizing
from RS_shortest_path import RS_DP

import signal

class TimeoutException(Exception):
    pass

def deadline(seconds, *args):
    def decorate(f):
        def handler(signum, frame):
            raise TimeoutException("Timed out!")

        def new_f(*args):
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds)
            try:
                return f(*args)
            finally:
                signal.alarm(0)

        new_f.__name__ = f.__name__
        return new_f
    return decorate

# https://osxdaily.com/2017/01/30/curl-post-request-command-line-syntax/

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/ss', methods=['POST'])
@deadline(120)
def solve_ss():
    instance = request.get_json()
    lot_sizing = StochasticLotSizing(**instance)
    i = 0   #initial inventory level
    start_time = time.time()
    result = lot_sizing.solve()
    end_time = time.time() - start_time
    return jsonify({'optCost': result["Cn"][i], 'solTime': round(end_time, 2),'s': result["s"], 'S': result["S"]})

@app.route('/ss_dp', methods=['POST'])
@deadline(120)
def solve_ss_dp():
    instance = request.get_json()
    ww = RS_DP(**instance)
    # optCost = ww.optimal_cost()
    start_time = time.time()
    res = ww.reorder_points(instance)
    end_time = time.time() - start_time
    simCost = round(ww.simulate_sS(res["s"],res["S"],0),2)
    return jsonify({'optCost': simCost, 'solTime': round(end_time, 2),'s': res["s"], 'S': res["S"]})

