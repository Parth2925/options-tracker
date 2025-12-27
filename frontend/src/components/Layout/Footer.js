import React from 'react';
import { Link } from 'react-router-dom';
import './Footer.css';

function Footer() {
  return (
    <footer className="app-footer">
      <div className="footer-content">
        <div className="footer-links">
          <Link to="/about">About</Link>
          {/* Future links can be added here:
          <Link to="/guide">Guide</Link>
          <Link to="/contact">Contact</Link>
          <Link to="/feedback">Feedback</Link>
          */}
        </div>
      </div>
    </footer>
  );
}

export default Footer;

