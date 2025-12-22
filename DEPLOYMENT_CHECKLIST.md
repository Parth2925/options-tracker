# Deployment Checklist

## Pre-Deployment

- [ ] Review and update environment variables
- [ ] Test application locally
- [ ] Ensure all dependencies are in requirements.txt
- [ ] Commit all changes to git

## Step 1: GitHub Setup

- [ ] Create GitHub account (if not already)
- [ ] Create new repository on GitHub
- [ ] Push code to GitHub:
  ```bash
  git add .
  git commit -m "Initial commit"
  git remote add origin https://github.com/YOUR_USERNAME/options-tracker.git
  git push -u origin main
  ```

## Step 2: Render.com Backend

- [ ] Sign up for Render.com account
- [ ] Create PostgreSQL database:
  - Name: `options-tracker-db`
  - Plan: Free
  - Copy Internal Database URL
- [ ] Create Web Service:
  - Connect GitHub repository
  - Build Command: `pip install -r backend/requirements.txt`
  - Start Command: `cd backend && gunicorn app:app --bind 0.0.0.0:$PORT`
  - Add all environment variables (see DEPLOYMENT.md)
- [ ] Wait for deployment
- [ ] Initialize database in Render Shell
- [ ] Copy backend URL (e.g., `https://options-tracker-api.onrender.com`)

## Step 3: Vercel Frontend

- [ ] Go to vercel.com and sign up/log in (Continue with GitHub recommended)
- [ ] Click "New Project" or "Add New..." button in dashboard
- [ ] Connect GitHub (if first time) or select GitHub as Git provider
- [ ] Find and import `options-tracker` repository
- [ ] Configure project settings:
  - [ ] Project Name: `options-tracker` (or custom)
  - [ ] Framework Preset: Create React App (should auto-detect)
  - [ ] **Root Directory: `frontend`** ⚠️ CRITICAL - change from `./` to `frontend`
  - [ ] Build Command: `npm run build` (verify it's correct)
  - [ ] Output Directory: `build` (verify it's correct)
  - [ ] Install Command: `npm install` (usually default)
- [ ] Add environment variable in Environment Variables section:
  - [ ] Click "Add" or "Add Variable"
  - [ ] Key: `REACT_APP_API_URL`
  - [ ] Value: `https://your-backend-url.onrender.com/api` (your actual Render URL)
  - [ ] Select all three environments: Production ✅ Preview ✅ Development ✅
  - [ ] Save/Add the variable
- [ ] Review all settings one more time
- [ ] Click "Deploy" button
- [ ] Watch deployment progress (2-5 minutes)
- [ ] Verify deployment success (green checkmark)
- [ ] Click "Visit" or copy the deployment URL
- [ ] Test the live site (try opening it in browser)
- [ ] Check browser console for errors (F12 → Console)
- [ ] Copy and save frontend URL for Step 4

## Step 4: Final Configuration (CORS)

- [ ] Go to Render dashboard → Backend service → Environment tab
- [ ] Add environment variable:
  - [ ] Key: `FRONTEND_URL`
  - [ ] Value: Your Vercel frontend URL (from Step 3)
- [ ] Click "Save Changes"
- [ ] Wait for automatic backend redeployment
- [ ] Test the live application:
  - [ ] Visit Vercel frontend URL
  - [ ] Try registering a new account
  - [ ] Verify login works
  - [ ] Check browser console for errors

## Post-Deployment

- [ ] Test user registration
- [ ] Test login
- [ ] Test email verification
- [ ] Test trade creation
- [ ] Test dashboard
- [ ] Monitor error logs

## Environment Variables Reference

### Render (Backend)
```
PYTHON_VERSION=3.11.9
DATABASE_URL=<from PostgreSQL>
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
FINNHUB_API_KEY=d525qj1r01qu5pvmiv2gd525qj1r01qu5pvmiv30
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=options.tracker.email.verify@gmail.com
MAIL_PASSWORD=gmjefaokgsjdlebd
MAIL_DEFAULT_SENDER=options.tracker.email.verify@gmail.com
FRONTEND_URL=<your-vercel-url>
FLASK_ENV=production
```

### Vercel (Frontend)
```
REACT_APP_API_URL=https://options-tracker-api.onrender.com/api
```

