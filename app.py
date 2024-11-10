import random
import string
import os
import logging
import shutil
import sys
from flask import Flask, request, render_template, g
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Set the version
VERSION=2.3

# Load environment variables from the .env file if it exists
load_dotenv()

# Initialise the app
app = Flask(__name__)
csrf = CSRFProtect(app)
app.config['PROPAGATE_EXCEPTIONS'] = False

# Get the FLASK_SECRET_KEY environment variable
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    print("Error: FLASK_SECRET_KEY environment variable not set!")
    sys.exit(1)
else:
    print(f"FLASK_SECRET_KEY loaded")

# Get the ALLOWED_EXTENSIONS environment variable
allowed_extensions = os.environ.get('ALLOWED_EXTENSIONS')
if not allowed_extensions:
    print("Error: ALLOWED_EXTENSIONS environment variable not set!")
    sys.exit(1)
else :
    ALLOWED_EXTENSIONS = set(allowed_extensions.split(','))
    print(f"ALLOWED_EXTENSIONS loaded: {ALLOWED_EXTENSIONS}")

# Get the logging level environment variable
logging_level = os.environ.get('LOGGING_LEVEL')
if not logging_level:
    LOGGING_LEVEL = logging.INFO
    logging_level = "info"
else :
    LOGGING_LEVEL = getattr(logging, logging_level.upper(), logging.INFO)
logging.basicConfig(level=LOGGING_LEVEL)
print(f"LOGGING_LEVEL loaded: {logging_level.upper()}")

# Get the DOWNLOADS_PATH and TEMP_CHUNKS_PATH environment variables
DOWNLOADS_PATH = os.environ.get('DOWNLOADS_PATH', './downloads')
print(f"DOWNLOADS_PATH loaded: {DOWNLOADS_PATH}")
TEMP_CHUNKS_PATH = os.environ.get('TEMP_CHUNKS_PATH', './temp_chunks')
print(f"TEMP_CHUNKS_PATH loaded: {TEMP_CHUNKS_PATH}")

# Get the max content length
CONTENT_MAX = int(os.environ.get('MAX_CONTENT_LENGTH', 20))  # 20 gigabytes default
print(f"MAX_CONTENT_LENGTH loaded: {CONTENT_MAX} GB")

# Get the max file size
FILE_MAX = int(os.environ.get('MAX_FILE_SIZE', 5))  # 5 gigabytes default
print(f"MAX_FILE_SIZE loaded: {FILE_MAX} GB")

def generate_nonce(length=16): 
    """
    Generates a random nonce (a random value that can be used once) with the given length.

    The default length is 16.

    :param length: The length of the nonce to generate.
    :type length: int
    :return: A random nonce with the given length.
    :rtype: str
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length)) 

@app.before_request
def before_request(): 
    """
    Generates a random nonce and stores it in the Flask g object before each request.

    The nonce is used to set the Content-Security-Policy header in the response to prevent
    XSS attacks.
    """
    g.nonce = generate_nonce()

@app.after_request 
def add_security_headers(response): 
    """
    Adds security headers to the HTTP response to enhance the security of the application.

    This function is executed after each request to ensure that the response includes
    various HTTP headers that enforce strict security policies. These headers include:
    - 'Strict-Transport-Security': Enforces the use of HTTPS for a specified duration.
    - 'X-Content-Type-Options': Prevents MIME type sniffing.
    - 'X-Frame-Options': Denies rendering of the page in a frame to protect against clickjacking.
    - 'X-XSS-Protection': Enables the browser's built-in XSS protection.
    - 'Content-Security-Policy': Restricts the sources from which content can be loaded,
      using a nonce for script and style sources to prevent XSS attacks.
    - 'X-Permitted-Cross-Domain-Policies': Prevents cross-domain policy files from being used.
    - 'Referrer-Policy': Controls the amount of referrer information sent with requests.

    :param response: The Flask response object to which the security headers will be added.
    :type response: flask.Response
    :return: The response object with added security headers.
    :rtype: flask.Response
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

