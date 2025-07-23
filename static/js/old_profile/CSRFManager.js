class CSRFManager {
    static getToken() {
        return document.querySelector('meta[name="csrf-token"]')?.content || profileConfig.csrfToken;
    }

    static getHeaders() {
        const token = this.getToken();
        if (!token) {
            console.error('CSRF token not found');
        }
        return {
            'Content-Type': 'application/json',
            'X-CSRFToken': token
        };
    }
}