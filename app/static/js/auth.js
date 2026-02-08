// app/static/js/auth.js

/**
 * Wrapper for fetch that includes the JWT token in headers.
 * Redirects to /login if 401 Unauthorized is returned.
 */
async function authFetch(url, options = {}) {
    const token = localStorage.getItem('access_token');

    // Prepare headers
    const headers = new Headers(options.headers || {});
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    const fetchOptions = {
        ...options,
        headers: headers
    };

    console.log(`AUTH_FETCH [${url}]: Sending with token present: ${!!token}`);
    if (token) {
        console.log(`AUTH_FETCH [${url}]: Header = Bearer ${token.substring(0, 10)}...`);
    }

    try {
        const response = await fetch(url, fetchOptions);

        if (response.status === 401) {
            console.warn("Unauthorized access to " + url + ". Redirecting...");
            localStorage.removeItem('access_token');
            window.location.href = '/login';
            return null;
        }

        return response;
    } catch (error) {
        console.error("authFetch error:", error);
        throw error;
    }
}

// Redirect if accessing a protected page without a token
document.addEventListener('DOMContentLoaded', () => {
    const publicPages = ['/login', '/', ''];
    const currentPath = window.location.pathname;

    if (!publicPages.includes(currentPath) && !localStorage.getItem('access_token')) {
        console.log("No token found. Redirecting to login.");
        window.location.href = '/login';
    }
});
