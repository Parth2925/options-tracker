import React, { useState, useEffect } from 'react';
import Navbar from '../Layout/Navbar';
import api from '../../utils/api';
import AccountForm from './AccountForm';
import DepositForm from './DepositForm';
import { useToast } from '../../contexts/ToastContext';
import './Accounts.css';

function Accounts() {
  const { showToast } = useToast();
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [deposits, setDeposits] = useState([]);
  const [showAccountForm, setShowAccountForm] = useState(false);
  const [showDepositForm, setShowDepositForm] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      loadDeposits();
    }
  }, [selectedAccount]);

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const response = await api.get('/accounts');
      setAccounts(response.data);
    } catch (error) {
      console.error('Error loading accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDeposits = async () => {
    if (!selectedAccount) return;
    
    try {
      const response = await api.get(`/accounts/${selectedAccount}/deposits`);
      setDeposits(response.data);
    } catch (error) {
      console.error('Error loading deposits:', error);
    }
  };

  const handleAccountCreated = () => {
    setShowAccountForm(false);
    loadAccounts();
    showToast('Account created successfully!', 'success');
  };

  const handleDepositCreated = () => {
    setShowDepositForm(false);
    loadDeposits();
    showToast('Deposit added successfully!', 'success');
  };

  const handleDeleteAccount = async (accountId) => {
    if (!window.confirm('Are you sure you want to delete this account? All associated trades and deposits will be deleted.')) {
      return;
    }

    try {
      await api.delete(`/accounts/${accountId}`);
      showToast('Account deleted successfully!', 'success');
      if (selectedAccount === accountId) {
        setSelectedAccount(null);
        setDeposits([]);
      }
      loadAccounts();
    } catch (error) {
      showToast(error.response?.data?.error || 'Delete failed', 'error');
    }
  };

  const calculateTotalCapital = (account) => {
    let total = parseFloat(account.initial_balance) || 0;
    const accountDeposits = deposits.filter(d => d.account_id === account.id);
    accountDeposits.forEach(deposit => {
      total += parseFloat(deposit.amount) || 0;
    });
    return total;
  };

  return (
    <>
      <Navbar />
      <div className="container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h1>Accounts</h1>
          <button className="btn btn-primary" onClick={() => setShowAccountForm(!showAccountForm)}>
            {showAccountForm ? 'Cancel' : 'Add Account'}
          </button>
        </div>


        {showAccountForm && (
          <AccountForm
            onSuccess={handleAccountCreated}
            onCancel={() => setShowAccountForm(false)}
          />
        )}

        {loading ? (
          <div className="loading">Loading accounts...</div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div className="card">
              <h2>Your Accounts</h2>
              {accounts.length === 0 ? (
                <p>No accounts yet. Create your first account!</p>
              ) : (
                <div className="accounts-list">
                  {accounts.map((account) => {
                    const totalCapital = calculateTotalCapital(account);
                    return (
                      <div
                        key={account.id}
                        className={`account-item ${selectedAccount === account.id ? 'selected' : ''}`}
                        onClick={() => setSelectedAccount(account.id)}
                      >
                        <div>
                          <h3>{account.name}</h3>
                          <p>{account.account_type || 'Standard Account'}</p>
                          <p>Initial Balance: ${(account.initial_balance || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                          <p>Total Capital: ${totalCapital.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                        </div>
                        <button
                          className="btn btn-danger"
                          style={{ padding: '5px 10px', fontSize: '12px' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteAccount(account.id);
                          }}
                        >
                          Delete
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {selectedAccount && (
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                  <h2>Deposits</h2>
                  <button className="btn btn-primary" onClick={() => setShowDepositForm(!showDepositForm)}>
                    {showDepositForm ? 'Cancel' : 'Add Deposit'}
                  </button>
                </div>

                {showDepositForm && (
                  <DepositForm
                    accountId={selectedAccount}
                    onSuccess={handleDepositCreated}
                    onCancel={() => setShowDepositForm(false)}
                  />
                )}

                {deposits.length === 0 ? (
                  <p>No deposits yet. Add your first deposit!</p>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Amount</th>
                        <th>Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {deposits.map((deposit) => (
                        <tr key={deposit.id}>
                          <td>{new Date(deposit.deposit_date).toLocaleDateString()}</td>
                          <td>${parseFloat(deposit.amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                          <td>{deposit.notes || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}

export default Accounts;

