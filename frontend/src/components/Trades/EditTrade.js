import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import Footer from '../Layout/Footer';
import api from '../../utils/api';
import TradeForm from './TradeForm';
import { useToast } from '../../contexts/ToastContext';

function EditTrade() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [trade, setTrade] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load accounts
      const accountsResponse = await api.get('/accounts');
      setAccounts(accountsResponse.data);

      // Load all trades (needed for parent trade selection)
      const tradesResponse = await api.get('/trades');
      setTrades(tradesResponse.data);

      // Load the specific trade to edit
      const tradeResponse = await api.get(`/trades/${id}`);
      setTrade(tradeResponse.data);
    } catch (err) {
      console.error('Error loading trade data:', err);
      setError('Failed to load trade data. Please try again.');
      showToast('Failed to load trade data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSuccess = () => {
    showToast('Trade updated successfully!', 'success');
    navigate('/trades');
  };

  const handleCancel = () => {
    navigate('/trades');
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="container">
          <div className="loading">Loading trade...</div>
        </div>
      </>
    );
  }

  if (error || !trade) {
    return (
      <div className="page-wrapper">
        <Navbar />
        <div className="container">
          <div className="card" style={{ color: 'var(--text-danger)', padding: '20px' }}>
            <h2>Error</h2>
            <p>{error || 'Trade not found'}</p>
            <button className="btn btn-primary" onClick={() => navigate('/trades')}>
              Back to Trades
            </button>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="page-wrapper">
      <Navbar />
      <div className="container">
        <div style={{ marginBottom: '20px' }}>
          <button 
            className="btn btn-secondary" 
            onClick={() => navigate('/trades')}
            style={{ marginBottom: '20px' }}
          >
            ← Back to Trades
          </button>
          <h1>Edit Trade</h1>
        </div>
        <TradeForm
          accounts={accounts}
          trade={trade}
          trades={trades}
          onSuccess={handleSuccess}
          onCancel={handleCancel}
        />
      </div>
      <Footer />
    </div>
  );
}

export default EditTrade;

