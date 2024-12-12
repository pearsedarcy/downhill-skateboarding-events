class RSVPManager {
    static async updateRSVP(eventId, status) {
        const response = await fetch('/profile/api/rsvp/update/', {
            method: 'POST',
            headers: CSRFManager.getHeaders(),
            body: JSON.stringify({ event_id: eventId, status })
        });

        const data = await response.json();
        if (data.status === 'success') {
            this.updateUI(eventId, status);
        }
    }

    static updateUI(eventId, status) {
        const card = document.querySelector(`[data-event-id="${eventId}"]`);
        if (!card) return;

        // Update badge in dropdown button
        const dropdownButton = card.querySelector('.dropdown button.badge');
        if (dropdownButton) {
            const icon = this.getStatusIcon(status);
            const badgeClass = this.getStatusBadgeClass(status);
            
            dropdownButton.innerHTML = `${icon} ${status}`;
            dropdownButton.className = `badge badge-lg gap-2 ${badgeClass}`;
        }
        
        // Update dropdown menu items
        const dropdownItems = card.querySelectorAll('.dropdown-content li a');
        dropdownItems.forEach(item => {
            const itemText = item.textContent.trim();
            const isActive = itemText.includes(status);
            item.classList.toggle('active', isActive);
        });

        // Close dropdown by removing focus from all interactive elements
        const dropdown = card.querySelector('.dropdown');
        const dropdownMenu = card.querySelector('.dropdown-content');
        if (dropdown && dropdownMenu) {
            dropdownButton.blur();
            dropdownMenu.blur();
            dropdown.blur();
            // Remove tabindex focus
            dropdownMenu.setAttribute('tabindex', '-1');
            setTimeout(() => dropdownMenu.setAttribute('tabindex', '0'), 100);
        }
    }

    static getStatusIcon(status) {
        switch(status) {
            case 'Going': return '<i class="fas fa-check-circle"></i>';
            case 'Not interested': return '<i class="fas fa-times-circle"></i>';
            default: return '<i class="fas fa-star"></i>';
        }
    }

    static getStatusBadgeClass(status) {
        switch(status) {
            case 'Going': return 'badge-primary';
            case 'Not interested': return 'badge-error';
            default: return 'badge-secondary';
        }
    }
}

// Global function needed for inline HTML handlers
window.updateRSVP = function(eventId, status) {
    RSVPManager.updateRSVP(eventId, status);
};