from flask import Flask, request, Response, jsonify
from flask_cors import CORS # https://github.com/corydolphin/flask-cors

import time

from sdp import StochasticLotSizing
from RS_shortest_path import RS_DP

# https://osxdaily.com/2017/01/30/curl-post-request-command-line-syntax/

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/ss', methods=['POST'])
def solve_ss():
    instance = request.get_json()
    lot_sizing = StochasticLotSizing(**instance)
    i = 0   #initial inventory level
    start_time = time.time()
    result = lot_sizing.solve()
    end_time = time.time() - start_time
    return jsonify({'optCost': result["Cn"][i], 'solTime': round(end_time, 2),'s': result["s"], 'S': result["S"]})

@app.route('/ss_dp', methods=['POST'])
def solve_ss_dp():
    instance = request.get_json()
    ww = RS_DP(**instance)
    start_time = time.time()
    # optCost = ww.optimal_cost()
    end_time = time.time() - start_time
    res = ww.reorder_points(instance)
    simCost = round(ww.simulate_sS(res["s"],res["S"],0),2)
    return jsonify({'optCost': simCost, 'solTime': round(end_time, 2),'s': res["s"], 'S': res["S"]})