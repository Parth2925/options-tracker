import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import api from '../../utils/api';
import { useToast } from '../../contexts/ToastContext';
import PublicNavbar from '../Layout/PublicNavbar';
import './Auth.css';

function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const { showToast } = useToast();
  
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) {
      setError('Invalid reset link. Please request a new password reset.');
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validate passwords match
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    // Validate password length
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    if (!token) {
      setError('Invalid reset token');
      return;
    }

    setLoading(true);

    try {
      const response = await api.post('/auth/reset-password', {
        token,
        password,
        confirm_password: confirmPassword
      });
      
      showToast(response.data.message || 'Password reset successfully!', 'success');
      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to reset password';
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <>
        <PublicNavbar />
        <div className="auth-container">
        <div className="auth-card">
          <h2>Invalid Reset Link</h2>
          <div className="error" style={{ marginBottom: '20px' }}>
            This password reset link is invalid or has expired. Please request a new one.
          </div>
          <Link to="/forgot-password" className="btn btn-primary" style={{ textDecoration: 'none', display: 'inline-block', width: '100%', textAlign: 'center' }}>
            Request New Reset Link
          </Link>
        </div>
      </div>
      </>
    );
  }

  return (
    <>
      <PublicNavbar />
      <div className="auth-container">
      <div className="auth-card">
        <h2>Reset Password</h2>
        <p style={{ marginBottom: '20px', color: 'var(--text-secondary)' }}>
          Enter your new password below.
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>New Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter new password (min. 6 characters)"
              minLength={6}
            />
          </div>
          <div className="form-group">
            <label>Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              placeholder="Confirm new password"
              minLength={6}
            />
          </div>
          {error && <div className="error">{error}</div>}
          <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%' }}>
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>
        <p style={{ marginTop: '15px', textAlign: 'center' }}>
          <Link to="/login">Back to Login</Link>
        </p>
      </div>
    </div>
    </>
  );
}

export default ResetPassword;

