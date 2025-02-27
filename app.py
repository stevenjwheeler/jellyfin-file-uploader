# Jellyfin File Uploader
# Author: Steven Wheeler
# https://github.com/stevenjwheeler
# Based on the work of Osama Yusuf (https://github.com/Osama-Yusuf)
#
# Source Code available at: https://github.com/stevenjwheeler/jellyfin-file-uploader
# 
# This is an easy-to-use and self-hosted jellyfin media uploader straight to your jellyfin volume folders.
# Upload media using your browser locally or from other devices on your network, or expose it and upload media from anywhere in the world*!
# (*Make sure that the login is enabled and connected to your jellyfin if you want to expose it publically! Not recommended unless you know what you're doing).
# 
# This uploader supports chunk-based file uploads, logging, XSS protection, directory traversal protection and CSRF protection, cleans up after itself, 
# and all with a simple, easy-to-use and self-hosted interface.

import logging
import random
import string
import threading
from flask import Flask, g
from flask_wtf.csrf import CSRFProtect

# Import components
from components.configuration import VERSION, FLASK_SECRET_KEY
from components.routes import routes
from components.stale_cleanup import periodic_cleanup

# Initialise the app
app = Flask(__name__)
app.config.from_object('components.configuration')
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
app.config['PROPAGATE_EXCEPTIONS'] = False
csrf = CSRFProtect(app)

app.register_blueprint(routes)

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
