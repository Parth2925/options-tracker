import React, { useState, useEffect } from 'react';
import Navbar from '../Layout/Navbar';
import Footer from '../Layout/Footer';
import { getVersion } from '../../utils/version';
import { getReleaseNotes, getAllReleaseNotes } from '../../data/releaseNotes';
import api from '../../utils/api';
import './About.css';

function About() {
  const [appVersion, setAppVersion] = useState(getVersion());
  const [currentReleaseNotes, setCurrentReleaseNotes] = useState(null);
  const [allReleaseNotes, setAllReleaseNotes] = useState([]);

  useEffect(() => {
    // Try to get version from backend, fallback to frontend version
    api.get('/version')
      .then(response => {
        if (response.data && response.data.version) {
          setAppVersion(response.data.version);
        }
      })
      .catch(() => {
        // If backend is unavailable, use frontend version
        setAppVersion(getVersion());
      });
  }, []);

  useEffect(() => {
    // Load release notes for current version
    const notes = getReleaseNotes(appVersion);
    setCurrentReleaseNotes(notes);
    
    // Load all release notes
    const allNotes = getAllReleaseNotes();
    setAllReleaseNotes(allNotes);
  }, [appVersion]);

  return (
    <div className="page-wrapper">
      <Navbar />
      <div className="container">
        <h1>About Options Tracker</h1>
        
        <div className="about-content">
          <div className="about-section">
            <h2>Version Information</h2>
            <div className="version-info">
              <p><strong>Current Version:</strong> <span className="version-badge-large">v{appVersion}</span></p>
              {currentReleaseNotes && (
                <p><strong>Release Date:</strong> {new Date(currentReleaseNotes.date).toLocaleDateString('en-US', { 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}</p>
              )}
            </div>
          </div>

          {currentReleaseNotes && (
            <div className="about-section">
              <h2>What's New in v{appVersion}</h2>
              <div className="release-notes">
                {currentReleaseNotes.features && currentReleaseNotes.features.length > 0 && (
                  <div className="release-category">
                    <h3>✨ New Features</h3>
                    <ul>
                      {currentReleaseNotes.features.map((feature, index) => (
                        <li key={index}>{feature}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {currentReleaseNotes.improvements && currentReleaseNotes.improvements.length > 0 && (
                  <div className="release-category">
                    <h3>🔧 Improvements</h3>
                    <ul>
                      {currentReleaseNotes.improvements.map((improvement, index) => (
                        <li key={index}>{improvement}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {currentReleaseNotes.bugfixes && currentReleaseNotes.bugfixes.length > 0 && (
                  <div className="release-category">
                    <h3>🐛 Bug Fixes</h3>
                    <ul>
                      {currentReleaseNotes.bugfixes.map((fix, index) => (
                        <li key={index}>{fix}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {allReleaseNotes.length > 0 && (
            <div className="about-section">
              <h2>Release History</h2>
              <div className="release-history">
                {allReleaseNotes.map((release, index) => (
                  <div key={release.version} className="release-item">
                    <div className="release-header">
                      <h3>Version {release.version}</h3>
                      <span className="release-date">
                        {new Date(release.date).toLocaleDateString('en-US', { 
                          year: 'numeric', 
                          month: 'long', 
                          day: 'numeric' 
                        })}
                      </span>
                    </div>
                    
                    {release.features && release.features.length > 0 && (
                      <div className="release-details">
                        <strong>Features:</strong>
                        <ul>
                          {release.features.map((feature, idx) => (
                            <li key={idx}>{feature}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {release.improvements && release.improvements.length > 0 && (
                      <div className="release-details">
                        <strong>Improvements:</strong>
                        <ul>
                          {release.improvements.map((improvement, idx) => (
                            <li key={idx}>{improvement}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {release.bugfixes && release.bugfixes.length > 0 && (
                      <div className="release-details">
                        <strong>Bug Fixes:</strong>
                        <ul>
                          {release.bugfixes.map((fix, idx) => (
                            <li key={idx}>{fix}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="about-section">
            <h2>About Options Tracker</h2>
            <p>
              Options Tracker is a comprehensive tool for managing and analyzing your options trading portfolio. 
              Track your Cash-Secured Puts, Covered Calls, LEAPS, and assigned positions all in one place.
            </p>
            <p>
              Monitor your performance with detailed analytics, monthly returns, and position allocation. 
              Make informed decisions with market data integration and the VIX Cash Allocation Calculator.
            </p>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}

export default About;

