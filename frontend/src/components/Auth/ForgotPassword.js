import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../../utils/api';
import { useToast } from '../../contexts/ToastContext';
import PublicNavbar from '../Layout/PublicNavbar';
import './Auth.css';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setLoading(true);

    try {
      const response = await api.post('/auth/forgot-password', { email });
      setSuccess(true);
      showToast(response.data.message || 'Password reset email sent!', 'success');
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to send reset email';
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PublicNavbar />
      <div className="auth-container">
      <div className="auth-card">
        <h2>Forgot Password</h2>
        {success ? (
          <div>
            <div className="success" style={{ marginBottom: '20px', padding: '15px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px', color: 'var(--text-primary)' }}>
              <p>If an account with that email exists, a password reset link has been sent.</p>
              <p style={{ marginTop: '10px', fontSize: '14px', color: 'var(--text-secondary)' }}>
                Please check your email and click the link to reset your password.
              </p>
            </div>
            <Link to="/login" className="btn btn-primary" style={{ textDecoration: 'none', display: 'inline-block', width: '100%', textAlign: 'center' }}>
              Back to Login
            </Link>
          </div>
        ) : (
          <>
            <p style={{ marginBottom: '20px', color: 'var(--text-secondary)' }}>
              Enter your email address and we'll send you a link to reset your password.
            </p>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="Enter your email address"
                />
              </div>
              {error && <div className="error">{error}</div>}
              <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%' }}>
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>
            <p style={{ marginTop: '15px', textAlign: 'center' }}>
              Remember your password? <Link to="/login">Back to Login</Link>
            </p>
          </>
        )}
      </div>
    </div>
    </>
  );
}

export default ForgotPassword;

