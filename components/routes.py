import os
from flask import current_app, render_template, g, request, redirect, url_for, session, flash, Blueprint, jsonify
from flask_wtf import FlaskForm
import logging

from components.chunk_handler import handle_upload_chunk
from components.auth import authenticate_user
from components.configuration import DOWNLOADS_PATH, VERSION, ALLOWED_EXTENSIONS, FILE_MAX, CONTENT_MAX, JELLYFIN_SERVER_ADDRESS

routes = Blueprint('routes', __name__)

@routes.route('/')
def home():
    if current_app.config['LOGIN_ENABLED'] and 'user_id' not in session:
        return redirect(url_for('routes.login'))
    directories = [d for d in os.listdir(DOWNLOADS_PATH) if os.path.isdir(os.path.join(DOWNLOADS_PATH, d))]
    return render_template('index.html', nonce=g.nonce, directories=directories, FILE_TYPES=ALLOWED_EXTENSIONS, FILE_MAX=FILE_MAX, CONTENT_MAX=CONTENT_MAX, VERSION=VERSION, LOGIN_ENABLED=current_app.config['LOGIN_ENABLED'])

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if not current_app.config['LOGIN_ENABLED']:
        return redirect(url_for('routes.home'))

    form = FlaskForm()
    if request.method == 'POST' and form.validate_on_submit():
        username = request.form['username']
        password = request.form['password']
        user_ip = request.remote_addr
        
        # Authenticate with Jellyfin server
        data = authenticate_user(username, password)
        
        if data:
            session['user_id'] = data['User']['Id']
            session['access_token'] = data['AccessToken']
            logging.info(f"User \"{username}\" logged in successfully from IP {user_ip}.")
            return jsonify(success=True, redirect_url=url_for('routes.home'))
        else:
            logging.warning(f"Failed login attempt for user \"{username}\" from IP {user_ip}.")
            return jsonify(success=False, message='Invalid username or password'), 401
    
    return render_template('login.html', form=form, VERSION=VERSION, SERVER=JELLYFIN_SERVER_ADDRESS)

@routes.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('routes.login'))

@routes.route('/upload_chunk', methods=['POST'])
def upload_chunk():
    if current_app.config['LOGIN_ENABLED'] and 'user_id' not in session:
        return redirect(url_for('routes.login'))
    
    return handle_upload_chunk(request)
