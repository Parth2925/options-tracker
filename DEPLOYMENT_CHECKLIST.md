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

- [ ] Sign up for Vercel account
- [ ] Import GitHub repository
- [ ] Configure:
  - Root Directory: `frontend`
  - Build Command: `npm run build`
  - Output Directory: `build`
- [ ] Add environment variable:
  - `REACT_APP_API_URL`: Your Render backend URL + `/api`
- [ ] Deploy
- [ ] Copy frontend URL

## Step 4: Final Configuration

- [ ] Update Render backend environment variable:
  - `FRONTEND_URL`: Your Vercel frontend URL
- [ ] Redeploy backend (automatic on git push)
- [ ] Test the live application

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

