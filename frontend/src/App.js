import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ToastProvider } from './contexts/ToastContext';
import './components/Toast/Toast.css';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import VerifyEmail from './components/Auth/VerifyEmail';
import Home from './components/Home/Home';
import Dashboard from './components/Dashboard/Dashboard';
import Trades from './components/Trades/Trades';
import EditTrade from './components/Trades/EditTrade';
import Positions from './components/Positions/Positions';
import Accounts from './components/Accounts/Accounts';
import Profile from './components/Profile/Profile';
import Navbar from './components/Layout/Navbar';

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

