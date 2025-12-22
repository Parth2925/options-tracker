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
      description: 'Get accurate realized and unrealized P&L calculations. Track your rate of return based on invested capital with time-based metrics.'
    },
    {
      icon: '📅',
      title: 'Monthly Returns & YTD',
      description: 'View your monthly returns breakdown with year-to-date summary. Track performance over time with detailed analytics.'
    },
    {
      icon: '🏦',
      title: 'Multiple Account Support',
      description: 'Manage multiple trading accounts (IRA, Taxable, Margin, etc.) with separate tracking and aggregated views.'
    },
    {
      icon: '📥',
      title: 'Easy Trade Entry',
      description: 'Enter trades manually or import from CSV/Excel files. Automatic premium calculation from trade price and contract quantity.'
    },
    {
      icon: '📊',
      title: 'Portfolio Allocation',
      description: 'Visualize your open positions with pie charts showing portfolio allocation by symbol. See capital at risk for each position.'
    },
    {
      icon: '📰',
      title: 'Market Data Integration',
      description: 'View delayed market prices for your open positions and major indices (DJIA, S&P 500, NASDAQ, VIX) with CNBC-style displays.'
    },
    {
      icon: '✏️',
      title: 'Full Trade Management',
      description: 'Edit trades, perform partial closes, track assignments, and manage the complete lifecycle of your options positions.'
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
              Track your P&L, returns, and portfolio allocation all in one place.
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
                <h3>Create Your Account</h3>
                <p>Set up your trading accounts with initial balances and track deposits over time.</p>
              </div>
              <div className="step">
                <div className="step-number">2</div>
                <h3>Enter Your Trades</h3>
                <p>Add trades manually or import from CSV/Excel. The system automatically calculates premiums and tracks the full trade lifecycle.</p>
              </div>
              <div className="step">
                <div className="step-number">3</div>
                <h3>Track Performance</h3>
                <p>View your P&L, returns, monthly performance, and portfolio allocation on the comprehensive dashboard.</p>
              </div>
              <div className="step">
                <div className="step-number">4</div>
                <h3>Manage Positions</h3>
                <p>Close positions, track assignments, perform partial closes, and manage your complete options portfolio.</p>
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

