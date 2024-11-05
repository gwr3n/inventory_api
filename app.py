from flask import Flask, request, jsonify
from typing import List
import scipy.stats as sp
import time

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World! (2)'

def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

@app.route('/fibonacci', methods=['POST'])
def get_fibonacci():
    data = request.get_json()
    n = data.get('n')
    if n is None or not isinstance(n, int) or n < 0:
        return jsonify({'error': 'Invalid input. Please provide a non-negative integer.'}), 400
    result = fibonacci(n)
    return jsonify({'n': n, 'fibonacci': result})

class StochasticLotSizing:
    """
    The nonstationary stochastic lot sizing problem.

    Herbert E. Scarf. Optimality of (s, S) policies in the dynamic inventory problem. In K. J. Arrow,
    S. Karlin, and P. Suppes, editors, Mathematical Methods in the Social Sciences, pages 196–202.
    Stanford University Press, Stanford, CA, 1960.

    Returns:
        [type] -- A problem instance
    """

    def __init__(self, K: float, h: float, p: float, d: List[float]):
        """
        Create an instance of StochasticLotSizing.
        
        Arguments:
            K {float} -- the fixed ordering cost
            v {float} -- the proportional unit ordering cost
            h {float} -- the proportional unit inventory holding cost
            p {float} -- the proportional unit inventory penalty cost
            d {List[float]} -- the demand probability mass function 
              taking the form [[d_1,p_1],...,[d_N,p_N]], where d_k is 
              the k-th value in the demand support and p_k is its 
              probability.
            min_inv_level {float} -- the minimum inventory level
            max_inv_level {float} -- the maximum inventory level
            q {float} -- quantile truncation for the demand
            initial_order {bool} -- allow order in the first period
        """
        q = 0.999
        self.max_demand = lambda d: sp.poisson(d).ppf(q).astype(int)         # max demand in the support
        
        # initialize instance variables
        self.T, self.K, self.h, self.p, self.d, self.min_inv_level, self.max_inv_level = len(d), K, h, p, d, -self.max_demand(sum(d)), self.max_demand(sum(d))
        self.pmf = [[sp.poisson(self.d[t]).pmf(k)/q for k in range(0, self.max_demand(self.d[t]) + 1)] for t in range(self.T)] # tabulate pmf

    def solve(self):
        Gn = [0 for _ in range(self.min_inv_level, self.max_inv_level + 1)]
        J_new = [float("inf") for _ in range(self.min_inv_level, self.max_inv_level + 1)]
        J_old = [0.0 for _ in range(self.min_inv_level, self.max_inv_level + 1)]
        s = [float("inf") for _ in range(self.T)]
        S = [float("inf") for _ in range(self.T)]
        min_inv_level, max_inv_level, K, h, p, pmf = self.min_inv_level, self.max_inv_level, self.K, self.h, self.p, self.pmf

        def cost(t, i):
            temp = 0.0
            for d in range(self.max_demand(self.d[t]) + 1):
                if i - d >= max_inv_level:
                    temp = temp + (h * (i - d) + J_old[max_inv_level]) * pmf[t][d]
                if i - d <= self.min_inv_level:
                    temp = temp + (p * (d - i) + J_old[min_inv_level]) * pmf[t][d]
                if 0 < i - d < max_inv_level:
                    temp = temp + (h * (i - d) + J_old[i - d]) * pmf[t][d]
                if min_inv_level < i - d <= 0:
                    temp = temp + (p * (d - i) + J_old[i - d]) * pmf[t][d]
            return temp
        
        for t in range(self.T - 1, -1, -1):        
            i, min_so_far = max_inv_level, float("inf")
            J_new[i] = Gn[i] = cost(t, i)
            while True:
                i = i-1
                J_new[i] = cost(t, i)
                Gn[i] = cost(t, i)
                if cost(t, i) <= min_so_far:
                    min_so_far, S[t] = cost(t, i), i
                if cost(t, i) > min_so_far + K:
                    break
            s[t] = i

            for i in range(min_inv_level, int(s[t] + 1)):
                J_new[i] = cost(t, S[t]) + K 
                if t == 0: # at time 0 we capture Scarf's G function
                    Gn[i] = cost(t, i)

            for i in range(min_inv_level, max_inv_level + 1):
                J_old[i] = J_new[i]
        
        return {"Cn": J_old, "Gn": Gn, "s": s, "S": S}

@app.route('/ss', methods=['POST'])
def solve_ss():
    instance = request.get_json()
    lot_sizing = StochasticLotSizing(**instance)
    i = 0   #initial inventory level
    start_time = time.time()
    result = lot_sizing.solve()
    end_time = time.time() - start_time
    return jsonify({'optCost': result["Cn"][i], 'solTime': round(end_time, 2),'s': result["s"], 'S': result["S"]})