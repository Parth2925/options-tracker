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
    <nav className="navbar">
      <div className="navbar-content">
        <div className="navbar-left">
          <Link to="/" className="navbar-brand" style={{ textDecoration: 'none', color: 'white' }} onClick={closeMobileMenu}>
            Options Tracker
          </Link>
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
        <div className={`navbar-links ${mobileMenuOpen ? 'mobile-open' : ''}`}>
          <Link to="/dashboard" onClick={closeMobileMenu}>Dashboard</Link>
          <Link to="/positions" onClick={closeMobileMenu}>Positions</Link>
          <Link to="/trades" onClick={closeMobileMenu}>Trades</Link>
          <Link to="/accounts" onClick={closeMobileMenu}>Accounts</Link>
        </div>
        <div className={`navbar-right ${mobileMenuOpen ? 'mobile-open' : ''}`}>
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
    </nav>
  );
}

export default Navbar;

