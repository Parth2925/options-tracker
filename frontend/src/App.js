import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ToastProvider } from './contexts/ToastContext';
import './components/Toast/Toast.css';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import VerifyEmail from './components/Auth/VerifyEmail';
import ForgotPassword from './components/Auth/ForgotPassword';
import ResetPassword from './components/Auth/ResetPassword';
import Home from './components/Home/Home';
import Dashboard from './components/Dashboard/Dashboard';
import Trades from './components/Trades/Trades';
import EditTrade from './components/Trades/EditTrade';
import Positions from './components/Positions/Positions';
import Accounts from './components/Accounts/Accounts';
import Tools from './components/Tools/Tools';
import Profile from './components/Profile/Profile';
import Navbar from './components/Layout/Navbar';
import LogoPreview from './components/LogoPreview/LogoPreview';
import api from './utils/api';

function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/logo-preview" element={<LogoPreview />} />
      <Route path="/" element={<Home />} />
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        }
      />
      <Route
        path="/trades"
        element={
          <PrivateRoute>
            <Trades />
          </PrivateRoute>
        }
      />
      <Route
        path="/trades/:id/edit"
        element={
          <PrivateRoute>
            <EditTrade />
          </PrivateRoute>
        }
      />
      <Route
        path="/positions"
        element={
          <PrivateRoute>
            <Positions />
          </PrivateRoute>
        }
      />
      <Route
        path="/accounts"
        element={
          <PrivateRoute>
            <Accounts />
          </PrivateRoute>
        }
      />
      <Route
        path="/tools"
        element={
          <PrivateRoute>
            <Tools />
          </PrivateRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <PrivateRoute>
            <Profile />
          </PrivateRoute>
        }
      />
    </Routes>
  );
}

function App() {
  // Keep-alive mechanism to prevent Render free tier spin-down
  useEffect(() => {
    // Only run keep-alive in production (when using Render)
    if (process.env.NODE_ENV === 'production') {
      const keepAliveInterval = setInterval(() => {
        // Ping the backend every 10 minutes to keep it awake (Render spins down after 15 min)
        api.get('/ping').catch(() => {
          // Silently fail - this is just a keep-alive, don't show errors
        });
      }, 10 * 60 * 1000); // 10 minutes

      // Also ping immediately when app loads
      api.get('/ping').catch(() => {});

      return () => clearInterval(keepAliveInterval);
    }
  }, []);

  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <Router>
            <div className="App">
              <AppRoutes />
            </div>
          </Router>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;

