// API Client for Strava Dashboard
// Handles all AJAX requests to backend API

const API = {
    baseUrl: '/api',

    /**
     * Make a fetch request with error handling
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;

        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error?.message || 'Request failed');
            }

            return data;

        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    },

    /**
     * Get activities with optional filters
     */
    async getActivities(filters = {}) {
        const params = new URLSearchParams();

        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                params.append(key, filters[key]);
            }
        });

        const queryString = params.toString();
        const endpoint = queryString ? `/activities?${queryString}` : '/activities';

        return this.request(endpoint);
    },

    /**
     * Get single activity details
     */
    async getActivity(activityId) {
        return this.request(`/activity/${activityId}`);
    },

    /**
     * Get calculated statistics
     */
    async getStats() {
        return this.request('/stats');
    },

    /**
     * Get weekly summary
     */
    async getWeeklyStats(weeks = 4) {
        return this.request(`/stats/weekly?weeks=${weeks}`);
    },

    /**
     * Get monthly summary
     */
    async getMonthlyStats(months = 6) {
        return this.request(`/stats/monthly?months=${months}`);
    },

    /**
     * Force refresh cached data
     */
    async refreshCache() {
        return this.request('/refresh', {
            method: 'POST'
        });
    }
};

// Export for use in other modules
window.API = API;
