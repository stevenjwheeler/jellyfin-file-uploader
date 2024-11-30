import logging
import os
import time

from components.configuration import TEMP_CHUNKS_PATH, STALE_FILE_THRESHOLD

def cleanup_stale_files():
    """
    Cleans up files in TEMP_CHUNKS_PATH that are left behind after an error and are older than the defined threshold.
    """
    if not os.path.exists(TEMP_CHUNKS_PATH):
        logging.info(f"Temporary directory {TEMP_CHUNKS_PATH} does not exist yet. Skipping cleanup.")
        return
    
    current_time = time.time()
    for filename in os.listdir(TEMP_CHUNKS_PATH):
        file_path = os.path.join(TEMP_CHUNKS_PATH, filename)
        
        if os.path.isdir(file_path):
            continue
        
        if current_time - os.path.getmtime(file_path) > STALE_FILE_THRESHOLD:
            try:
                os.remove(file_path)
                logging.info(f"Deleted stale temporary file: {file_path}")
            except Exception as e:
                logging.error(f"Error while deleting file {file_path}: {e}")

def periodic_cleanup():
    """
    Periodically runs the cleanup function every N seconds (e.g., every 1 hour).
    """
    while True:
        cleanup_stale_files()
        time.sleep(3600) # Run the cleanup scan every hour
