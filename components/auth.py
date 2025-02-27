import logging
import requests
from flask import current_app

def authenticate_user(username, password):
    jellyfin_server = current_app.config['JELLYFIN_SERVER_ADDRESS'].rstrip('/')
    auth_endpoint = current_app.config['JELLYFIN_AUTH_ENDPOINT']
    
    logging.info(f"Authenticating user \"{username}\" with Jellyfin server at {jellyfin_server}.")

    try:
        # Authenticate with Jellyfin server
        payload = {
            'Username': username,
            'Pw': password
        }
        authorization = (
            'MediaBrowser , '
            'Client="other", '
            'Device="script", '
            'DeviceId="script", '
            'Version="0.0.0"'
        )
        headers = {
            'Content-Type': 'application/json',
            'x-emby-authorization': authorization
        }
        
        response = requests.post(f'{jellyfin_server}{auth_endpoint}', json=payload, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            logging.info(f"Failed to authenticate user \"{username}\" with Jellyfin server: Server rejected credentials.")
            return None
        else:
            logging.error(f"Failed to authenticate with Jellyfin server: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to Jellyfin server: {e}")
        return None