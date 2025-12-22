import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="navbar">
      <div className="navbar-content">
        <div>
          <Link to="/" className="navbar-brand" style={{ textDecoration: 'none', color: 'white' }}>Options Tracker</Link>
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/positions">Positions</Link>
          <Link to="/trades">Trades</Link>
          <Link to="/accounts">Accounts</Link>
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
  );
}

export default Navbar;

