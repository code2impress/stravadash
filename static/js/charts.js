// Charts Module - Chart.js configurations for dark theme

const Charts = {
    instances: {
        distance: null,
        type: null,
        pace: null
    },

    // Common dark theme configuration
    darkThemeDefaults: {
        color: '#cbd5e1',
        borderColor: '#475569',
        backgroundColor: 'rgba(252, 76, 2, 0.1)',
        gridColor: '#334155'
    },

    /**
     * Initialize all charts
     */
    init(chartData) {
        this.createDistanceChart(chartData.distance_over_time);
        this.createTypeChart(chartData.activity_type_breakdown);
        this.createPaceChart(chartData.pace_trends);
    },

    /**
     * Create Distance Over Time Line Chart
     */
    createDistanceChart(data) {
        const ctx = document.getElementById('distance-chart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (this.instances.distance) {
            this.instances.distance.destroy();
        }

        this.instances.distance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: 'Distance (km)',
                    data: data.map(d => d.distance),
                    borderColor: '#FC4C02',
                    backgroundColor: 'rgba(252, 76, 2, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#FC4C02',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#cbd5e1',
                        borderColor: '#475569',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: (context) => {
                                const activity = data[context.dataIndex];
                                return [
                                    `${activity.name}`,
                                    `Distance: ${activity.distance.toFixed(2)} km`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: '#334155',
                            display: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            maxRotation: 45,
                            minRotation: 45
                        }
                    },
                    y: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8',
                            callback: (value) => value.toFixed(1) + ' km'
                        }
                    }
                }
            }
        });
    },

    /**
     * Create Activity Type Breakdown Doughnut Chart
     */
    createTypeChart(data) {
        const ctx = document.getElementById('type-chart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.instances.type) {
            this.instances.type.destroy();
        }

        const colors = {
            'Run': '#10b981',
            'Ride': '#3b82f6',
            'Swim': '#06b6d4',
            'Walk': '#8b5cf6',
            'Hike': '#f59e0b',
            'default': '#64748b'
        };

        const backgroundColors = data.map(d => colors[d.type] || colors.default);

        this.instances.type = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.type),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: backgroundColors,
                    borderColor: '#1e293b',
                    borderWidth: 2,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#cbd5e1',
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#cbd5e1',
                        borderColor: '#475569',
                        borderWidth: 1,
                        padding: 12,
                        callbacks: {
                            label: (context) => {
                                const type = data[context.dataIndex];
                                return [
                                    `${type.type}: ${type.count} activities`,
                                    `${type.distance.toFixed(1)} km total`
                                ];
                            }
                        }
                    }
                }
            }
        });
    },

    /**
     * Create Pace Trends Line Chart (Runs only)
     */
    createPaceChart(data) {
        const ctx = document.getElementById('pace-chart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.instances.pace) {
            this.instances.pace.destroy();
        }

        // Convert pace from seconds/km to minutes/km
        const paceData = data.map(d => d.pace / 60);

        this.instances.pace = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: 'Pace (min/km)',
                    data: paceData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#3b82f6',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#cbd5e1',
                        borderColor: '#475569',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: (context) => {
                                const run = data[context.dataIndex];
                                const paceMinutes = Math.floor(run.pace / 60);
                                const paceSeconds = Math.floor(run.pace % 60);
                                return [
                                    `${run.name}`,
                                    `Pace: ${paceMinutes}:${paceSeconds.toString().padStart(2, '0')} /km`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: '#334155',
                            display: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            maxRotation: 45,
                            minRotation: 45
                        }
                    },
                    y: {
                        reverse: true, // Lower pace is better
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8',
                            callback: (value) => {
                                const minutes = Math.floor(value);
                                const seconds = Math.floor((value - minutes) * 60);
                                return `${minutes}:${seconds.toString().padStart(2, '0')}`;
                            }
                        }
                    }
                }
            }
        });
    },

    /**
     * Update charts with new data
     */
    update(chartData) {
        this.init(chartData);
    },

    /**
     * Destroy all charts
     */
    destroy() {
        Object.values(this.instances).forEach(chart => {
            if (chart) chart.destroy();
        });
    }
};

// Export for use in other modules
window.Charts = Charts;
