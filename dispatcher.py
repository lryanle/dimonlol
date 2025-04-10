from flask import Flask, redirect, render_template, request, jsonify
from functools import wraps
from collections import defaultdict
from flask_cors import CORS
from threading import Lock
import time
import db

app = Flask(__name__)
CORS(app)

class RequestCoalescer:
    def __init__(self, timeout=0.5):
        self.pending_requests = defaultdict(list)
        self.results = {}
        self.lock = Lock()
        self.timeout = timeout

    def coalesce(self, key, operation):
        current_time = time.time()
        
        with self.lock:
            # Check if there's a recent result we can use
            if key in self.results:
                result_time, result = self.results[key]
                if current_time - result_time < self.timeout:
                    return result

            # Wait if there are pending requests
            if key in self.pending_requests:
                future = []
                self.pending_requests[key].append(future)
                return self._wait_for_result(future)

            # This is the first request, execute it
            self.pending_requests[key] = []
            result = operation()
            
            # Store result and notify other waiting requests
            self.results[key] = (current_time, result)
            pending = self.pending_requests[key]
            del self.pending_requests[key]
            
            for future in pending:
                future.append(result)
            
            return result

    def _wait_for_result(self, future):
        while not future:
            time.sleep(0.01)
        return future[0]

coalescer = RequestCoalescer()

# Decorator for coalescing requests
def coalesce_requests(key_func):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            key = key_func(*args, **kwargs)
            return coalescer.coalesce(key, lambda: f(*args, **kwargs))
        return wrapped
    return decorator

# API endpoints

# /search?q=%s
@app.route('/search', methods=['GET'])
@coalesce_requests(lambda: f"search_{request.args.get('q')}")
def search():
    query = request.args.get('q')
    if not query:
        aliases = db.get_all_aliases()
        return jsonify({'aliases': aliases, 'message': 'No query specified; returning all aliases'})
    
    search_result = db.read_alias(query)
    print(f"redirecting '{query}' to '{search_result}'")
    return redirect(search_result)

@app.route('/alias', methods=['POST'])
@coalesce_requests(lambda: f"add_alias_{request.json.get('alias')}")
def add_alias():
    data = request.json
    success, message = db.add_alias(data['alias'], data['pattern'])
    return jsonify({'success': success, 'message': message})

@app.route('/alias/<int:id>', methods=['DELETE'])
@coalesce_requests(lambda id: f"remove_alias_{id}")
def remove_alias(id):
    success, message = db.remove_alias(id)
    return jsonify({'success': success, 'message': message})

@app.route('/alias/<int:id>', methods=['PUT'])
@coalesce_requests(lambda id: f"update_alias_{id}_{request.json}")
def update_alias(id):
    data = request.json
    success, message = db.update_alias(
        id,
        alias=data.get('alias'),
        pattern=data.get('pattern')
    )
    return jsonify({'success': success, 'message': message})


@app.route('/admin')
def admin_page():
    return render_template('admin.html')

# Error handling
@app.errorhandler(Exception)
def handle_error(error):
    return jsonify({'error': str(error)}), 500

if __name__ == '__main__':
    db.create_alias_table()
    app.run(debug=True)