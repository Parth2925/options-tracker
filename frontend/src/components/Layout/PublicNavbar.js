import React from 'react';
import { Link } from 'react-router-dom';

function PublicNavbar() {
  return (
    <nav className="navbar">
      <div className="navbar-content">
        <div>
          <Link to="/" className="navbar-brand" style={{ textDecoration: 'none', color: 'white' }}>Options Tracker</Link>
        </div>
        <div className="navbar-right">
          <Link to="/login" className="btn btn-secondary" style={{ marginRight: '10px' }}>
            Login
          </Link>
          <Link to="/register" className="btn btn-primary">
            Sign Up
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default PublicNavbar;


