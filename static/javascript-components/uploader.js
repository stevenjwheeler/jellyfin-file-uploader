const CHUNK_SIZE = 32 * 1024 * 1024; // 32MB per chunk
import { totalBytesUploaded, updateTotalBytesUploaded, updateUploadedFilesCount, updateSkippedFilesCount } from '../main.js';
import { showToast } from './toast-display.js';

/**
 * Uploads a file to the server in chunks, to avoid issues with large file sizes.
 * @param {File} file The file to upload
 * @param {string} directory The directory to upload the file to
 * @param {number} totalBytesToUpload The total number of bytes to upload across all files
 */
export async function uploadFileInChunks(file, directory, totalBytesToUpload) {
    const checksum = await computeChecksum(file);
    console.log(`Checksum for file ${file.name}: ${checksum}`);
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE); // Calculate the total number of chunks needed to send this file
    let currentChunk = 0; // Track the current chunk
    let fileBytesUploaded = 0; // Track bytes uploaded for the current file
    const upload_uuid = crypto.randomUUID(); // Generate a UUID for the upload
    
    /**
     * Uploads the next chunk of a file to the server.
     * @private
     */
    async function uploadNextChunk() {
        return new Promise((resolve, reject) => {
            console.log(`Uploading chunk ${currentChunk + 1} of ${totalChunks} for file ${file.name}`);
            const start = currentChunk * CHUNK_SIZE;
            const end = Math.min(start + CHUNK_SIZE, file.size);
            const chunk = file.slice(start, end);
            const formData = new FormData();
            formData.append('file', chunk);
            formData.append('filename', file.name);
            formData.append('checksum', checksum);
            formData.append('chunk', currentChunk);
            formData.append('total_chunks', totalChunks);
            formData.append('directory', directory);
            formData.append('upload_uuid', upload_uuid);

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
                    // Progress for the current file chunk
                    const previouslyUploaded = currentChunk * CHUNK_SIZE; // Bytes completed in all previous chunks of this file
                    const currentChunkProgress = event.loaded; // Bytes uploaded in the current chunk
                    
                    // Calculate the current file progress
                    fileBytesUploaded = previouslyUploaded + currentChunkProgress; // Total bytes uploaded for the current file
                    
                    // Update global progress
                    const globalBytesUploaded = totalBytesUploaded + fileBytesUploaded;
            
                    // Update overall progress bar
                    const overallPercentComplete = Math.round((globalBytesUploaded / totalBytesToUpload) * 100);
                    document.getElementById('overallProgressBar').style.width = `${Math.min(overallPercentComplete, 100)}%`;
            
                    // Update file progress bar
                    const currentFilePercentComplete = Math.round((fileBytesUploaded / file.size) * 100);
                    document.getElementById('fileProgressBar').style.width = `${Math.min(currentFilePercentComplete, 100)}%`;
            
                    // Update progress text
                    document.getElementById('progressText').innerText = `Uploading ${file.name} - ${Math.min(currentFilePercentComplete, 100)}% uploaded`;
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
                    // Check if all chunks have been uploaded
                    if (currentChunk < totalChunks) {
                        resolve(uploadNextChunk());
                    } else {
                        // File completely uploaded, update totalBytesUploaded
                        updateTotalBytesUploaded(file.size);
                        console.log(`All chunks uploaded for file ${file.name}. Total bytes uploaded: ${totalBytesUploaded}`);
                        updateUploadedFilesCount();
                        resolve();
                    }
                } else { // Upload failed
                    let errorMessage = xhr.responseText; // Get the raw error response
                    try {
                        // Try to parse the response and extract the error message
                        const responseObject = JSON.parse(xhr.responseText);
                        if (responseObject && responseObject.error) {
                            errorMessage = responseObject.error; // Extract the error message
                        }
                    } catch (e) {
                        // If parsing fails, log an error and use the raw response text
                        console.error('Error parsing response:', e);
                        reject(new Error("An error occurred during the upload."));
                    }
                reject(new Error(errorMessage));
                }
            };

            xhr.onerror = function () { // Network error
                let errorMessage = 'Network error during upload.';
                try {
                    // If responseText is available (it may not be on network errors)
                    if (xhr.responseText) {
                        const responseObject = JSON.parse(xhr.responseText);
                        if (responseObject && responseObject.error) {
                            errorMessage = responseObject.error; // Extract the error message
                        }
                    }
                } catch (e) {
                    console.error('Error parsing response:', e);
                }
                reject(new Error(errorMessage));
            };

            // Send the file chunk
            xhr.send(formData);
        });
    }

    try {
        await uploadNextChunk();
    } catch (error) {
        // If an error occurs, log it and skip the current file, but continue with the others
        console.log(`Error during upload of ${file.name}\n${error}\nSkipping this file.`);
        showToast(`Failed to upload ${file.name}<br>${error}<br>Skipping this file.`, 'error');
        updateSkippedFilesCount();
    }
}

/**
 * Computes the SHA-256 checksum of a file using the Web Crypto API.
 * @param {File} file The file to compute the checksum for
 * @returns {Promise<string>} The computed checksum as a hex string
 */
async function computeChecksum(file) {
    const arrayBuffer = await file.arrayBuffer(); // Read file as an ArrayBuffer
    const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer); // Compute SHA-256 hash
    return Array.from(new Uint8Array(hashBuffer)) // Convert ArrayBuffer to byte array
        .map(b => b.toString(16).padStart(2, '0')) // Convert bytes to hex
        .join(''); // Join all hex bytes into a single string
}