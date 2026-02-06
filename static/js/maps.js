// Maps Module - Leaflet.js map rendering for activity routes

const Maps = {
    map: null,
    currentPolyline: null,

    /**
     * Initialize the map modal
     */
    initModal() {
        const modal = document.getElementById('map-modal');
        const closeBtn = document.getElementById('close-map-modal');

        // Close modal on button click
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeModal());
        }

        // Close modal on outside click
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal();
                }
            });
        }

        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                this.closeModal();
            }
        });
    },

    /**
     * Show activity route on map
     */
    showRoute(activity) {
        const modal = document.getElementById('map-modal');
        const titleEl = document.getElementById('map-modal-title');
        const mapContainer = document.getElementById('map-container');

        if (!activity.map || !activity.map.summary_polyline) {
            alert('No map data available for this activity');
            return;
        }

        // Set modal title
        if (titleEl) {
            titleEl.textContent = activity.name || 'Activity Route';
        }

        // Show modal
        if (modal) {
            modal.classList.remove('hidden');
        }

        // Initialize map if not already done
        if (!this.map) {
            this.initMap();
        }

        // Decode polyline and render route
        const coordinates = this.decodePolyline(activity.map.summary_polyline);

        if (coordinates.length > 0) {
            this.renderRoute(coordinates);
        } else {
            console.error('Failed to decode polyline');
        }
    },

    /**
     * Initialize Leaflet map
     */
    initMap() {
        const mapContainer = document.getElementById('map-container');

        if (!mapContainer) return;

        // Create map centered on default location
        this.map = L.map(mapContainer, {
            zoomControl: true,
            attributionControl: true
        }).setView([0, 0], 2);

        // Add dark theme tile layer
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '© OpenStreetMap contributors © CARTO',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(this.map);
    },

    /**
     * Render route on map
     */
    renderRoute(coordinates) {
        if (!this.map) return;

        // Remove existing polyline
        if (this.currentPolyline) {
            this.map.removeLayer(this.currentPolyline);
        }

        // Add new polyline
        this.currentPolyline = L.polyline(coordinates, {
            color: '#FC4C02',
            weight: 3,
            opacity: 0.8,
            smoothFactor: 1
        }).addTo(this.map);

        // Fit map bounds to route
        const bounds = this.currentPolyline.getBounds();
        this.map.fitBounds(bounds, { padding: [50, 50] });

        // Add start and end markers
        if (coordinates.length > 0) {
            const startIcon = L.divIcon({
                className: 'custom-marker',
                html: '<div style="background-color: #10b981; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>',
                iconSize: [12, 12]
            });

            const endIcon = L.divIcon({
                className: 'custom-marker',
                html: '<div style="background-color: #ef4444; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>',
                iconSize: [12, 12]
            });

            L.marker(coordinates[0], { icon: startIcon }).addTo(this.map);
            L.marker(coordinates[coordinates.length - 1], { icon: endIcon }).addTo(this.map);
        }

        // Invalidate size to handle any layout issues
        setTimeout(() => {
            if (this.map) {
                this.map.invalidateSize();
            }
        }, 100);
    },

    /**
     * Close map modal
     */
    closeModal() {
        const modal = document.getElementById('map-modal');
        if (modal) {
            modal.classList.add('hidden');
        }

        // Clear map
        if (this.currentPolyline && this.map) {
            this.map.removeLayer(this.currentPolyline);
            this.currentPolyline = null;
        }
    },

    /**
     * Decode Google polyline encoding
     * Algorithm from: https://developers.google.com/maps/documentation/utilities/polylinealgorithm
     */
    decodePolyline(encoded) {
        if (!encoded) return [];

        const coordinates = [];
        let index = 0;
        let lat = 0;
        let lng = 0;

        while (index < encoded.length) {
            // Decode latitude
            let b;
            let shift = 0;
            let result = 0;

            do {
                b = encoded.charCodeAt(index++) - 63;
                result |= (b & 0x1f) << shift;
                shift += 5;
            } while (b >= 0x20);

            const dlat = ((result & 1) ? ~(result >> 1) : (result >> 1));
            lat += dlat;

            // Decode longitude
            shift = 0;
            result = 0;

            do {
                b = encoded.charCodeAt(index++) - 63;
                result |= (b & 0x1f) << shift;
                shift += 5;
            } while (b >= 0x20);

            const dlng = ((result & 1) ? ~(result >> 1) : (result >> 1));
            lng += dlng;

            coordinates.push([lat / 1e5, lng / 1e5]);
        }

        return coordinates;
    }
};

// Export for use in other modules
window.Maps = Maps;
