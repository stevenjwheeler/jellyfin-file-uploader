let toastQueue = []; // Queue to store toasts waiting to be displayed
let activeToasts = 0; // Counter to track the number of active toasts

/**
 * Shows a toast message to the user.
 *
 * @param {string} message The message to show in the toast.
 * @param {'success'|'error'} [type='success'] The type of toast to show.
 */
export function showToast(message, type = 'success') {
    if (activeToasts >= 3) {
        // If there are already 3 active toasts, add the new toast to the queue
        toastQueue.push({ message, type });
        return; // Don't show the toast yet, it will be shown when there's space
    }

    // Create the toast element
    const toast = document.createElement('div');
    toast.classList.add('toast', type);

    // Create the close button (X)
    const closeButton = document.createElement('span');
    closeButton.classList.add('close-btn');
    closeButton.innerHTML = '&times;';  // Unicode for "×"

    // Append the message and close button to the toast
    toast.innerHTML = message;
    toast.appendChild(closeButton);

    // Append the toast to the container
    document.getElementById('toastContainer').appendChild(toast);

    // Make the toast visible with a slight delay
    setTimeout(() => {
        toast.classList.add('show');
    }, 100); // Delay before showing the toast

    // Increment the active toasts counter
    activeToasts++;

     // Add the close button functionality
     closeButton.addEventListener('click', () => {
        toast.classList.remove('show');  // Fade out the toast
        // Remove the toast from the DOM once the fade-out is complete
        toast.addEventListener('transitionend', () => {
            toast.remove();
            activeToasts--; // Decrease the active toast count
            // If there are toasts in the queue, show the next one
            if (toastQueue.length > 0) {
                showNextToast();
            }
        });
    });

    // Remove the toast after 20 seconds if not manually closed
    setTimeout(() => {
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => {
            toast.remove();
            activeToasts--; // Decrease the active toast count
            // If there are toasts in the queue, show the next one
            if (toastQueue.length > 0) {
                showNextToast();
            }
        });
    }, 20000); // Toast will disappear after 20 seconds
}

// Show the next toast from the queue
function showNextToast() {
    if (toastQueue.length > 0 && activeToasts < 3) {
        const nextToast = toastQueue.shift(); // Get the next toast in the queue
        showToast(nextToast.message, nextToast.type); // Show it
    }
}