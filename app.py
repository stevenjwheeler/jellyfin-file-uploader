import logging
import random
import string
import threading
from flask import Flask, g
from flask_wtf.csrf import CSRFProtect

from components.configuration import FLASK_SECRET_KEY, VERSION
from components.routes import home, upload_chunk
from components.stale_cleanup import periodic_cleanup

# Initialise the app
app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
app.config['PROPAGATE_EXCEPTIONS'] = False
csrf = CSRFProtect(app)

# Register routes from components/routes.py
app.add_url_rule('/', 'home', home)
app.add_url_rule('/upload_chunk', 'upload_chunk', upload_chunk, methods=['POST'])

# Generate nonce for CSRF protection
def generate_nonce(length=16): 
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# CSRF protection
@app.before_request
def before_request(): 
    """
    Generates a random nonce and stores it in the Flask g object before each request.
    """
    g.nonce = generate_nonce()

# Security headers
@app.after_request 
def add_security_headers(response): 
    """
    Adds security headers to the HTTP response to enhance the security of the application.
    """
    nonce_value = getattr(g, 'nonce', None)

    response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubdomains' 
    response.headers['X-Content-Type-Options'] = 'nosniff' 
    response.headers['X-Frame-Options'] = 'DENY' 
    response.headers['X-XSS-Protection'] = '1; mode=block' 
    response.headers['Content-Security-Policy'] = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce_value}'; "
        f"style-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'nonce-{nonce_value}'; "
        f"font-src https://cdnjs.cloudflare.com; "
        "img-src 'self'; "
        "media-src 'self';"
    )
    response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

# Run the app
if __name__ == '__main__':
    logging.info("Application starting up...")
    logging.info("Version %s", VERSION)
    # Start a background thread for periodic cleanup
    logging.info("Starting periodic cleanup in the background.")
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    # Start the Flask app
    logging.info("Starting the web server.")
    app.run(debug=False, host='0.0.0.0', port=5005)
