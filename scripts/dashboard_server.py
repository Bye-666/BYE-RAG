"""Simple web dashboard for RAG system monitoring."""

from flask import Flask, render_template, jsonify
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.app import Dashboard

app = Flask(__name__)
dashboard = Dashboard()


@app.route('/')
def index():
    """Dashboard home page."""
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics."""
    stats = dashboard.get_stats()
    return jsonify(stats)


@app.route('/api/queries')
def get_queries():
    """Get recent queries."""
    limit = 20
    queries = dashboard.get_recent_queries(limit=limit)
    return jsonify(queries)


@app.route('/api/ingestions')
def get_ingestions():
    """Get recent ingestions."""
    limit = 20
    ingestions = dashboard.get_recent_ingestions(limit=limit)
    return jsonify(ingestions)


if __name__ == '__main__':
    print("=" * 60)
    print("RAG Dashboard Starting...")
    print("=" * 60)
    print("")
    print("Open in browser: http://localhost:5000")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)
