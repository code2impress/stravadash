// Dashboard Module - Main orchestrator for Strava Dashboard

const Dashboard = {
    activities: [],
    stats: null,
    autoRefreshTimer: null,
    selectedYear: 'all',
    yearlyData: {},

    /**
     * Initialize dashboard
     */
    async init() {
        console.log('Initializing dashboard...');

        // Initialize modules
        Maps.initModal();
        Filters.init();
        this.initGoals();

        // Setup event listeners
        this.setupEventListeners();

        // Load initial data
        await this.loadData();

        // Setup auto-refresh
        this.setupAutoRefresh();

        // Update last updated timestamp
        this.updateLastUpdated();
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.handleRefresh());
        }

        // Year selector
        const yearSelector = document.getElementById('year-selector');
        if (yearSelector) {
            yearSelector.addEventListener('change', (e) => this.handleYearChange(e.target.value));
        }

        // Goals button and modal
        const setGoalsBtn = document.getElementById('set-goals-btn');
        const closeGoalsBtn = document.getElementById('close-goals-modal');
        const saveGoalsBtn = document.getElementById('save-goals-btn');
        const clearGoalsBtn = document.getElementById('clear-goals-btn');

        if (setGoalsBtn) setGoalsBtn.addEventListener('click', () => this.openGoalsModal());
        if (closeGoalsBtn) closeGoalsBtn.addEventListener('click', () => this.closeGoalsModal());
        if (saveGoalsBtn) saveGoalsBtn.addEventListener('click', () => this.saveGoals());
        if (clearGoalsBtn) clearGoalsBtn.addEventListener('click', () => this.clearGoals());
    },

    /**
     * Load all dashboard data
     */
    async loadData() {
        try {
            // Show loading state
            this.showLoading(true);

            // Load activities and stats in parallel
            const [activitiesResult, statsResult] = await Promise.all([
                API.getActivities(Filters.currentFilters),
                API.getStats()
            ]);

            this.activities = activitiesResult.data.activities;
            this.stats = statsResult.data;

            // Update UI
            this.updateStats(this.stats.totals);
            this.renderActivities(this.activities);

            // Update charts
            if (this.stats.chart_data) {
                Charts.init(this.stats.chart_data);
            }

            // Update yearly stats table
            if (this.stats.yearly_stats) {
                this.renderYearlyStats(this.stats.yearly_stats);
                // Populate year selector dropdown
                this.populateYearSelector(this.stats.yearly_stats);
            }

            // Update goal progress
            this.updateGoalProgress();

            // Hide loading, show content
            this.showLoading(false);

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data. Please try refreshing the page.');
            this.showLoading(false);
        }
    },

    /**
     * Load activities with filters
     */
    async loadActivities(filters = {}) {
        try {
            const result = await API.getActivities(filters);
            this.activities = result.data.activities;
            this.renderActivities(this.activities);

        } catch (error) {
            console.error('Error loading activities:', error);
            this.showError('Failed to load activities.');
        }
    },

    /**
     * Update statistics display
     */
    updateStats(totals) {
        // Total distance
        const distanceEl = document.getElementById('stat-distance');
        if (distanceEl) {
            const distanceKm = (totals.total_distance / 1000).toFixed(1);
            distanceEl.textContent = `${distanceKm} km`;
            distanceEl.classList.add('stat-update');
            setTimeout(() => distanceEl.classList.remove('stat-update'), 300);
        }

        // Activity count
        const countEl = document.getElementById('stat-count');
        if (countEl) {
            countEl.textContent = totals.activity_count;
            countEl.classList.add('stat-update');
            setTimeout(() => countEl.classList.remove('stat-update'), 300);
        }

        // Total time
        const timeEl = document.getElementById('stat-time');
        if (timeEl) {
            const hours = Math.floor(totals.total_time / 3600);
            const minutes = Math.floor((totals.total_time % 3600) / 60);
            timeEl.textContent = `${hours}h ${minutes}m`;
            timeEl.classList.add('stat-update');
            setTimeout(() => timeEl.classList.remove('stat-update'), 300);
        }

        // Total elevation
        const elevationEl = document.getElementById('stat-elevation');
        if (elevationEl) {
            elevationEl.textContent = `${Math.round(totals.total_elevation)} m`;
            elevationEl.classList.add('stat-update');
            setTimeout(() => elevationEl.classList.remove('stat-update'), 300);
        }
    },

    /**
     * Render activities list
     */
    renderActivities(activities) {
        const listEl = document.getElementById('activities-list');
        const countEl = document.getElementById('activity-count');
        const noActivitiesEl = document.getElementById('no-activities');

        if (!listEl) return;

        // Update count
        if (countEl) {
            countEl.textContent = activities.length;
        }

        // Show/hide empty state
        if (activities.length === 0) {
            listEl.innerHTML = '';
            if (noActivitiesEl) noActivitiesEl.classList.remove('hidden');
            return;
        } else {
            if (noActivitiesEl) noActivitiesEl.classList.add('hidden');
        }

        // Render activity cards
        listEl.innerHTML = activities.map(activity => this.createActivityCard(activity)).join('');

        // Add click handlers for map buttons
        activities.forEach((activity, index) => {
            const mapBtn = document.getElementById(`map-btn-${index}`);
            if (mapBtn && activity.map && activity.map.summary_polyline) {
                mapBtn.addEventListener('click', () => Maps.showRoute(activity));
            }
        });
    },

    /**
     * Render yearly statistics table
     */
    renderYearlyStats(yearlyStats) {
        const tbody = document.getElementById('yearly-stats-body');
        if (!tbody) return;

        if (!yearlyStats || yearlyStats.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-slate-400">No yearly data available</td></tr>';
            return;
        }

        // Sort by year descending (most recent first)
        const sortedStats = [...yearlyStats].sort((a, b) => b.year - a.year);

        tbody.innerHTML = sortedStats.map(yearStat => {
            const distanceKm = (yearStat.total_distance / 1000).toFixed(1);
            const hours = Math.floor(yearStat.total_time / 3600);
            const elevation = Math.round(yearStat.total_elevation);

            return `
                <tr class="border-b border-slate-700 hover:bg-slate-750">
                    <td class="py-3 px-4 text-white font-semibold">${yearStat.year}</td>
                    <td class="py-3 px-4 text-right text-slate-300">${yearStat.activity_count}</td>
                    <td class="py-3 px-4 text-right text-slate-300">${distanceKm} km</td>
                    <td class="py-3 px-4 text-right text-slate-300">${hours}h</td>
                    <td class="py-3 px-4 text-right text-slate-300">${elevation} m</td>
                </tr>
            `;
        }).join('');
    },

    /**
     * Create activity card HTML
     */
    createActivityCard(activity, index) {
        const date = new Date(activity.start_date_local || activity.start_date);
        const dateStr = date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
        const timeStr = date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });

        const distanceKm = (activity.distance / 1000).toFixed(2);
        const durationMin = Math.floor(activity.moving_time / 60);
        const hours = Math.floor(durationMin / 60);
        const minutes = durationMin % 60;
        const durationStr = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;

        const elevation = Math.round(activity.total_elevation_gain || 0);

        const badgeClass = `badge-${activity.type.toLowerCase()}`;
        const hasMap = activity.map && activity.map.summary_polyline;

        return `
            <div class="activity-card bg-slate-900 border border-slate-700 rounded-lg p-4 hover:border-strava transition-colors">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center space-x-2 mb-2">
                            <span class="${badgeClass} px-2 py-1 rounded text-xs font-semibold">${activity.type}</span>
                            <h4 class="text-lg font-semibold text-white">${activity.name}</h4>
                        </div>

                        <p class="text-slate-400 text-sm mb-3">
                            ${dateStr} at ${timeStr}
                        </p>

                        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                            <div>
                                <p class="text-slate-500">Distance</p>
                                <p class="text-white font-semibold">${distanceKm} km</p>
                            </div>
                            <div>
                                <p class="text-slate-500">Duration</p>
                                <p class="text-white font-semibold">${durationStr}</p>
                            </div>
                            <div>
                                <p class="text-slate-500">Elevation</p>
                                <p class="text-white font-semibold">${elevation} m</p>
                            </div>
                            <div>
                                <p class="text-slate-500">Avg Speed</p>
                                <p class="text-white font-semibold">${(activity.average_speed * 3.6).toFixed(1)} km/h</p>
                            </div>
                        </div>
                    </div>

                    ${hasMap ? `
                        <button id="map-btn-${index}" class="ml-4 bg-strava hover:bg-orange-600 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
                            View Map
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    },

    /**
     * Handle refresh button click
     */
    async handleRefresh() {
        const refreshBtn = document.getElementById('refresh-btn');
        const refreshText = document.getElementById('refresh-text');
        const refreshSpinner = document.getElementById('refresh-spinner');

        try {
            // Show loading state
            if (refreshBtn) refreshBtn.disabled = true;
            if (refreshText) refreshText.classList.add('hidden');
            if (refreshSpinner) refreshSpinner.classList.remove('hidden');

            // Clear cache and reload
            await API.refreshCache();
            await this.loadData();

            // Update timestamp
            this.updateLastUpdated();

        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showError('Failed to refresh data.');

        } finally {
            // Reset button state
            if (refreshBtn) refreshBtn.disabled = false;
            if (refreshText) refreshText.classList.remove('hidden');
            if (refreshSpinner) refreshSpinner.classList.add('hidden');
        }
    },

    /**
     * Setup auto-refresh timer
     */
    setupAutoRefresh() {
        const interval = window.DASHBOARD_CONFIG?.autoRefreshInterval || 300000; // Default 5 minutes

        this.autoRefreshTimer = setInterval(() => {
            console.log('Auto-refreshing dashboard...');
            this.loadData();
        }, interval);
    },

    /**
     * Update last updated timestamp
     */
    updateLastUpdated() {
        const lastUpdatedEl = document.getElementById('last-updated');
        if (lastUpdatedEl) {
            const now = new Date();
            lastUpdatedEl.textContent = now.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    },

    /**
     * Show/hide loading state
     */
    showLoading(show) {
        const loadingEl = document.getElementById('loading-state');
        const contentEl = document.getElementById('dashboard-content');

        if (loadingEl) {
            loadingEl.classList.toggle('hidden', !show);
        }

        if (contentEl) {
            contentEl.classList.toggle('hidden', show);
        }
    },

    /**
     * Show error message
     */
    showError(message) {
        // Create error toast or use a more sophisticated notification system
        alert(message);
    },

    /**
     * Initialize goals system
     */
    initGoals() {
        // Populate year selector after data loads
        // Goals modal event handlers are set in setupEventListeners
    },

    /**
     * Populate year selector dropdown
     */
    populateYearSelector(yearlyStats) {
        const selector = document.getElementById('year-selector');
        if (!selector) return;

        // Clear existing options except "All Time"
        selector.innerHTML = '<option value="all">All Time</option>';

        // Add years in descending order
        const years = yearlyStats.map(ys => ys.year).sort((a, b) => b - a);
        years.forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            selector.appendChild(option);
        });

        // Store yearly data for quick access
        this.yearlyData = {};
        yearlyStats.forEach(ys => {
            this.yearlyData[ys.year] = ys;
        });
    },

    /**
     * Handle year selection change
     */
    handleYearChange(year) {
        this.selectedYear = year;

        if (year === 'all') {
            // Show all-time stats
            this.updateStats(this.stats.totals);
            this.updateStatsLabels('All-time');
        } else {
            // Show stats for selected year
            const yearData = this.yearlyData[year];
            if (yearData) {
                this.updateStats(yearData);
                this.updateStatsLabels(year);
            }
        }

        // Update goal progress
        this.updateGoalProgress();
    },

    /**
     * Update stat card labels
     */
    updateStatsLabels(label) {
        document.getElementById('stat-distance-label').textContent = label;
        document.getElementById('stat-count-label').textContent = label;
        document.getElementById('stat-time-label').textContent = label;
        document.getElementById('stat-elevation-label').textContent = label;
    },

    /**
     * Open goals modal
     */
    openGoalsModal() {
        const modal = document.getElementById('goals-modal');
        const yearSpan = document.getElementById('goals-year');

        if (modal) {
            // Set year in modal title
            const currentYear = this.selectedYear === 'all' ? new Date().getFullYear() : this.selectedYear;
            if (yearSpan) yearSpan.textContent = currentYear;

            // Load existing goals
            const goals = this.loadGoals(currentYear);
            document.getElementById('goal-distance').value = goals.distance || '';
            document.getElementById('goal-count').value = goals.count || '';
            document.getElementById('goal-time').value = goals.time || '';
            document.getElementById('goal-elevation').value = goals.elevation || '';

            modal.classList.remove('hidden');
        }
    },

    /**
     * Close goals modal
     */
    closeGoalsModal() {
        const modal = document.getElementById('goals-modal');
        if (modal) modal.classList.add('hidden');
    },

    /**
     * Save goals to localStorage
     */
    saveGoals() {
        const currentYear = this.selectedYear === 'all' ? new Date().getFullYear() : this.selectedYear;

        const goals = {
            distance: parseFloat(document.getElementById('goal-distance').value) || 0,
            count: parseFloat(document.getElementById('goal-count').value) || 0,
            time: parseFloat(document.getElementById('goal-time').value) || 0,
            elevation: parseFloat(document.getElementById('goal-elevation').value) || 0
        };

        localStorage.setItem(`strava_goals_${currentYear}`, JSON.stringify(goals));

        // Update goal progress display
        this.updateGoalProgress();
        this.closeGoalsModal();

        alert(`Goals saved for ${currentYear}!`);
    },

    /**
     * Clear goals
     */
    clearGoals() {
        const currentYear = this.selectedYear === 'all' ? new Date().getFullYear() : this.selectedYear;

        if (confirm(`Clear all goals for ${currentYear}?`)) {
            localStorage.removeItem(`strava_goals_${currentYear}`);

            // Clear form
            document.getElementById('goal-distance').value = '';
            document.getElementById('goal-count').value = '';
            document.getElementById('goal-time').value = '';
            document.getElementById('goal-elevation').value = '';

            // Update display
            this.updateGoalProgress();
        }
    },

    /**
     * Load goals from localStorage
     */
    loadGoals(year) {
        const stored = localStorage.getItem(`strava_goals_${year}`);
        return stored ? JSON.parse(stored) : {};
    },

    /**
     * Update goal progress bars
     */
    updateGoalProgress() {
        // Hide goals when viewing "All Time" since they're year-specific
        if (this.selectedYear === 'all') {
            this.updateSingleGoal('distance', 0, 0);
            this.updateSingleGoal('count', 0, 0);
            this.updateSingleGoal('time', 0, 0);
            this.updateSingleGoal('elevation', 0, 0);
            return;
        }

        const currentYear = this.selectedYear;
        const goals = this.loadGoals(currentYear);

        // Get current stats for the selected year
        const currentStats = this.yearlyData[this.selectedYear];
        if (!currentStats) return;

        // Distance goal
        this.updateSingleGoal('distance', goals.distance, currentStats.total_distance / 1000);

        // Activities goal
        this.updateSingleGoal('count', goals.count, currentStats.activity_count);

        // Time goal (convert seconds to hours)
        this.updateSingleGoal('time', goals.time, currentStats.total_time / 3600);

        // Elevation goal
        this.updateSingleGoal('elevation', goals.elevation, currentStats.total_elevation);
    },

    /**
     * Update a single goal's progress bar
     */
    updateSingleGoal(type, goal, current) {
        const goalDiv = document.getElementById(`${type}-goal`);
        const progressBar = document.getElementById(`${type}-progress`);
        const goalText = document.getElementById(`${type}-goal-text`);

        if (!goalDiv || !progressBar || !goalText) return;

        if (goal > 0) {
            // Show goal progress
            goalDiv.classList.remove('hidden');

            const percentage = Math.min((current / goal) * 100, 100);
            progressBar.style.width = `${percentage}%`;

            let unit = '';
            if (type === 'distance') unit = 'km';
            else if (type === 'time') unit = 'h';
            else if (type === 'elevation') unit = 'm';

            goalText.textContent = `Goal: ${goal.toFixed(0)}${unit} (${percentage.toFixed(0)}%)`;
        } else {
            // Hide goal progress
            goalDiv.classList.add('hidden');
        }
    }
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    Dashboard.init();
});

// Export for use in other modules
window.Dashboard = Dashboard;
