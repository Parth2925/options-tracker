import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
    setMobileMenuOpen(false);
  };

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  return (
    <>
      <nav className="navbar">
        <div className="navbar-content">
          <div className="navbar-left">
            <Link to="/" className="navbar-brand" style={{ textDecoration: 'none', color: 'white', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <img src="/logo.svg" alt="Options Tracker Logo" style={{ width: '32px', height: '32px' }} />
              <span>Options Tracker</span>
            </Link>
            <div className="navbar-links">
              <Link to="/dashboard">Dashboard</Link>
              <Link to="/positions">Positions</Link>
              <Link to="/trades">Trades</Link>
              <Link to="/accounts">Accounts</Link>
              <Link to="/tools">Tools</Link>
            </div>
            <button 
              className="mobile-menu-toggle" 
              onClick={toggleMobileMenu}
              aria-label="Toggle menu"
            >
              <span></span>
              <span></span>
              <span></span>
            </button>
          </div>
          <div className="navbar-right">
            <Link to="/profile" className="profile-link">
              {user?.first_name && user?.last_name 
                ? `${user.first_name} ${user.last_name}` 
                : user?.email}
            </Link>
            <button className="btn btn-secondary" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </div>
      </nav>
      
      {/* Mobile Menu Overlay */}
      <div 
        className={`mobile-menu-overlay ${mobileMenuOpen ? 'active' : ''}`}
        onClick={closeMobileMenu}
      ></div>
      
      {/* Mobile Sidebar Menu */}
      <div className={`mobile-menu-sidebar ${mobileMenuOpen ? 'active' : ''}`}>
        <div className="mobile-menu-header">
          <Link to="/" className="navbar-brand" style={{ textDecoration: 'none', color: 'white', display: 'flex', alignItems: 'center', gap: '10px' }} onClick={closeMobileMenu}>
            <img src="/logo.svg" alt="Options Tracker Logo" style={{ width: '28px', height: '28px' }} />
            <span>Options Tracker</span>
          </Link>
          <button className="mobile-close-btn" onClick={closeMobileMenu} aria-label="Close menu">
            ×
          </button>
        </div>
        <div className="mobile-menu-content">
          <div className="navbar-links">
            <Link to="/dashboard" onClick={closeMobileMenu}>Dashboard</Link>
            <Link to="/positions" onClick={closeMobileMenu}>Positions</Link>
            <Link to="/trades" onClick={closeMobileMenu}>Trades</Link>
            <Link to="/accounts" onClick={closeMobileMenu}>Accounts</Link>
            <Link to="/tools" onClick={closeMobileMenu}>Tools</Link>
          </div>
        </div>
        <div className="mobile-menu-footer">
          <Link to="/profile" className="profile-link" onClick={closeMobileMenu}>
            {user?.first_name && user?.last_name 
              ? `${user.first_name} ${user.last_name}` 
              : user?.email}
          </Link>
          <button className="btn btn-secondary" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>
    </>
  );
}

export default Navbar;

