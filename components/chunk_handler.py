import hashlib
import os
import shutil
import logging
from werkzeug.utils import secure_filename
from flask import jsonify

from components.configuration import TEMP_CHUNKS_PATH, DOWNLOADS_PATH, ALLOWED_EXTENSIONS

def handle_upload_chunk(request):
    """
    Handles a chunk of the file upload. Saves chunks and assembles the file when the last chunk is uploaded.
    """
    # Ensure the 'file' part exists in the request
    if 'file' not in request.files:
        logging.warning('No file part in the request')
        return jsonify({'error': 'No file part received in request'}), 400
    
    file = request.files['file']
    
    # Retrieve other parameters and ensure they're present
    filename = request.form.get('filename')
    if not filename:
        logging.warning('Filename is missing in the request')
        return jsonify({'error': 'Filename is missing'}), 400
    filename = secure_filename(filename)
    chunk_number = request.form.get('chunk')
    if not chunk_number:
        logging.warning('Chunk number is missing in the request')
        return jsonify({'error': 'Chunk number is missing'}), 400
    chunk_number = int(chunk_number)
    total_chunks = request.form.get('total_chunks')
    if not total_chunks:
        logging.warning('Total chunks is missing in the request')
        return jsonify({'error': 'Total chunks is missing'}), 400
    total_chunks = int(total_chunks)
    directory = request.form.get('directory')
    if not directory:
        logging.warning('Directory is missing in the request')
        return jsonify({'error': 'Directory is missing'}), 400
    upload_uuid = request.form.get('upload_uuid')
    if not upload_uuid:
        logging.warning('Upload UUID is missing in the request')
        return jsonify({'error': 'Upload UUID is missing'}), 400

    # Create a temporary folder to store chunks
    os.makedirs(TEMP_CHUNKS_PATH, exist_ok=True)

    # Save the chunk temporarily
    chunk_path = os.path.join(TEMP_CHUNKS_PATH, f"{filename}.chunk{chunk_number}-{upload_uuid}")
    try:
        file.save(chunk_path)
        logging.info(f"Upload of {filename} Chunk {chunk_number + 1}/{total_chunks} received successfully and saved to {chunk_path}.")
    except Exception as e:
        logging.error(f"Error saving chunk: {e}")
        return jsonify({'error': 'Failed to save chunk'}), 500

    # If this is the last chunk, reassemble the file
    if chunk_number + 1 == total_chunks:
        logging.info(f"Reassembling {filename}...")
        final_file_path = os.path.join(TEMP_CHUNKS_PATH, filename)  # Recombined file still in temp folder
        try:
            with open(final_file_path, 'wb') as final_file:
                for i in range(total_chunks):
                    part_path = os.path.join(TEMP_CHUNKS_PATH, f"{filename}.chunk{i}-{upload_uuid}")
                    with open(part_path, 'rb') as part_file:
                        final_file.write(part_file.read())
                    os.remove(part_path)  # Remove the chunk after appending
            logging.info(f"File {filename} reassembled.")
        except Exception as e:
            logging.error(f"Error during file reassembly: {e}")
            return jsonify({'error': 'Failed to reassemble file'}), 500
        
        # Now validate the checksum of the recombined file
        checksum = request.form.get('checksum')
        if checksum != compute_checksum(final_file_path):
            os.remove(final_file_path)
            logging.warning(f"Checksum mismatch for file {filename}. Was expecting {compute_checksum(final_file_path)}, but got {checksum}. The file has been deleted.")
            return jsonify({'error': 'Checksum mismatch, the upload may have been corrupted and the server has rejected the file'}), 400
        logging.info(f"Checksum for file {filename} successfully validated.")

        # Now validate the file's extension and MIME type after it's recombined
        if not allowed_file(filename):
            os.remove(final_file_path)
            logging.warning(f"Invalid file type: {filename}. The file has been deleted.")
            return jsonify({'error': 'Invalid file type, the server has rejected the file'}), 400
        logging.info(f"Filetype for file {filename} successfully validated.")

        # Ensure the directory is safe and inside the DOWNLOADS_PATH
        resolved_directory = os.path.realpath(os.path.join(DOWNLOADS_PATH, directory))
        if not resolved_directory.startswith(os.path.realpath(DOWNLOADS_PATH)):
            os.remove(final_file_path)
            logging.warning(f'Directory traversal attempt detected: {resolved_directory}. The file has been deleted.')
            return jsonify({'error': 'Invalid directory, the server has rejected the file'}), 400
        logging.info(f"Directory for file {filename} successfully validated.")

        # If the file is valid, move it to the target directory
        target_directory = os.path.join(DOWNLOADS_PATH, directory)
        final_destination = os.path.join(target_directory, filename)
        if os.path.exists(final_destination):
            logging.warning(f"File {filename} already exists at {final_destination}. The file has been deleted.")
            os.remove(final_file_path)
            return jsonify({'error': 'File already exists on server'}), 400
        shutil.move(final_file_path, final_destination)
        logging.info(f"File {filename} completed validations and was moved to {target_directory}.")
        return jsonify({'message': 'File uploaded and reassembled successfully.'}), 200

    return jsonify({'message': 'Chunk uploaded successfully.'}), 200

def compute_checksum(file):
    """
    Computes the MD5 checksum of a file.

    :param file: The path to the file.
    :type file: str
    :return: The SHA-256 checksum of the file.
    :rtype: str
    """
    sha256 = hashlib.sha256()
    with open(file, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
    server_checksum = sha256.hexdigest()
    return server_checksum

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