# Deployment Guide

This guide will help you deploy the Options Tracker application to free hosting platforms.

## Architecture

- **Backend (Flask)**: Deployed on Render.com
- **Frontend (React)**: Deployed on Vercel
- **Database**: PostgreSQL (free tier on Render)

## Prerequisites

1. GitHub account (free)
2. Render.com account (free)
3. Vercel account (free)
4. Git installed on your local machine

## Step 1: Set Up Version Control

### Initialize Git Repository

```bash
cd /Users/parthsoni/Documents/options-tracker
git init
git add .
git commit -m "Initial commit: Options Tracker application"
```

### Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it `options-tracker` (or your preferred name)
3. **Don't** initialize with README, .gitignore, or license (we already have these)
4. Copy the repository URL

### Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/options-tracker.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

**Note**: If you get a "Permission denied (publickey)" error, it means your remote is using SSH. Switch to HTTPS:
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/options-tracker.git
```

**Authentication**: When pushing via HTTPS, GitHub will prompt for:
- **Username**: Your GitHub username
- **Password**: Use a Personal Access Token (not your GitHub password)

To create a Personal Access Token:
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Name it (e.g., "Options Tracker Deployment")
4. Select scope: `repo` (full control)
5. Generate and copy the token
6. Use this token as your password when pushing

## Step 2: Deploy Backend to Render.com

### Create Render Account

1. Go to [Render.com](https://render.com)
2. Sign up with your GitHub account (recommended for easy deployment)

### Create PostgreSQL Database

1. In Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Name: `options-tracker-db`
3. Database: `options_tracker`
4. User: `options_tracker_user`
5. Region: Choose closest to you
6. Plan: **Free**
7. Click **"Create Database"**
8. Wait for database to be created
9. Copy the **Internal Database URL** (you'll need this)

### Deploy Backend Service

1. In Render dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub repository (`options-tracker`)
3. Configure the service:
   - **Name**: `options-tracker-api`
   - **Environment**: `Python 3`
   - **Python Version**: **IMPORTANT** - You have two options:
     - **Option A (Recommended)**: Manually set to **Python 3.11.9** in Render settings (Settings → Build & Deploy → Python Version)
     - **Option B**: Use Python 3.13 with pandas 2.2.3 (already updated in requirements.txt)
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Root Directory**: Leave empty (or set to root if needed)
   
   **Note**: If `runtime.txt` isn't being detected automatically, manually set the Python version in Render dashboard → Settings → Build & Deploy → Python Version dropdown.

4. Add Environment Variables:
   - `DATABASE_URL`: Paste the Internal Database URL from PostgreSQL
   - `JWT_SECRET_KEY`: Generate a secure random string (you can use: `openssl rand -hex 32`)
   - `FINNHUB_API_KEY`: `d525qj1r01qu5pvmiv2gd525qj1r01qu5pvmiv30`
   - `MAIL_SERVER`: `smtp.gmail.com`
   - `MAIL_PORT`: `587`
   - `MAIL_USE_TLS`: `true`
   - `MAIL_USERNAME`: `options.tracker.email.verify@gmail.com`
   - `MAIL_PASSWORD`: `gmjefaokgsjdlebd`
   - `MAIL_DEFAULT_SENDER`: `options.tracker.email.verify@gmail.com`
   - `FLASK_ENV`: `production`

5. Click **"Create Web Service"**
6. Wait for deployment to complete (5-10 minutes)
7. Copy the service URL (e.g., `https://options-tracker-api.onrender.com`) https://options-tracker-api-4pfx.onrender.com

### Initialize Database

After the backend is deployed, you need to initialize the database:

1. Go to your Render service dashboard
2. Click on **"Shell"** tab
3. Run:
   ```bash
   cd backend
   python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

## Step 3: Deploy Frontend to Vercel

### Create Vercel Account

1. Go to [Vercel.com](https://vercel.com)
2. Sign up with your GitHub account

### Deploy Frontend

1. In Vercel dashboard, click **"Add New..."** → **"Project"**
2. Import your GitHub repository (`options-tracker`)
3. Configure the project:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
   - **Install Command**: `npm install`

4. Add Environment Variable:
   - `REACT_APP_API_URL`: `https://options-tracker-api.onrender.com/api`
   (Replace with your actual Render backend URL)

5. Click **"Deploy"**
6. Wait for deployment to complete (2-5 minutes)
7. Your site will be live at a URL like `https://options-tracker-xxx.vercel.app`

## Step 4: Update CORS Settings

After deploying, you need to update CORS settings in the backend to allow your Vercel frontend URL.

1. Go to Render dashboard → Your backend service
2. Go to **"Environment"** tab
3. Add environment variable:
   - `FRONTEND_URL`: `https://your-vercel-app.vercel.app`
4. Update `backend/app.py` to use this environment variable for CORS

Or manually update `backend/app.py`:

```python
# In app.py, update CORS configuration:
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://your-vercel-app.vercel.app",
            "http://localhost:3000"  # For local development
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

Then commit and push:
```bash
git add backend/app.py
git commit -m "Update CORS for production"
git push
```

Render will automatically redeploy.

## Step 5: Continuous Deployment

Both Render and Vercel automatically deploy when you push to GitHub:

1. Make changes locally
2. Commit: `git add . && git commit -m "Your message"`
3. Push: `git push origin main`
4. Both services will automatically rebuild and deploy

## Troubleshooting

### Backend Issues

- **Database connection errors**: Check that `DATABASE_URL` is set correctly in Render environment variables
- **Import errors**: Make sure all dependencies are in `requirements.txt`
- **Port errors**: Render automatically sets `$PORT`, make sure your start command uses it
- **Pandas build errors**: If you see pandas compilation errors:
  - **Solution 1**: Manually set Python version in Render:
    1. Go to Render dashboard → Your service → Settings
    2. Under "Build & Deploy", find "Python Version" dropdown
    3. Select **Python 3.11.9** (or 3.12.x)
    4. Save and redeploy
  - **Solution 2**: Use pandas 2.2.3+ which supports Python 3.13 (already updated in requirements.txt)
  - **Solution 3**: If `runtime.txt` isn't detected, ensure it's in the root directory and commit/push it, then manually set Python version in Render settings

### Frontend Issues

- **API connection errors**: Verify `REACT_APP_API_URL` is set correctly in Vercel
- **Build errors**: Check Vercel build logs for specific errors
- **CORS errors**: Make sure your Vercel URL is added to backend CORS settings

### Database Migration

If you need to update the database schema:

1. Update your models in `backend/models.py`
2. In Render shell, run:
   ```bash
   cd backend
   python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

## Environment Variables Summary

### Backend (Render)
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `FINNHUB_API_KEY` - API key for market data
- `MAIL_*` - Email configuration
- `FRONTEND_URL` - Frontend URL for CORS

### Frontend (Vercel)
- `REACT_APP_API_URL` - Backend API URL

## Cost

All services are **FREE**:
- Render: Free tier (spins down after 15 min inactivity, but free)
- Vercel: Free tier (generous limits)
- PostgreSQL: Free tier on Render (limited but sufficient for small apps)

## Next Steps

1. Set up a custom domain (optional, both services support it)
2. Monitor usage and upgrade if needed
3. Set up error tracking (e.g., Sentry - free tier)
4. Configure backups for database (Render provides automatic backups on paid plans)

