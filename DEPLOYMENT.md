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
   - **Python Version**: **CRITICAL** - Add environment variable `PYTHON_VERSION` = `3.11.9` (see step 4 below)
     
     **Why**: `psycopg2-binary` (PostgreSQL driver) does NOT support Python 3.13. Setting `PYTHON_VERSION` environment variable ensures Render uses Python 3.11.9.
     
     **Note**: While `runtime.txt` in the repository root can also specify the Python version, the `PYTHON_VERSION` environment variable is more reliable and works even if the service was created before `runtime.txt` was added.
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Root Directory**: Leave empty (or set to root if needed)

4. Add Environment Variables:
   - `PYTHON_VERSION`: `3.11.9` ⚠️ **CRITICAL** - This ensures Python 3.11.9 is used (required for psycopg2-binary compatibility)
   - `DATABASE_URL`: Paste the Internal Database URL from PostgreSQL
   - `JWT_SECRET_KEY`: Generate a secure random string (you can use: `openssl rand -hex 32`)
   - `FINNHUB_API_KEY`: `d525qj1r01qu5pvmiv2gd525qj1r01qu5pvmiv30`
   - `SENDGRID_API_KEY`: Your SendGrid API key (see "Email Setup with SendGrid" section below)
   - `SENDGRID_FROM_EMAIL`: The verified sender email in SendGrid (e.g., `noreply@yourdomain.com` or your verified email)
   - `FLASK_ENV`: `production`
   
   **Note**: Render's free tier blocks SMTP ports, so we use SendGrid (HTTP-based) instead. See "Email Setup with SendGrid" section below.

5. Click **"Create Web Service"**
6. Wait for deployment to complete (5-10 minutes)
7. Copy the service URL (e.g., `https://options-tracker-api.onrender.com`) https://options-tracker-api-4pfx.onrender.com

### Initialize Database

**Good news!** The database will be automatically initialized when the app starts. The Flask application includes automatic database initialization that:

1. Creates all required tables on first startup
2. Runs migrations to add any missing columns
3. Works automatically with gunicorn (no shell access needed)

**No manual steps required!** Just deploy and the database will be ready.

**Alternative (if needed)**: If you need to manually trigger initialization, you can call the `/api/init-db` endpoint (requires authentication) after logging in.

### Email Setup with SendGrid

**Important**: Render's free tier blocks outbound SMTP connections (ports 25, 465, 587), so we use SendGrid's HTTP-based API instead.

#### Step 2.5.1: Create SendGrid Account

