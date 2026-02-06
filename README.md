# Strava Live Stats Dashboard

A modern, feature-rich dashboard for visualizing your Strava fitness data with beautiful charts, interactive maps, and real-time updates.

## Features

- **Modern Dark Theme** - Beautiful slate-colored interface with Strava orange accents
- **Interactive Charts** - Distance over time, pace trends, and activity type breakdown using Chart.js
- **Activity Maps** - View your routes on interactive maps powered by Leaflet.js
- **Real-time Updates** - Auto-refresh every 5 minutes to keep your dashboard current
- **Advanced Filtering** - Filter by activity type, date range, distance, and search
- **Personal Records** - Track your longest runs, fastest pace, and highest elevations
- **Statistics** - Weekly and monthly summaries with totals and averages
- **Smart Caching** - Reduces API calls and respects Strava rate limits

## Technology Stack

**Backend:**
- Flask 3.0 with modular blueprint architecture
- Flask-Caching for filesystem-based caching
- python-dotenv for configuration
- polyline for map route decoding

**Frontend:**
- Tailwind CSS (CDN) for responsive dark theme
- Chart.js for data visualization
- Leaflet.js for map rendering
- Vanilla JavaScript (no framework overhead)

## Project Structure

```
Strava Live Stats/
├── flask_app.py              # Entry point
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── flask_app.backup.py       # Original backup
│
├── app/                      # Application package
│   ├── __init__.py          # App factory
│   ├── auth.py              # OAuth & token management
│   ├── strava_api.py        # Strava API wrapper
│   ├── cache.py             # Caching layer
│   ├── stats.py             # Statistics calculations
│   ├── utils.py             # Utility functions
│   └── routes/              # Route blueprints
│       ├── main.py          # Dashboard routes
│       ├── auth_routes.py   # OAuth routes
│       └── api.py           # JSON API endpoints
│
├── static/                  # Static assets
│   ├── css/
│   │   └── custom.css       # Dark theme styles
│   └── js/
│       ├── api-client.js    # API wrapper
│       ├── dashboard.js     # Main orchestrator
│       ├── charts.js        # Chart configurations
│       ├── maps.js          # Map rendering
│       └── filters.js       # Filter management
│
└── templates/               # Jinja2 templates
    ├── base.html           # Base template
    ├── index.html          # Landing page
    ├── dashboard.html      # Main dashboard
    └── auth/
        └── error.html      # OAuth error page
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file (or set environment variables):

```env
# Required
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret

# Optional (defaults provided)
STRAVA_REDIRECT_URI=http://localhost:5000/authorized
SECRET_KEY=your-secret-key
FLASK_ENV=development
```

### 3. Run Locally

```bash
python flask_app.py
```

Visit `http://localhost:5000` and click "Connect with Strava" to authorize.

### 4. Deploy to PythonAnywhere

1. Upload all files to PythonAnywhere
2. Create a virtual environment:
   ```bash
   mkvirtualenv strava-env
   pip install -r requirements.txt
   ```
3. Create the cache directory:
   ```bash
   mkdir cache
   ```
4. Update your WSGI configuration file:
   ```python
   import sys
   path = '/home/yourusername/Strava Live Stats'
   if path not in sys.path:
       sys.path.append(path)

   from flask_app import app as application
   ```
5. Set environment variables in the WSGI configuration or `.env` file
6. Update `STRAVA_REDIRECT_URI` to your PythonAnywhere URL:
   ```
   https://yourusername.pythonanywhere.com/authorized
   ```
7. Update the redirect URI in your Strava API application settings

## API Endpoints

### Frontend Routes

- `GET /` - Landing page
- `GET /dashboard` - Main dashboard (requires auth)
- `GET /authorize` - Redirect to Strava OAuth
- `GET /authorized` - OAuth callback
- `GET /logout` - Disconnect Strava account

### API Routes (JSON)

- `GET /api/activities` - Get activities with optional filters
  - Query params: `type`, `start_date`, `end_date`, `min_distance`, `max_distance`, `search`, `page`, `per_page`
- `GET /api/activity/<id>` - Get activity details
- `GET /api/stats` - Get calculated statistics
- `GET /api/stats/weekly` - Get weekly summaries
- `GET /api/stats/monthly` - Get monthly summaries
- `POST /api/refresh` - Force refresh cached data

## Configuration

### Cache Settings

Default cache TTLs (can be modified in [config.py](config.py)):
- Activity list: 5 minutes
- Activity details: 30 minutes
- Statistics: 5 minutes

### Auto-refresh

Dashboard auto-refreshes every 5 minutes. Modify `AUTO_REFRESH_INTERVAL` in [config.py](config.py) (value in milliseconds).

### Rate Limits

The app respects Strava's rate limits:
- 100 requests per 15 minutes
- 1000 requests per day

Caching helps stay well within these limits.

## Key Features Implementation

### Dark Theme

- Slate color palette (bg-slate-900, 800, 700)
- Strava orange (#FC4C02) accents
- Custom scrollbars and animations
- Responsive mobile-first design

### Charts

1. **Distance Over Time** - Line chart showing km per activity
2. **Activity Type Breakdown** - Doughnut chart by activity type
3. **Pace Trends** - Line chart for run pace (reversed Y-axis, lower is better)

All charts use dark theme colors and responsive configurations.

### Maps

- Dark theme Carto tiles
- Polyline decoding for Strava routes
- Start (green) and end (red) markers
- Modal overlay for expanded view

### Filters

- Activity type dropdown (Run, Ride, Swim, Walk, Hike)
- Date range pickers
- Distance range inputs
- Text search for activity names
- URL parameter support for shareable filtered views

## Development

### Running in Debug Mode

```bash
# Set environment
export FLASK_ENV=development

# Run with debug mode
python flask_app.py
```

### Testing OAuth Flow

1. Visit `/authorize`
2. Authorize on Strava
3. Verify redirect to dashboard
4. Check that activities and stats load

### Cache Management

The `cache/` directory stores cached API responses. Delete this directory to force fresh API calls.

## Troubleshooting

### Common Issues

**"Authentication required" error**
- Check that your Strava credentials are correct in `.env`
- Verify the redirect URI matches your Strava app settings
- Try reconnecting via `/authorize`

**"Rate limit exceeded" error**
- Wait 15 minutes before making more requests
- Check that caching is working (cache directory should have files)

**Charts not displaying**
- Check browser console for JavaScript errors
- Verify Chart.js CDN is loading
- Ensure stats API endpoint returns data

**Maps not showing**
- Verify Leaflet.js CDN is loading
- Check that activity has `map.summary_polyline` data
- Indoor activities may not have map data

### Logs

Check logs for debugging:
- Flask logs in terminal/console
- Browser console for JavaScript errors
- Network tab for API requests

## Browser Compatibility

Tested and working on:
- Chrome/Edge (recommended)
- Firefox
- Safari
- Mobile browsers (iOS Safari, Chrome Android)

## Future Enhancements

Potential features for future versions:
- Goal setting and progress tracking
- Segment analysis
- Social features (kudos, comments)
- Export to CSV/PDF
- Strava webhooks for real-time updates
- Multiple athlete accounts
- AI-powered training insights
- Gear tracking
- Weather integration

## Credits

- Built with Flask and Tailwind CSS
- Charts by Chart.js
- Maps by Leaflet.js
- Data from Strava API

## License

This is a personal project for educational purposes. Strava is a registered trademark of Strava, Inc.

---

**Enjoy your fancy new dashboard!** 🎉

For issues or questions, refer to the inline code comments or check the Strava API documentation at https://developers.strava.com/
