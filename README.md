# Options Tracker

A comprehensive web application for tracking options trading strategies including Cash-Secured Puts (CSP), Covered Calls, LEAPS, and the Wheel Strategy.

## Features

- **Trade Management**: Track CSP, Covered Calls, LEAPS, Assignments, and Rollovers
- **Dashboard**: View performance metrics, monthly returns, and open positions allocation
- **Position Tracking**: Monitor open and closed positions with detailed analytics
- **Account Management**: Multiple account support with deposits tracking
- **Market Data**: Real-time (delayed) market prices for major indices (DJIA, S&P 500, NASDAQ, VIX)
- **User Profile**: Profile management, password changes, and email verification
- **Dark Mode**: Toggle between light and dark themes
- **Data Import/Export**: Import trades from CSV/Excel files with templates

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: React
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT
- **Email**: Flask-Mail for verification

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 16+
- npm or yarn

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/options-tracker.git
   cd options-tracker
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Copy environment variables
   cp ../.env.example .env
   # Edit .env with your configuration
   
   # Initialize database
   python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
   
   # Run backend
   python app.py
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   
   # Copy environment variables
   cp .env.example .env
   # Edit .env with your API URL (default: http://localhost:5001/api)
   
   # Run frontend
   npm start
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5001/api

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to:
- **Backend**: Render.com (free tier)
- **Frontend**: Vercel (free tier)
- **Database**: PostgreSQL on Render (free tier)

## Project Structure

```
options-tracker/
├── backend/
│   ├── app.py              # Flask application
│   ├── models.py           # Database models
│   ├── routes/            # API routes
│   │   ├── auth.py        # Authentication
│   │   ├── accounts.py    # Account management
│   │   ├── trades.py      # Trade management
│   │   └── dashboard.py   # Dashboard data
│   ├── utils/             # Utility functions
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── contexts/      # React contexts (Auth, Theme, Toast)
│   │   └── utils/         # Utility functions
│   └── package.json       # Node dependencies
└── DEPLOYMENT.md          # Deployment guide
```

## Environment Variables

### Backend (.env)
- `DATABASE_URL`: Database connection string
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `FINNHUB_API_KEY`: API key for market data
- `MAIL_*`: Email configuration for verification
- `FRONTEND_URL`: Frontend URL for CORS

### Frontend (.env)
- `REACT_APP_API_URL`: Backend API URL

See `.env.example` files for reference.

## API Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user
- `GET /api/accounts` - Get user accounts
- `POST /api/accounts` - Create account
- `GET /api/trades` - Get trades
- `POST /api/trades` - Create trade
- `GET /api/dashboard/summary` - Get dashboard summary
- `GET /api/dashboard/monthly-returns` - Get monthly returns

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.
