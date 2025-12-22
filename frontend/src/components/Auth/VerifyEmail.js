import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../utils/api';
import PublicNavbar from '../Layout/PublicNavbar';
import './Auth.css';

function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setUser, isAuthenticated } = useAuth();
  const [status, setStatus] = useState('verifying');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setStatus('error');
      setMessage('No verification token provided');
      return;
    }

    // Verify email via backend
    api.get(`/auth/verify-email?token=${token}`)
      .then(async (response) => {
        setStatus('success');
        setMessage(response.data.message || 'Email verified successfully');
        
        // If user is already logged in, refresh their user data
        if (isAuthenticated) {
          try {
            const userResponse = await api.get('/auth/me');
            setUser(userResponse.data);
            // Update localStorage as well
            localStorage.setItem('user', JSON.stringify(userResponse.data));
            // Redirect to profile after 2 seconds
            setTimeout(() => {
              navigate('/profile');
            }, 2000);
          } catch (err) {
            console.error('Failed to refresh user data:', err);
            // Still redirect to login if refresh fails
            setTimeout(() => {
              navigate('/login');
            }, 3000);
          }
        } else {
          // Redirect to login after 3 seconds if not logged in
          setTimeout(() => {
            navigate('/login');
          }, 3000);
        }
      })
      .catch((error) => {
        setStatus('error');
        setMessage(error.response?.data?.error || 'Verification failed');
      });
  }, [searchParams, navigate, setUser, isAuthenticated]);

  return (
    <>
      <PublicNavbar />
      <div className="auth-container">
      <div className="auth-card">
        <h2>Email Verification</h2>
        {status === 'verifying' && (
          <div>
            <p>Verifying your email address...</p>
          </div>
        )}
        {status === 'success' && (
          <div>
            <div className="alert alert-success">{message}</div>
            <p>Redirecting to login page...</p>
          </div>
        )}
        {status === 'error' && (
          <div>
            <div className="alert alert-error">{message}</div>
            <button className="btn btn-primary" onClick={() => navigate('/login')}>
              Go to Login
            </button>
          </div>
        )}
      </div>
    </div>
    </>
  );
}

export default VerifyEmail;