def allowed_file(filename):
    """
    Checks if a file is of an allowed type.

    This function is used to verify that a file uploaded by a user is of an allowed type.
    It checks if the file extension is in the ALLOWED_EXTENSIONS set.

    :param filename: The filename of the file to be checked.
    :type filename: str
    :return: True if the file is of an allowed type, False otherwise.
    :rtype: bool
    """
    if not ('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
        return False
    return True

@app.route('/')
def home():
    """
    The homepage of the file uploader.

    This function serves the index.html template which contains the file uploader form.
    It also passes the list of directories in the DOWNLOADS_PATH to the template.

    :return: The rendered index.html template as a response.
    :rtype: flask.Response
    """
    directories = [d for d in os.listdir(DOWNLOADS_PATH) if os.path.isdir(os.path.join(DOWNLOADS_PATH, d))]
    return render_template('index.html', nonce=g.nonce, directories=directories, FILE_TYPES=ALLOWED_EXTENSIONS, FILE_MAX=FILE_MAX, CONTENT_MAX=CONTENT_MAX, VERSION=VERSION)

@app.route('/upload_chunk', methods=['POST'])
def upload_chunk():
    """
    Handles a POST request to upload a chunk of a file.

    This function is called each time a chunk of a file is uploaded by the client. It
    saves the chunk to a temporary folder, and if the chunk is the last one, reassembles
    the file and moves it to the target directory.

    :return: A response indicating whether the chunk was uploaded successfully.
    :rtype: flask.Response
    """
    if 'file' not in request.files:
        logging.warning('No file part in the request')
        return 'No file part recieved in request', 400
    
    file = request.files['file']
    filename = request.form.get('filename')
    filename = secure_filename(filename)
    chunk_number = int(request.form.get('chunk'))
    total_chunks = int(request.form.get('total_chunks'))
    directory = request.form.get('directory')

    # Create a temporary folder to store chunks
    os.makedirs(TEMP_CHUNKS_PATH, exist_ok=True)

    # Save the chunk temporarily
    chunk_path = os.path.join(TEMP_CHUNKS_PATH, f"{filename}.chunk{chunk_number}")
    file.save(chunk_path)
    logging.info(f"Upload of {filename} Chunk {chunk_number + 1}/{total_chunks} recieved successfully and saved to {chunk_path}.")

    # If this is the last chunk, reassemble the file
    if chunk_number + 1 == total_chunks:
        logging.info(f"Reassembling {filename}...")
        final_file_path = os.path.join(TEMP_CHUNKS_PATH, filename)  # Recombined file still in temp folder
        # Open the final file in write mode and append each chunk
        with open(final_file_path, 'wb') as final_file:
            for i in range(total_chunks):
                part_path = os.path.join(TEMP_CHUNKS_PATH, f"{filename}.chunk{i}")
                with open(part_path, 'rb') as part_file:
                    final_file.write(part_file.read())
                os.remove(part_path)  # Remove the chunk after appending
        logging.info(f"File {filename} reassembled.")
        
        # Now validate the file's extension and MIME type after it's recombined
        if not allowed_file(filename):
            # If the file is not valid, reject it and delete the recombined file
            os.remove(final_file_path)
            logging.warning(f"Invalid file type: {filename}. The file has been deleted.")
            return 'Invalid file type, the server has rejected the file', 400
        logging.info(f"File {filename} successfully validated.")

        # Ensure the directory is safe and inside the DOWNLOADS_PATH
        resolved_directory = os.path.realpath(os.path.join(DOWNLOADS_PATH, directory))
        if not resolved_directory.startswith(os.path.realpath(DOWNLOADS_PATH)):
            os.remove(final_file_path)
            logging.warning(f'Directory traversal attempt detected: {resolved_directory}. The file has been deleted.')
            return 'Invalid directory, the server has rejected the file', 400

        # If the file is valid, move it to the target directory
        target_directory = os.path.join(DOWNLOADS_PATH, directory)
        final_destination = os.path.join(target_directory, filename)
        # Check if the file already exists at the target location
        if os.path.exists(final_destination):
            logging.warning(f"File {filename} already exists at {final_destination}. The file has been deleted.")
            os.remove(final_file_path)
            return 'File already exists on server', 400  # Send error message if file already exists
        # Move the file to the target directory
        shutil.move(final_file_path, final_destination)
        logging.info(f"File {filename} moved to {target_directory}.")

        return 'File uploaded and reassembled successfully.', 200
    return 'Chunk uploaded successfully.', 200

# Run the app
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5005)
