"""
Simple Flask server to serve the SEO landing page.
Run this alongside your Telegram bot to make the landing page live.
"""
import os
from flask import Flask, send_from_directory, abort
from flask_cors import CORS

app = Flask(__name__, static_folder='public')
CORS(app)

# Serve main page
@app.route('/')
def home():
    """Serve the landing page."""
    return send_from_directory('public', 'index.html')

# Serve CSS files
@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files."""
    return send_from_directory('public/css', filename)

# Serve JS files
@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files."""
    return send_from_directory('public/js', filename)

# Serve static files (images, icons, etc.)
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    try:
        return send_from_directory('public', filename)
    except:
        abort(404)

# Health check endpoint
@app.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'ok', 'service': 'meetgrid-landing-page'}, 200

# Error handlers
@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return send_from_directory('public', 'index.html')

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return {'error': 'Internal server error'}, 500

if __name__ == '__main__':
    # Get port from environment or use 8080
    port = int(os.environ.get('PORT', 8080))
    
    print(f"🌐 Starting MeetGrid Landing Page Server...")
    print(f"🚀 Server running on http://localhost:{port}")
    print(f"📱 Open in browser: http://localhost:{port}")
    print(f"🛑 Press Ctrl+C to stop\n")
    
    # Run the server
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,  # Set to True for development
        threaded=True
    )
