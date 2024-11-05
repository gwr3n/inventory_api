from flask import Flask, request, jsonify
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

@app.route('/fibonacci', methods=['POST','GET'])
def get_fibonacci():
    data = request.get_json()
    n = data.get('n')
    if n is None or not isinstance(n, int) or n < 0:
        return jsonify({'error': 'Invalid input. Please provide a non-negative integer.'}), 400
    result = fibonacci(n)
    return jsonify({'n': n, 'fibonacci': result})
