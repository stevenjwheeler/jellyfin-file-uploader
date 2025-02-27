import logging
import os
import sys
import requests
from dotenv import load_dotenv

# Set the version
VERSION = 3.0

# Load environment variables from the .env file if it exists, if it doesn't then exit
load_dotenv()

# List of required environment variables
required_env_vars = [
    'FLASK_SECRET_KEY',
    'ALLOWED_EXTENSIONS',
]

# Check if the required environment variables are set, exit if not
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}.\nPlease consult the provided .env file or the documentation for more information.")
    sys.exit(1)

# Retrieve required environment variables
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
ALLOWED_EXTENSIONS = os.environ.get('ALLOWED_EXTENSIONS')
# Retrieve or set default on optional variables
ALLOWED_EXTENSIONS = set(ALLOWED_EXTENSIONS.split(','))
DOWNLOADS_PATH = os.environ.get('DOWNLOADS_PATH', './downloads')  # ./downloads default
TEMP_CHUNKS_PATH = os.environ.get('TEMP_CHUNKS_PATH', './temp_chunks')  # ./temp_chunks default
CONTENT_MAX = int(os.environ.get('MAX_CONTENT_LENGTH', 20))  # 20 GB default
FILE_MAX = int(os.environ.get('MAX_FILE_SIZE', 5))  # 5 GB default
STALE_FILE_THRESHOLD = int(os.environ.get('STALE_FILE_THRESHOLD', 86400))  # 24 hours default
LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', 'INFO').upper()

# Set the logging level
log_level = getattr(logging, LOGGING_LEVEL, logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Logs to console
        logging.FileHandler('app.log')  # Logs to file 'app.log'
    ]
)

# Login settings
LOGIN_ENABLED = os.environ.get('LOGIN_ENABLED', "true").lower() in ['true', '1', 't', 'y', 'yes']
if LOGIN_ENABLED:
    JELLYFIN_SERVER_ADDRESS = os.environ.get('JELLYFIN_SERVER_ADDRESS', "http://localhost:8096")
    JELLYFIN_AUTH_ENDPOINT = '/Users/AuthenticateByName'
    logging.info(f"Login system is enabled. Logins are being authenticated against {JELLYFIN_SERVER_ADDRESS}.")

    # Check if the Jellyfin server is reachable
    try:
        response = requests.get(JELLYFIN_SERVER_ADDRESS)
        if response.status_code == 200:
            logging.info(f"Successfully connected to Jellyfin server at {JELLYFIN_SERVER_ADDRESS}.")
            pass
        else:
            logging.error(f"Failed to reach Jellyfin server at {JELLYFIN_SERVER_ADDRESS}. Status code: {response.status_code}. Logins will not work, thus the application will exit.")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to Jellyfin server at {JELLYFIN_SERVER_ADDRESS}: {e}")
        sys.exit(1)

else:
    logging.info(f"Login system is DISABLED. This is NOT recommended unless you have alternative security measures in place to prevent anyone from uploading to your server.")