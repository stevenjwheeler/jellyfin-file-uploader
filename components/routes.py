import os
from flask import render_template, request, g

from components.chunk_handler import handle_upload_chunk
from components.configuration import DOWNLOADS_PATH, ALLOWED_EXTENSIONS, FILE_MAX, CONTENT_MAX, VERSION

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

def upload_chunk():
    return handle_upload_chunk(request)
