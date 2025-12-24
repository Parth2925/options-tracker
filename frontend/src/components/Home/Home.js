import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import PublicNavbar from '../Layout/PublicNavbar';
import Navbar from '../Layout/Navbar';
import './Home.css';

function Home() {
  const { isAuthenticated, loading } = useAuth();

  const features = [
    {
      icon: '📊',
      title: 'Options Wheel Strategy Tracking',
      description: 'Track the complete wheel cycle: Cash-Secured Puts → Assignment → Covered Calls. Automatically calculates P&L for each stage of the strategy.'
    },
    {
      icon: '📈',
      title: 'LEAPS Trading',
      description: 'Track long-term equity anticipation securities with accurate P&L calculations for both opening and closing positions.'
    },
    {
      icon: '💰',
      title: 'Real-Time P&L Calculations',
      description: 'Get accurate realized and unrealized P&L calculations. Includes realized P&L in total capital calculations. Track your rate of return based on invested capital with time-based metrics (Days Held, Simple Return %, Annualized Return %).'
    },
    {
      icon: '📅',
      title: 'Monthly Returns & YTD',
      description: 'View your monthly returns breakdown by amount and percentage with year-to-date summary. Track performance over time with detailed analytics.'
    },
    {
      icon: '🏦',
      title: 'Multiple Account Support',
      description: 'Manage multiple trading accounts (IRA, Taxable, Margin, etc.) with separate tracking and aggregated views. Track deposits and withdrawals for complete capital management.'
    },
    {
      icon: '📥',
      title: 'Easy Trade Entry & Export',
      description: 'Enter trades manually or import from CSV/Excel files with comprehensive templates. Export all your trades to CSV/Excel for backup or re-import. Automatic premium calculation from trade price and contract quantity.'
    },
    {
      icon: '📊',
      title: 'Portfolio Allocation',
      description: 'Visualize your open positions with pie charts showing portfolio allocation by symbol and percentage. See capital at risk for each position with real-time spot prices.'
    },
    {
      icon: '📰',
      title: 'Market Data Integration',
      description: 'View delayed market prices for your open positions and major indices (DJIA, S&P 500, NASDAQ, VIX) with CNBC-style color-coded displays showing daily performance.'
    },
    {
      icon: '✏️',
      title: 'Full Trade Management',
      description: 'Edit trades, perform partial closes, track assignments, and manage the complete lifecycle of your options positions. Sortable and searchable tables for easy navigation.'
    },
    {
      icon: '🔧',
      title: 'VIX Cash Allocation Calculator',
      description: 'Professional trading tool that recommends cash allocation based on current VIX levels. Calculate allocations for individual accounts, all accounts combined, or custom balances.'
    },
    {
      icon: '💳',
      title: 'Complete Capital Tracking',
      description: 'Track deposits and withdrawals for each account. Total capital includes initial balance, deposits, withdrawals, and realized P&L from closed trades. Accurate capital management for better position sizing.'
    },
    {
      icon: '🔍',
      title: 'Advanced Search & Filtering',
      description: 'Search and filter trades by symbol, status, trade type, and account. Sortable columns for easy data analysis. Visual indicators for closed positions.'
    },
    {
      icon: '🌓',
      title: 'Dark Mode & Mobile Friendly',
      description: 'Complete dark mode support with easy theme switching. Fully responsive design that works seamlessly on desktop, tablet, and mobile devices.'
    },
    {
      icon: '🔐',
      title: 'Secure Account Management',
      description: 'Email verification, password reset functionality, and secure authentication. User profile management with the ability to update personal information and preferences.'
    }
  ];

  // Show loading while checking auth status
  if (loading) {
    return (
      <>
        {isAuthenticated ? <Navbar /> : <PublicNavbar />}
        <div style={{ textAlign: 'center', padding: '40px' }}>Loading...</div>
      </>
    );
  }

  return (
    <>
      {isAuthenticated ? <Navbar /> : <PublicNavbar />}
      <div className="home-container">
        {/* Hero Section */}
        <section className="hero-section">
          <div className="hero-content">
            <h1 className="hero-title">Options Trading Tracker</h1>
            <p className="hero-subtitle">
              Professional options trading tracking for the wheel strategy, LEAPS, and more.
              Track your P&L, returns, portfolio allocation, and optimize your cash position with the VIX Calculator.
              All in one place, completely free.
            </p>
            <div className="hero-buttons">
              {isAuthenticated ? (
                <Link to="/dashboard" className="btn btn-primary btn-large">
                  Go to Dashboard
                </Link>
              ) : (
                <>
                  <Link to="/register" className="btn btn-primary btn-large">
                    Get Started Free
                  </Link>
                  <Link to="/login" className="btn btn-secondary btn-large">
                    Login
                  </Link>
                </>
              )}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="features-section">
          <div className="container">
            <h2 className="section-title">Key Features</h2>
            <div className="features-grid">
              {features.map((feature, index) => (
                <div key={index} className="feature-card">
                  <div className="feature-icon">{feature.icon}</div>
                  <h3 className="feature-title">{feature.title}</h3>
                  <p className="feature-description">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section className="how-it-works-section">
          <div className="container">
            <h2 className="section-title">How It Works</h2>
            <div className="steps-container">
              <div className="step">
                <div className="step-number">1</div>
                <h3>Sign Up & Create Accounts</h3>
                <p>Create your free account and set up your trading accounts (IRA, Taxable, Margin, etc.) with initial balances. Track deposits and withdrawals for accurate capital management.</p>
              </div>
              <div className="step">
                <div className="step-number">2</div>
                <h3>Enter Your Trades</h3>
                <p>Add trades manually or import from CSV/Excel using our comprehensive templates. Track CSPs, Covered Calls, LEAPS, and Assignments. The system automatically calculates premiums and tracks the full trade lifecycle.</p>
              </div>
              <div className="step">
                <div className="step-number">3</div>
                <h3>Track Performance</h3>
                <p>View your P&L, returns, monthly performance with YTD summary, and portfolio allocation on the comprehensive dashboard. See market data integration with real-time prices for indices and your positions.</p>
              </div>
              <div className="step">
                <div className="step-number">4</div>
                <h3>Use Tools & Manage Portfolio</h3>
                <p>Use the VIX Cash Allocation Calculator to optimize your cash position. Export trades for backup. Close positions, track assignments, perform partial closes, and manage your complete options portfolio with advanced search and filtering.</p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="cta-section">
          <div className="container">
            <h2>Ready to Start Tracking Your Options Trades?</h2>
            <p>Get started today and take control of your options trading performance.</p>
            <div className="hero-buttons" style={{ justifyContent: 'center', marginTop: '20px' }}>
              {isAuthenticated ? (
                <Link to="/dashboard" className="btn btn-primary btn-large">
                  Go to Dashboard
                </Link>
              ) : (
                <>
                  <Link to="/register" className="btn btn-primary btn-large">
                    Sign Up Free
                  </Link>
                  <Link to="/login" className="btn btn-secondary btn-large">
                    Login
                  </Link>
                </>
              )}
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

export default Home;

