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
      description: 'Track the complete wheel cycle: CSP → Assignment → Stock Position → Covered Calls. Auto-creates stock positions from assignments and exercises.'
    },
    {
      icon: '📈',
      title: 'LEAPS & Stock Positions',
      description: 'Track LEAPS with exercise support. Manage stock positions separately with automatic creation from CSP assignments and LEAPS exercises.'
    },
    {
      icon: '💰',
      title: 'Real-Time P&L Calculations',
      description: 'Accurate realized and unrealized P&L with time-based metrics (Days Held, Return %, Annualized Return %). Uses stock cost basis for covered calls.'
    },
    {
      icon: '🔄',
      title: 'Enhanced Close Workflow',
      description: 'Context-aware close options for all trade types. Single-entry system for full closes. Track partial closes with detailed history.'
    },
    {
      icon: '📅',
      title: 'Monthly Returns & YTD',
      description: 'Monthly returns breakdown with year-to-date summary. Track performance over time with detailed analytics.'
    },
    {
      icon: '🏦',
      title: 'Multiple Account Support',
      description: 'Manage multiple accounts with default fees, deposits, withdrawals, and aggregated views. Edit account names and balances.'
    },
    {
      icon: '📥',
      title: 'Easy Trade Entry & Export',
      description: 'Import/export CSV/Excel with backward compatibility. Automatic premium calculation. Edit closing details after trade closure.'
    },
    {
      icon: '📊',
      title: 'Portfolio Allocation',
      description: 'Visualize positions with pie charts and allocation percentages. See capital at risk with real-time spot prices and company logos.'
    },
    {
      icon: '📰',
      title: 'Market Data Integration',
      description: 'Real-time prices for positions and major indices (DJIA, S&P 500, NASDAQ, VIX) with color-coded daily performance.'
    },
    {
      icon: '✏️',
      title: 'Full Trade Management',
      description: 'Edit trades and closing details. Partial closes with history tracking. Sortable, searchable tables with pagination.'
    },
    {
      icon: '🔧',
      title: 'VIX Cash Allocation Calculator',
      description: 'Professional tool recommending cash allocation based on VIX levels. Calculate for individual accounts or combined balances.'
    },
    {
      icon: '🔍',
      title: 'Advanced Search & Filtering',
      description: 'Search and filter by symbol, status, trade type, and account. Visual indicators for closed positions.'
    },
    {
      icon: '🌓',
      title: 'Dark Mode & Mobile Friendly',
      description: 'Dark mode support with easy theme switching. Fully responsive design for desktop, tablet, and mobile.'
    },
    {
      icon: '📚',
      title: 'Interactive How-To Guide',
      description: 'Step-by-step guide for new users covering all features, use cases, and trading strategies.'
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
              Professional options trading tracker for the wheel strategy, LEAPS, stock positions, and covered calls.
              Track P&L, returns, portfolio allocation, and optimize cash with the VIX Calculator. All in one place, completely free.
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
                <p>Add trades manually or import from CSV/Excel. Track CSPs, Covered Calls, LEAPS with context-aware close options. Stock positions auto-create from assignments and exercises.</p>
              </div>
              <div className="step">
                <div className="step-number">3</div>
                <h3>Track Performance</h3>
                <p>View P&L, returns, monthly performance with YTD summary, and portfolio allocation on the dashboard. See market data with company logos and real-time prices.</p>
              </div>
              <div className="step">
                <div className="step-number">4</div>
                <h3>Manage Portfolio</h3>
                <p>Close positions with context-aware options, track partial closes with history, and manage stock positions. Use the VIX Calculator and export trades for backup.</p>
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

