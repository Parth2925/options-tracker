import React from 'react';
import './LogoPreview.css';

function LogoPreview() {
  const logos = [
    { id: 1, name: 'Chart with Upward Trend', file: 'logo-option1.svg', desc: 'Upward trending line representing growth and trading success' },
    { id: 2, name: 'Options Chain (C/P)', file: 'logo-option2.svg', desc: 'Call/Put letters representing options trading' },
    { id: 3, name: 'Circular Target/Chart', file: 'logo-option3.svg', desc: 'Circular target with center point, representing precision' },
    { id: 4, name: 'Stylized "O" for Options', file: 'logo-option4.svg', desc: 'O shape with clock-like indicator' },
    { id: 5, name: 'Bar Chart', file: 'logo-option5.svg', desc: 'Ascending bars representing growth' },
  ];

  return (
    <div className="logo-preview-container">
      <h1>Logo Options for Options Tracker</h1>
      <p>Select your preferred logo option:</p>
      
      <div className="logos-grid">
        {logos.map((logo) => (
          <div key={logo.id} className="logo-option-card">
            <h3>Option {logo.id}: {logo.name}</h3>
            <div className="logo-display">
              <img 
                src={`/${logo.file}`} 
                alt={logo.name}
                className="logo-large"
              />
            </div>
            <p className="logo-desc">{logo.desc}</p>
            <div className="navbar-preview">
              <img 
                src={`/${logo.file}`} 
                alt={logo.name}
                className="logo-small"
              />
              <span>Options Tracker</span>
            </div>
          </div>
        ))}
      </div>

      <div className="instructions">
        <h2>How to Choose:</h2>
        <p>Note the logo number (1-5) that you prefer and let me know. I'll integrate it into:</p>
        <ul>
          <li>Browser favicon (tab icon)</li>
          <li>Navbar logo next to "Options Tracker"</li>
          <li>Multiple sizes for different devices</li>
        </ul>
      </div>
    </div>
  );
}

export default LogoPreview;

