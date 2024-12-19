// Infinite scroll implementation
const InfiniteScroll = {
    init() {
        console.log('Initializing infinite scroll'); // Debug
        this.loading = false;
        this.paginationData = document.getElementById('pagination-data');
        this.hasNext = JSON.parse(this.paginationData.dataset.hasNext);
        this.nextPage = this.paginationData.dataset.nextPage;
        this.nextPage = this.nextPage === 'null' ? null : parseInt(this.nextPage);
        this.currentFilters = this.paginationData.dataset.currentFilters;
        this.eventsGrid = document.getElementById('events-grid');
        this.spinner = document.getElementById('loading-spinner');
        this.sentinel = document.getElementById('scroll-sentinel');

        console.log('Initial state:', { hasNext: this.hasNext, nextPage: this.nextPage }); // Debug

        if (this.hasNext && this.nextPage) {
            this.initObserver();
        }
    },

    async loadMoreEvents() {
        if (this.loading || !this.hasNext || !this.nextPage) {
            console.log('Loading stopped:', { loading: this.loading, hasNext: this.hasNext, nextPage: this.nextPage }); // Debug
            return;
        }
        
        console.log('Loading more events...'); // Debug
        this.loading = true;
        this.spinner.classList.remove('hidden');
        
        const url = window.location.pathname + 
            `?page=${this.nextPage}${this.currentFilters ? '&' + this.currentFilters : ''}`;
        
        try {
            const response = await fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            console.log('Received data:', data); // Debug
            
            if (data.html) {
                this.eventsGrid.insertAdjacentHTML('beforeend', data.html);
                this.updatePaginationState(data);
            }
        } catch (error) {
            console.error('Error loading more events:', error);
        } finally {
            this.loading = false;
            this.spinner.classList.add('hidden');
        }
    },

    updatePaginationState(data) {
        this.hasNext = data.has_next;
        this.nextPage = data.next_page;
        this.paginationData.dataset.hasNext = this.hasNext;
        this.paginationData.dataset.nextPage = this.nextPage || 'null';
        console.log('Updated pagination state:', { hasNext: this.hasNext, nextPage: this.nextPage }); // Debug
    },

    initObserver() {
        console.log('Creating observer'); // Debug
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    console.log('Intersection:', entry.isIntersecting); // Debug
                    if (entry.isIntersecting && this.hasNext && this.nextPage) {
                        this.loadMoreEvents();
                    }
                });
            },
            {
                root: null,
                rootMargin: '50px',
                threshold: 0.1
            }
        );

        observer.observe(this.sentinel);
        console.log('Observer started'); // Debug
    }
};

// Initialize infinite scroll when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing infinite scroll'); // Debug
    InfiniteScroll.init();
});
