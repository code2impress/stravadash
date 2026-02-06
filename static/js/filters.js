// Filters Module - Activity filtering logic

const Filters = {
    currentFilters: {},

    /**
     * Initialize filter event listeners
     */
    init() {
        const applyBtn = document.getElementById('apply-filters-btn');
        const resetBtn = document.getElementById('reset-filters-btn');

        if (applyBtn) {
            applyBtn.addEventListener('click', () => this.applyFilters());
        }

        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetFilters());
        }

        // Load filters from URL parameters on page load
        this.loadFiltersFromURL();
    },

    /**
     * Get current filter values from form
     */
    getFilterValues() {
        return {
            search: document.getElementById('filter-search')?.value || '',
            type: document.getElementById('filter-type')?.value || '',
            start_date: document.getElementById('filter-start-date')?.value || '',
            end_date: document.getElementById('filter-end-date')?.value || '',
            min_distance: document.getElementById('filter-min-distance')?.value || '',
            max_distance: document.getElementById('filter-max-distance')?.value || ''
        };
    },

    /**
     * Set filter values in form
     */
    setFilterValues(filters) {
        if (filters.search !== undefined) {
            const searchInput = document.getElementById('filter-search');
            if (searchInput) searchInput.value = filters.search;
        }

        if (filters.type !== undefined) {
            const typeSelect = document.getElementById('filter-type');
            if (typeSelect) typeSelect.value = filters.type;
        }

        if (filters.start_date !== undefined) {
            const startDateInput = document.getElementById('filter-start-date');
            if (startDateInput) startDateInput.value = filters.start_date;
        }

        if (filters.end_date !== undefined) {
            const endDateInput = document.getElementById('filter-end-date');
            if (endDateInput) endDateInput.value = filters.end_date;
        }

        if (filters.min_distance !== undefined) {
            const minDistInput = document.getElementById('filter-min-distance');
            if (minDistInput) minDistInput.value = filters.min_distance;
        }

        if (filters.max_distance !== undefined) {
            const maxDistInput = document.getElementById('filter-max-distance');
            if (maxDistInput) maxDistInput.value = filters.max_distance;
        }
    },

    /**
     * Apply filters and reload activities
     */
    async applyFilters() {
        const filters = this.getFilterValues();

        // Remove empty filters
        Object.keys(filters).forEach(key => {
            if (!filters[key]) {
                delete filters[key];
            }
        });

        this.currentFilters = filters;

        // Update URL with filter parameters
        this.updateURL(filters);

        // Trigger dashboard reload
        if (window.Dashboard) {
            await window.Dashboard.loadActivities(filters);
        }
    },

    /**
     * Reset all filters
     */
    async resetFilters() {
        // Clear form inputs
        this.setFilterValues({
            search: '',
            type: '',
            start_date: '',
            end_date: '',
            min_distance: '',
            max_distance: ''
        });

        this.currentFilters = {};

        // Clear URL parameters
        window.history.pushState({}, '', window.location.pathname);

        // Reload activities without filters
        if (window.Dashboard) {
            await window.Dashboard.loadActivities();
        }
    },

    /**
     * Update URL with filter parameters
     */
    updateURL(filters) {
        const params = new URLSearchParams();

        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                params.set(key, filters[key]);
            }
        });

        const queryString = params.toString();
        const newURL = queryString ? `?${queryString}` : window.location.pathname;

        window.history.pushState({}, '', newURL);
    },

    /**
     * Load filters from URL parameters
     */
    loadFiltersFromURL() {
        const params = new URLSearchParams(window.location.search);
        const filters = {};

        ['search', 'type', 'start_date', 'end_date', 'min_distance', 'max_distance'].forEach(key => {
            const value = params.get(key);
            if (value) {
                filters[key] = value;
            }
        });

        if (Object.keys(filters).length > 0) {
            this.setFilterValues(filters);
            this.currentFilters = filters;
        }
    },

    /**
     * Get active filter count (for display)
     */
    getActiveFilterCount() {
        return Object.keys(this.currentFilters).length;
    }
};

// Export for use in other modules
window.Filters = Filters;
