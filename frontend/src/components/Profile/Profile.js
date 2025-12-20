import React, { useState, useEffect } from 'react';
import Navbar from '../Layout/Navbar';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import api from '../../utils/api';
import './Profile.css';

function Profile() {
  const { user, updateProfile, changePassword, resendVerification, setUser } = useAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // Profile form state
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    email: '',
  });

  // Password form state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  useEffect(() => {
    // Refresh user data when component mounts to get latest verification status
    const refreshUserData = async () => {
      try {
        const response = await api.get('/auth/me');
        setUser(response.data);
      } catch (err) {
        console.error('Failed to refresh user data:', err);
      }
    };
    
    refreshUserData();
  }, []);

  useEffect(() => {
    if (user) {
      setProfileData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
      });
    }
  }, [user]);

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    const result = await updateProfile(profileData);
    
    if (result.success) {
      setMessage(result.message || 'Profile updated successfully');
      // Refresh user data
      try {
        const response = await api.get('/auth/me');
        setUser(response.data);
      } catch (err) {
        console.error('Failed to refresh user data:', err);
      }
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('New passwords do not match');
      return;
    }

    if (passwordData.new_password.length < 6) {
      setError('New password must be at least 6 characters');
      return;
    }

    setLoading(true);

    const result = await changePassword(
      passwordData.current_password,
      passwordData.new_password
    );
    
    if (result.success) {
      setMessage(result.message || 'Password changed successfully');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  const handleResendVerification = async () => {
    setError('');
    setMessage('');
    setLoading(true);

    const result = await resendVerification();
    
    if (result.success) {
      setMessage(result.message || 'Verification email sent successfully');
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  if (!user) {
    return (
      <>
        <Navbar />
        <div className="container">Loading...</div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="container">
      <h1>Profile</h1>
      
      <div className="profile-tabs">
        <button
          className={activeTab === 'profile' ? 'active' : ''}
          onClick={() => setActiveTab('profile')}
        >
          Profile Information
        </button>
        <button
          className={activeTab === 'password' ? 'active' : ''}
          onClick={() => setActiveTab('password')}
        >
          Change Password
        </button>
        <button
          className={activeTab === 'preferences' ? 'active' : ''}
          onClick={() => setActiveTab('preferences')}
        >
          Preferences
        </button>
      </div>

      {message && <div className="alert alert-success">{message}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {activeTab === 'profile' && (
        <div className="profile-card">
          <h2>Profile Information</h2>
          
          {!user.email_verified && (
            <div className="alert alert-warning">
              <strong>Email not verified.</strong> Please verify your email address to access all features.
              <button 
                className="btn btn-small btn-primary" 
                onClick={handleResendVerification}
                disabled={loading}
                style={{ marginLeft: '10px' }}
              >
                Resend Verification Email
              </button>
            </div>
          )}

          {user.email_verified && (
            <div className="alert alert-success" style={{ marginBottom: '20px' }}>
              ✓ Email verified
            </div>
          )}

          <form onSubmit={handleProfileSubmit}>
            <div className="form-group">
              <label>First Name</label>
              <input
                type="text"
                value={profileData.first_name}
                onChange={(e) => setProfileData({ ...profileData, first_name: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label>Last Name</label>
              <input
                type="text"
                value={profileData.last_name}
                onChange={(e) => setProfileData({ ...profileData, last_name: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={profileData.email}
                onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                required
              />
              {profileData.email !== user.email && (
                <small className="form-text">
                  Changing your email will require re-verification.
                </small>
              )}
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Updating...' : 'Update Profile'}
            </button>
          </form>
        </div>
      )}

      {activeTab === 'password' && (
        <div className="profile-card">
          <h2>Change Password</h2>
          
          <form onSubmit={handlePasswordSubmit}>
            <div className="form-group">
              <label>Current Password</label>
              <input
                type="password"
                value={passwordData.current_password}
                onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label>New Password</label>
              <input
                type="password"
                value={passwordData.new_password}
                onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                required
                minLength={6}
              />
              <small className="form-text">Must be at least 6 characters</small>
            </div>

            <div className="form-group">
              <label>Confirm New Password</label>
              <input
                type="password"
                value={passwordData.confirm_password}
                onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                required
                minLength={6}
              />
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Changing...' : 'Change Password'}
            </button>
          </form>
        </div>
      )}

      {activeTab === 'preferences' && (
        <div className="profile-card">
          <h2>Preferences</h2>
          
          <div className="form-group" style={{ marginTop: '20px' }}>
            <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
              <span>Dark Mode</span>
              <div style={{ position: 'relative', display: 'inline-block' }}>
                <input
                  type="checkbox"
                  checked={isDarkMode}
                  onChange={toggleTheme}
                  style={{
                    width: '50px',
                    height: '26px',
                    appearance: 'none',
                    backgroundColor: isDarkMode ? '#28a745' : '#ccc',
                    borderRadius: '13px',
                    position: 'relative',
                    cursor: 'pointer',
                    transition: 'background-color 0.3s',
                  }}
                />
                <span
                  style={{
                    position: 'absolute',
                    top: '2px',
                    left: isDarkMode ? '26px' : '2px',
                    width: '22px',
                    height: '22px',
                    backgroundColor: 'white',
                    borderRadius: '50%',
                    transition: 'left 0.3s',
                    pointerEvents: 'none',
                  }}
                />
              </div>
            </label>
            <small className="form-text" style={{ display: 'block', marginTop: '8px' }}>
              Toggle between light and dark mode. Your preference will be saved automatically.
            </small>
          </div>
        </div>
      )}
      </div>
    </>
  );
}

export default Profile;

