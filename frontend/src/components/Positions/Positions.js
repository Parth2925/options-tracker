import React, { useState, useEffect } from 'react';
import Navbar from '../Layout/Navbar';
import Footer from '../Layout/Footer';
import api from '../../utils/api';
import OptionsPositions from './OptionsPositions';
import StockPositions from './StockPositions';
import './Positions.css';

function Positions() {
  const [activeTab, setActiveTab] = useState('options'); // 'options' or 'stocks'
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('all');

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const response = await api.get('/accounts');
      setAccounts(response.data);
    } catch (error) {
      console.error('Error loading accounts:', error);
    }
  };

  return (
    <div className="page-wrapper">
      <Navbar />
      <div className="container">
        <div className="page-header">
          <h1>Positions</h1>
        </div>

        {/* Tabs - More prominent styling */}
        <div className="positions-tabs">
          <button
            className={`tab-button ${activeTab === 'options' ? 'active' : ''}`}
            onClick={() => setActiveTab('options')}
          >
            Options
          </button>
          <button
            className={`tab-button ${activeTab === 'stocks' ? 'active' : ''}`}
            onClick={() => setActiveTab('stocks')}
          >
            Stocks
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'options' ? (
          <OptionsPositions
            accounts={accounts}
            selectedAccount={selectedAccount}
            onAccountChange={setSelectedAccount}
          />
        ) : (
          <StockPositions
            accounts={accounts}
            selectedAccount={selectedAccount}
            onAccountChange={setSelectedAccount}
          />
        )}
      </div>
      <Footer />
    </div>
  );
}

export default Positions;

