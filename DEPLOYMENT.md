# PythonAnywhere Deployment Guide

## Quick Deploy Steps

### 1. Create ZIP file (on local machine)

Create a ZIP file excluding unnecessary files:
- Exclude: `cache/`, `__pycache__/`, `.env`, `*.pyc`, `venv/`
- Include: All app files, templates, static, requirements.txt

### 2. Upload to PythonAnywhere

1. Log into PythonAnywhere: https://www.pythonanywhere.com
2. Go to **Files** tab
3. Navigate to your home directory
4. Click **Upload a file** and upload your ZIP
5. Open a Bash console and extract:
   ```bash
   unzip Strava-Live-Stats.zip -d strava-dashboard
   cd strava-dashboard
   ```

### 3. Create Virtual Environment

```bash
mkvirtualenv --python=/usr/bin/python3.10 strava-env
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file:
```bash
nano .env
```

Paste your credentials:
```
STRAVA_CLIENT_ID=195807
STRAVA_CLIENT_SECRET=3ba01f8e82bfebf3115e91d91c3fdfcf0a4fb935
STRAVA_REDIRECT_URI=https://YOURUSERNAME.pythonanywhere.com/authorized
SECRET_KEY=3ba01f8e82bfebf3115e91d91c3fdfcf0a4fb935
FLASK_ENV=production
```

**IMPORTANT**: Update `STRAVA_REDIRECT_URI` with your actual PythonAnywhere username!

### 5. Create Cache Directory

```bash
mkdir -p cache
```

### 6. Configure Web App

1. Go to **Web** tab in PythonAnywhere
2. Click **Add a new web app**
3. Choose **Manual configuration** (not Flask wizard)
4. Choose **Python 3.10**

### 7. Configure WSGI File

Click on the WSGI configuration file link and replace contents with:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOURUSERNAME/strava-dashboard'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables from .env
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Import your Flask app
from flask_app import app as application
```

**IMPORTANT**: Replace `YOURUSERNAME` with your actual PythonAnywhere username!

### 8. Configure Virtual Environment

In the Web tab:
1. Find the **Virtualenv** section
2. Enter the path: `/home/YOURUSERNAME/.virtualenvs/strava-env`
3. Replace `YOURUSERNAME` with your actual username

### 9. Update Strava API Settings

1. Go to https://www.strava.com/settings/api
2. Update **Authorization Callback Domain** to: `yourusername.pythonanywhere.com`
3. Click **Update**

### 10. Reload Web App

1. Click the green **Reload** button in PythonAnywhere Web tab
2. Visit: `https://yourusername.pythonanywhere.com`

---

## Troubleshooting

### Check Error Logs
In PythonAnywhere Web tab:
- Click on **Error log** link
- Click on **Server log** link

### Common Issues

1. **ImportError**: Virtual environment not configured correctly
   - Double-check virtualenv path in Web tab

2. **Template not found**: WSGI file path incorrect
   - Verify `project_home` path in WSGI file

3. **OAuth fails**: Redirect URI mismatch
   - Check `.env` has correct PythonAnywhere URL
   - Verify Strava API settings match

4. **Cache errors**: Cache directory doesn't exist
   - Run: `mkdir -p cache` in project directory

### Test OAuth Flow
1. Visit your site
2. Click "Connect with Strava"
3. Authorize the app
4. Should redirect to dashboard with your data

---

## File Structure on PythonAnywhere

```
/home/YOURUSERNAME/
└── strava-dashboard/
    ├── app/
    ├── static/
    ├── templates/
    ├── cache/               # Create this
    ├── .env                 # Create this
    ├── flask_app.py
    ├── config.py
    └── requirements.txt
```

---

## Updating Your App

To update after making local changes:

1. Create new ZIP with updated files
2. Upload to PythonAnywhere
3. Extract over existing files:
   ```bash
   cd ~/strava-dashboard
   unzip -o ~/Strava-Live-Stats.zip
   ```
4. Reload web app in Web tab

---

## Production Considerations

1. **Change SECRET_KEY**: Use a unique, random secret key in production
2. **Rate Limits**: Strava allows 100 req/15min, 1000 req/day
3. **Cache**: Set to 5 minutes to minimize API calls
4. **HTTPS**: PythonAnywhere provides free HTTPS automatically

---

## Alternative: Git Deployment

If you have Git:

```bash
# On PythonAnywhere
cd ~
git clone YOUR_REPO_URL strava-dashboard
cd strava-dashboard
mkvirtualenv --python=/usr/bin/python3.10 strava-env
pip install -r requirements.txt
```

Then follow steps 4-10 above.
