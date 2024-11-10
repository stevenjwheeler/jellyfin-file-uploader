MAX_FILE_SIZE = MAX_FILE_SIZE * 1024 * 1024 * 1024; // Convert MB to bytes
MAX_TOTAL_SIZE = MAX_TOTAL_SIZE * 1024 * 1024 * 1024; // Convert MB to bytes
const CHUNK_SIZE = 32 * 1024 * 1024; // 32MB per chunk

// Track upload bytes for progress bars
let totalBytesUploaded = 0;
let totalUploadSize = 0;

document.addEventListener('DOMContentLoaded', async function () {
    /**
     * Called when the form is submitted. Prevents the default form submission
     * and instead uploads the files in chunks to the server.
     * @param {Event} event The form submission event
     */
    document.getElementById('uploadForm').onsubmit = async function (event) {
        event.preventDefault();
        console.log('Form submitted');
        const files = document.getElementById('fileInput').files;
        const directory = document.getElementById('directorySelect').value;

        // Disable the submit button
        document.getElementById('uploadButton').disabled = true;

        // Reset the overall progress bar once before starting any uploads
        document.getElementById('overallProgressBar').style.width = '0%';
        totalBytesUploaded = 0;
        totalUploadSize = 0;

        // Determine if a file is too large
        for (let file of files) {
            console.log(`Checking file ${file.name} size: ${file.size}`);
            totalUploadSize += file.size;
            if (file.size > MAX_FILE_SIZE) {
                console.log(`File ${file.name} exceeds the maximum allowed.`);
                resetForm(`File ${file.name} exceeds the maximum allowed.`);
                return;
            }
        }
        // Determine if the total upload size is too large
        console.log(`Total upload size: ${totalUploadSize}`);
        if (totalUploadSize > MAX_TOTAL_SIZE) {
            console.log('Total upload size exceeds the maximum allowed.');
            resetForm('Total upload size exceeds the maximum allowed.');
            return;
        }

        // Process each file
        for (let file of files) {
            console.log(`Processing file ${file.name}`);
            document.getElementById('fileProgressBar').style.width = '0%'; // Reset progress bar
            await uploadFileInChunks(file, directory, totalUploadSize);
        }

        // Clear the form and display a success message
        console.log('All files uploaded successfully');
        resetForm('All files uploaded successfully');
        return;
    };
});

/**
 * Uploads a file to the server in chunks, to avoid issues with large file sizes.
 * @param {File} file The file to upload
 * @param {string} directory The directory to upload the file to
 * @param {number} totalBytesToUpload The total number of bytes to upload across all files
 */
async function uploadFileInChunks(file, directory, totalBytesToUpload) {
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE); // Calculate the total number of chunks needed to send this file
    let currentChunk = 0; // Track the current chunk
    let fileBytesUploaded = 0; // Track bytes uploaded for the current file

    /**
     * Uploads the next chunk of a file to the server.
     * @private
     */
    function uploadNextChunk() {
        return new Promise((resolve, reject) => {
            console.log(`Uploading chunk ${currentChunk + 1} of ${totalChunks} for file ${file.name}`);
            const start = currentChunk * CHUNK_SIZE;
            const end = Math.min(start + CHUNK_SIZE, file.size);
            const chunk = file.slice(start, end);
            const formData = new FormData();
            formData.append('file', chunk);
            formData.append('filename', file.name);
            formData.append('chunk', currentChunk);
            formData.append('total_chunks', totalChunks);
            formData.append('directory', directory);

            // Get the CSRF token from the meta tag
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

            // Create an XMLHttpRequest
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload_chunk', true);

            // Set the request headers
            xhr.setRequestHeader('X-CSRFToken', csrfToken);

            /**
             * Event handler for tracking the upload progress of a file chunk.
             *
             * @param {ProgressEvent} event - The progress event containing information about the upload progress.
             */
            xhr.upload.onprogress = function (event) {
                if (event.lengthComputable) {
                    // Increment the total bytes uploaded for the current file (this is chunk by chunk)
                    fileBytesUploaded += event.loaded;

                    // Calculate the percentage of the file uploaded (relative to the total file size)
                    const currentFilePercentComplete = Math.round((fileBytesUploaded / file.size) * 100);
                    document.getElementById('fileProgressBar').style.width = `${Math.min(currentFilePercentComplete, 100)}%`;
                    document.getElementById('progressText').innerText = `Uploading ${file.name} - ${Math.min(currentFilePercentComplete, 100)}% uploaded`;

                    // Calculate the overall progress based on totalBytesToUpload
                    totalBytesUploaded += event.loaded;
                    const overallPercentComplete = Math.round((totalBytesUploaded / totalBytesToUpload) * 100);
                    document.getElementById('overallProgressBar').style.width = `${Math.min(overallPercentComplete, 100)}%`;
                }
            };

            /**
             * Handles the completion of an XMLHttpRequest.
             * 
             * @description
             * This function checks the HTTP status code of the XMLHttpRequest to determine
             * if the current file chunk was uploaded successfully.
             */
            xhr.onload = function () {
                if (xhr.status == 200) {
                    currentChunk++;
                    // Check if all chunks have been uploaded, and if not, upload the next chunk
                    if (currentChunk < totalChunks) {
                        resolve(uploadNextChunk());
                    } else { // All chunks have been uploaded
                        console.log(`All chunks uploaded for file ${file.name} successfully`);
                        resolve();
                    }
                } else { // Upload failed
                    console.log(`Upload failed for file ${file.name}`);
                    resetForm(xhr.responseText);
                    reject(new Error(xhr.responseText));
                }
            };

            xhr.onerror = function () {
                console.log(`Upload error for file ${file.name}`);
                resetForm(xhr.responseText);
                reject(new Error('Network error during upload.'));
            };

            // Send the file chunk
            xhr.send(formData);
        });
    }
    await uploadNextChunk();
}

/**
 * Resets the file input to blank values, and
 * displays the given message to the user.
 * @param {string} message The message to display to the user
 */
function resetForm(message) {
    // Check if message is empty or undefined and replace it with default if so
    message = message || 'An error occurred, please try again';
    // Clear the form and display the message
    console.log('Clearing form');
    document.getElementById('fileInput').value = '';
    document.getElementById('fileProgressBar').style.width = '0%';
    document.getElementById('overallProgressBar').style.width = '0%';
    document.getElementById('progressText').innerText = 'Waiting for upload to start...';
    alert(message);
    document.getElementById('uploadButton').disabled = false;
}