1. Go to [SendGrid.com](https://sendgrid.com)
2. Click **"Start for Free"** or **"Sign Up"**
3. Complete the signup process (free tier includes 100 emails/day)
4. Verify your email address

#### Step 2.5.2: Create API Key

1. In SendGrid dashboard, go to **Settings** → **API Keys** (or search for "API Keys")
2. Click **"Create API Key"**
3. Give it a name (e.g., "Options Tracker Production")
4. Select **"Full Access"** or **"Restricted Access"** with "Mail Send" permissions
5. Click **"Create & View"**
6. **Copy the API key immediately** (you won't be able to see it again!)
7. Paste it as `SENDGRID_API_KEY` in Render environment variables

#### Step 2.5.3: Verify Sender Email

1. In SendGrid dashboard, go to **Settings** → **Sender Authentication**
2. Click **"Verify a Single Sender"** (for testing) or **"Authenticate Your Domain"** (for production)
3. For single sender:
   - Enter your email address (e.g., `noreply@yourdomain.com` or use your personal email)
   - Fill in the required information
   - Check your email and click the verification link
4. Use this verified email as `SENDGRID_FROM_EMAIL` in Render environment variables

**Note**: For local development, you can still use Flask-Mail with Gmail SMTP. SendGrid is only required for production on Render's free tier.

## Step 3: Deploy Frontend to Vercel

> **Note**: Vercel's UI may change over time. If the interface looks different, refer to [Vercel's official documentation](https://vercel.com/docs) for the most current instructions. The key steps remain the same: import repository, set root directory to `frontend`, add environment variables, and deploy.

### Create Vercel Account

1. Go to [Vercel.com](https://vercel.com)
2. Click **"Sign Up"** (typically top right corner)
3. Choose **"Continue with GitHub"** (recommended for automatic deployments)
4. Authorize Vercel to access your GitHub repositories when prompted
5. You'll be redirected to the Vercel dashboard

### Deploy Frontend

#### Step 3.1: Import Your Repository

1. In the Vercel dashboard, look for and click the **"New Project"** or **"Add New..."** button
   - This button is typically at the top of the dashboard
   - The exact wording may vary - look for buttons like "New Project", "Add New...", or a "+" icon

2. You'll see options to import from Git providers (GitHub, GitLab, Bitbucket)
   - Select **GitHub** (or the provider where your repository is hosted)
   - If this is your first time, you may need to authorize Vercel to access your repositories

3. Find and select your `options-tracker` repository from the list
   - You can use the search bar if you have many repositories
   - Click on the repository name or the **"Import"** button next to it

4. If you don't see your repository:
   - Look for **"Configure GitHub App"** or **"Adjust GitHub App Permissions"**
   - Make sure you grant access to your repository (or all repositories)
   - Refresh the page and try again

#### Step 3.2: Configure Project Settings

After importing, you'll see the **"Configure Project"** page. Configure as follows:

1. **Project Name** (optional):
   - You can leave it as `options-tracker` or change it
   - This will be part of your deployment URL

2. **Framework Preset**:
   - Vercel should auto-detect **"Create React App"**
   - If not, manually select it from the dropdown

3. **Root Directory** ⚠️ **CRITICAL**:
   - Look for **"Root Directory"** or **"Project Root"** setting
   - The default is usually `./` (which means root of repository)
   - Click **"Edit"**, the input field, or a pencil icon next to it
   - Change from `./` to `frontend`
   - Press Enter or click outside to save
   - **This is very important!** Without this, Vercel won't find your React app and the build will fail

4. **Build and Output Settings** (should auto-populate):
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
   - **Install Command**: `npm install`
   - Verify these are correct (they should be by default)

#### Step 3.3: Add Environment Variables

1. Look for the **"Environment Variables"** section on the configuration page
   - It may be collapsible - click to expand if you see a chevron or arrow
   - Sometimes it's labeled as **"Environment Variables"** or in an **"Advanced"** section
   - Scroll down if you don't see it immediately

2. Click **"Add"**, **"Add Variable"**, **"Add Environment Variable"**, or click in the input field
   - The exact button text may vary

3. Add your environment variable:
   - **Variable Name** or **Key**: Enter `REACT_APP_API_URL`
   - **Value**: Enter `https://your-backend-url.onrender.com/api`
     - **Replace `your-backend-url`** with your actual Render backend URL from Step 2
     - Example: If your Render URL is `https://options-tracker-api-4pfx.onrender.com`
     - Then the value should be: `https://options-tracker-api-4pfx.onrender.com/api`
   
   - **Environments**: Select all three checkboxes:
     - ✅ **Production** (for production deployments)
     - ✅ **Preview** (for pull request previews)
     - ✅ **Development** (for local development with `vercel dev`)
   
   - Click **"Add"**, **"Save"**, or press Enter

4. Verify the variable appears in the list below with all three environments checked

#### Step 3.4: Deploy

1. Review all settings one more time:
   - Framework: Create React App
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `build`
   - Environment Variable: `REACT_APP_API_URL` set correctly

2. Click the **"Deploy"** button
   - Usually a large, prominent button (often blue or colored) at the bottom of the configuration page
   - The exact location may vary, but it's typically clearly visible

3. **Deployment Process**:
   - You'll see a deployment log showing:
     - Installing dependencies (`npm install`)
     - Building the project (`npm run build`)
     - Uploading files
     - Deployment complete
   - This typically takes 2-5 minutes

4. **Success!**:
   - You'll see a success message
   - Your site URL will be displayed (e.g., `https://options-tracker-xxx.vercel.app`)
   - Click **"Visit"** to open your live site

#### Step 3.5: Verify Deployment

1. Click on your deployment URL or look for a **"Visit"**, **"Open"**, or **"View"** button
2. Your Options Tracker landing page should load in a new tab/window
3. **Test the connection**:
   - Try clicking "Register" or "Login"
   - Check if forms load correctly
   - Open browser DevTools (press F12) → Go to **Console** tab
   - Look for any error messages (CORS errors are expected until Step 4)
4. **Common checks**:
   - ✅ Page loads without errors
   - ✅ Navigation works
   - ✅ Forms are displayed correctly
   - ⚠️ CORS errors in console are normal - we'll fix these in Step 4

#### Step 3.6: Save Your Frontend URL

**Important**: Copy your Vercel deployment URL (e.g., `https://options-tracker-xxx.vercel.app`). You'll need it for the next step to update CORS settings.

## Step 4: Update CORS Settings

After deploying the frontend, you need to update the backend CORS settings to allow your Vercel frontend URL.

### Step 4.1: Add FRONTEND_URL Environment Variable

1. Go to **Render dashboard** → Click on your backend service (`options-tracker-api`)
2. Click on the **"Environment"** tab (in the left sidebar)
3. Scroll down to the **"Environment Variables"** section
4. Click **"Add Environment Variable"** button
5. Add the following:
   - **Key**: `FRONTEND_URL`
   - **Value**: `https://your-vercel-app.vercel.app` (paste your Vercel URL from Step 3.6)
   - Example: `https://options-tracker-xxx.vercel.app`
6. Click **"Save Changes"**

### Step 4.2: Verify CORS Configuration

The `backend/app.py` file already uses the `FRONTEND_URL` environment variable for CORS. You can verify this by checking that the code includes:

```python
frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
allowed_origins = [frontend_url]
```

If you haven't deployed the latest version of `app.py` with CORS configuration:
1. Make sure your code is up to date and committed
2. Push to GitHub:
   ```bash
   git add backend/app.py
   git commit -m "Update CORS configuration"
   git push origin main
   ```

### Step 4.3: Redeploy Backend

1. After adding the `FRONTEND_URL` environment variable, Render will automatically trigger a redeploy
2. Wait for the redeployment to complete (about 2-3 minutes)
3. Check the logs to ensure it deployed successfully

### Step 4.4: Test the Connection

1. Go to your Vercel frontend URL
2. Try to register a new account or log in
3. If you see CORS errors in the browser console, double-check:
   - `FRONTEND_URL` environment variable is set correctly in Render
   - The value matches your exact Vercel URL (including `https://`)
   - The backend has been redeployed after adding the variable

## Step 5: Continuous Deployment

Both Render and Vercel automatically deploy when you push to GitHub:

### How It Works:

1. **Make changes locally** to your code
2. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Your descriptive commit message"
   ```
3. **Push to GitHub**:
   ```bash
   git push origin main
   ```
4. **Automatic deployments trigger**:
   - **Render (Backend)**: Detects the push and automatically starts a new build and deployment
   - **Vercel (Frontend)**: Detects the push and automatically starts a new build and deployment
   - Both services will send you notifications when deployments complete

### Monitoring Deployments:

- **Render**: Check your service dashboard → "Events" or "Logs" tab to see deployment progress
- **Vercel**: Check your project dashboard → "Deployments" tab to see all deployments and their status

### Deployment URLs:

- Both services use the same URLs for all deployments
- Vercel also creates preview deployments for pull requests (if you use branches)
- Production deployments are always on your main URL

### Rollback (if needed):

- **Vercel**: Go to Deployments → Click on a previous deployment → Click "Promote to Production"
- **Render**: Go to Events → Find a previous successful deployment → Click "Rollback to this deploy"

## Troubleshooting

### Backend Issues

- **Database connection errors**: Check that `DATABASE_URL` is set correctly in Render environment variables
- **Import errors**: Make sure all dependencies are in `requirements.txt`
- **Port errors**: Render automatically sets `$PORT`, make sure your start command uses it
- **Pandas build errors**: If you see pandas compilation errors:
  - **Solution**: Manually set Python version in Render to Python 3.11.9 or 3.12.x (see below)

- **psycopg2 ImportError with Python 3.13**: If you see `undefined symbol: _PyInterpreterState_Get` error:
  - **Root Cause**: `psycopg2-binary` does not support Python 3.13
  - **Solution**: Add environment variable `PYTHON_VERSION` = `3.11.9` in Render:
    1. Go to Render dashboard → Your service → **Environment** tab
    2. Click **"Add Environment Variable"**
    3. Key: `PYTHON_VERSION`
    4. Value: `3.11.9`
    5. Click **"Save Changes"**
    6. Render will automatically redeploy with Python 3.11.9
    7. Verify in build logs that it says "Using Python 3.11.9" (not 3.13)
    8. This will fix both pandas and psycopg2-binary compatibility issues

### Frontend Issues

- **API connection errors**: 
  - Verify `REACT_APP_API_URL` is set correctly in Vercel Environment Variables
  - Check that the URL includes `/api` at the end (e.g., `https://backend.onrender.com/api`)
  - Verify the backend is running and accessible (test the health endpoint)
  
- **Build errors**: 
  - Check Vercel build logs for specific error messages
  - Common issues:
    - Missing dependencies: Ensure all packages are in `package.json`
    - TypeScript errors: Check for type mismatches
    - Import errors: Verify all file paths are correct
  - Try building locally first: `cd frontend && npm run build`
  
- **CORS errors**: 
  - Make sure `FRONTEND_URL` environment variable is set in Render backend
  - Verify the Vercel URL matches exactly (including `https://`)
  - Check that backend has been redeployed after adding `FRONTEND_URL`
  - Check browser console for specific CORS error messages
  
- **404 errors on page refresh**:
  - This is normal for React Router - Vercel handles it automatically via `vercel.json`
  - If you see 404s, make sure `vercel.json` is in the root directory
  
- **Environment variables not working**:
  - Remember: Environment variables must start with `REACT_APP_` to be accessible in React
  - After adding/changing environment variables, you must redeploy
  - Check Vercel project settings → Environment Variables to verify they're set

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
- `SENDGRID_API_KEY` - SendGrid API key for sending emails (required for production)
- `SENDGRID_FROM_EMAIL` - Verified sender email address in SendGrid
- `FRONTEND_URL` - Frontend URL for CORS

### Frontend (Vercel)
- `REACT_APP_API_URL` - Backend API URL (e.g., `https://options-tracker-api-4pfx.onrender.com/api`)

**Note**: Environment variables in Vercel can be set for:
- **Production**: Used for production deployments
- **Preview**: Used for pull request previews
- **Development**: Used for local development with `vercel dev`

For this deployment, set it for all three environments.

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

