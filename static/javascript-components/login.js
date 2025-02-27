import { showToast } from "./toast-display.js";

document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);

    try {
        const response = await fetch(form.action, {
            method: form.method,
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrf_token')
            }
        });

        const result = await response.json();

        if (result.success) {
            window.location.href = result.redirect_url;
        } else {
            showToast('Login failed: ' + result.message, 'error');
            document.getElementById('password').value = '';
            document.getElementById('password').focus();
        }
    } catch (error) {
        showToast('Login failed: a system error occurred', 'error');
        document.getElementById('password').value = '';
        document.getElementById('password').focus();
    }
});