import { uploadFileInChunks } from './javascript-components/uploader.js';
import { showToast } from './javascript-components/toast-display.js';

MAX_FILE_SIZE = MAX_FILE_SIZE * 1024 * 1024 * 1024; // Convert MB to bytes
MAX_TOTAL_SIZE = MAX_TOTAL_SIZE * 1024 * 1024 * 1024; // Convert MB to bytes

export let totalBytesUploaded = 0; // Track upload bytes for progress bars
export let uploadedFilesCount = 0; // Count of files successfully uploaded
export let skippedFilesCount = 0;  // Count of files skipped due to errors
let totalUploadSize = 0; // Track total upload size for checking against the size limitations

document.addEventListener('DOMContentLoaded', async function () {
    /**
     * Called when the form is submitted. Prevents the default form submission
     * and instead uploads the files in chunks to the server.
     * @param {Event} event The form submission event
     */
    document.getElementById('uploadForm').onsubmit = async function (event) {
        event.preventDefault();
        console.log('Form submitted');

        // Track the total upload size for checking against the size limitations
        totalUploadSize = 0;

        // Track the number of uploaded and skipped files
        uploadedFilesCount = 0;
        skippedFilesCount = 0;

        // Get the form data
        const files = document.getElementById('fileInput').files;
        const directory = document.getElementById('directorySelect').value;

        // Disable the submit button
        document.getElementById('uploadButton').disabled = true;

        // Reset the overall progress bar once before starting any uploads
        document.getElementById('overallProgressBar').style.width = '0%';
        totalUploadSize = 0;
        totalBytesUploaded = 0;

        // Determine if a file is too large
        for (let file of files) {
            console.log(`Checking file ${file.name} size: ${file.size}`);
            totalUploadSize += file.size;
            if (file.size > MAX_FILE_SIZE) {
                console.log(`File ${file.name} exceeds the maximum allowed.`);
                showToast(`File ${file.name} exceeds the maximum allowed. Skipped that file.`, 'error');
                // Remove the file from the collection
                return;
            }
        }
        // Determine if the total upload size is too large
        console.log(`Total upload size: ${totalUploadSize}`);
        if (totalUploadSize > MAX_TOTAL_SIZE) {
            console.log('Total upload size exceeds the maximum allowed.');
            showToast('Total upload size exceeds the maximum allowed.', 'error');
            resetForm();
            return;
        }

        // Process each file
        for (let file of files) {
            console.log(`Processing file ${file.name}`);
            document.getElementById('fileProgressBar').style.width = '0%'; // Reset progress bar
            await uploadFileInChunks(file, directory, totalUploadSize);
        }

        // Clear the form and display a success message
        console.log('Upload finished');
        showToast(`Upload finished! ${uploadedFilesCount} file(s) uploaded, ${skippedFilesCount} file(s) skipped.`, 'success');
        resetForm();
        return;
    };
});

/**
 * Increments the count of skipped files. Called when a file cannot be uploaded
 * due to errors.
 */
export function updateSkippedFilesCount() {
    skippedFilesCount += 1;
}

/**
 * Increments the count of uploaded files. Called when a file is successfully
 * uploaded in chunks.
 */
export function updateUploadedFilesCount() {
    uploadedFilesCount += 1;
}

/**
 * Increments the totalBytesUploaded counter by the provided number of bytes.
 * @param {number} bytes The number of bytes to increment the counter by.
 */
export function updateTotalBytesUploaded(bytes) {
    totalBytesUploaded += bytes;
}

/**
 * Resets the file input to blank values
 */
export function resetForm() {
    // Clear the form
    console.log('Clearing form');
    document.getElementById('fileInput').value = '';
    document.getElementById('fileProgressBar').style.width = '0%';
    document.getElementById('overallProgressBar').style.width = '0%';
    document.getElementById('progressText').innerText = 'Waiting for upload to start...';
    document.getElementById('uploadButton').disabled = false;
}
