class FavoriteManager {
    static currentId = null;
    static modal = document.getElementById('confirm_modal');

    static initRemoval(favoriteId) {
        this.currentId = favoriteId;
        this.modal.showModal();
    }

    static async confirmRemoval() {
        if (!this.currentId) return;

        const response = await fetch(`/profiles/api/favorites/${this.currentId}/remove/`, {
            method: 'POST',
            headers: CSRFManager.getHeaders()
        });

        const data = await response.json();
        if (data.status === 'success') {
            this.removeCard();
        }
        this.closeModal();
    }

    static removeCard() {
        const card = document.querySelector(`[data-favorite-id="${this.currentId}"]`);
        if (card) {
            card.remove();
            
            // Check if we need to show the empty state
            const favoritesContent = document.getElementById('favorites-content');
            const remainingCards = favoritesContent.querySelectorAll('[data-favorite-id]');
            if (remainingCards.length === 0) {
                favoritesContent.innerHTML = `
                    <div class="col-span-3 text-center py-8">
                        <div class="alert">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-info shrink-0 w-6 h-6">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <span>No favorite events yet.</span>
                        </div>
                    </div>
                `;
            }
        }
        this.closeModal();
    }

    static closeModal() {
        this.modal.close();
        this.currentId = null;
    }
}

// Global functions needed for inline HTML handlers
window.removeFavorite = function(button) {
    FavoriteManager.initRemoval(button.dataset.favoriteId);
};

window.confirmRemoveFavorite = function() {
    FavoriteManager.confirmRemoval();
};

window.closeModal = function() {
    FavoriteManager.closeModal();
};