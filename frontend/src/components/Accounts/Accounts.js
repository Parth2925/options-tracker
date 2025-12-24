import React, { useState, useEffect } from 'react';
import Navbar from '../Layout/Navbar';
import api from '../../utils/api';
import AccountForm from './AccountForm';
import DepositForm from './DepositForm';
import WithdrawalForm from './WithdrawalForm';
import { useToast } from '../../contexts/ToastContext';
import './Accounts.css';

function Accounts() {
  const { showToast } = useToast();
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [deposits, setDeposits] = useState([]);
  const [withdrawals, setWithdrawals] = useState([]);
  const [showAccountForm, setShowAccountForm] = useState(false);
  const [showDepositForm, setShowDepositForm] = useState(false);
  const [showWithdrawalForm, setShowWithdrawalForm] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      loadDeposits();
      loadWithdrawals();
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

  const loadWithdrawals = async () => {
    if (!selectedAccount) return;
    
    try {
      const response = await api.get(`/accounts/${selectedAccount}/withdrawals`);
      setWithdrawals(response.data);
    } catch (error) {
      console.error('Error loading withdrawals:', error);
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
    loadAccounts(); // Reload accounts to update total capital
    showToast('Deposit added successfully!', 'success');
  };

  const handleWithdrawalCreated = () => {
    setShowWithdrawalForm(false);
    loadWithdrawals();
    loadAccounts(); // Reload accounts to update total capital
    showToast('Withdrawal added successfully!', 'success');
  };

  const handleDeleteWithdrawal = async (withdrawalId) => {
    if (!window.confirm('Are you sure you want to delete this withdrawal?')) {
      return;
    }

    try {
      await api.delete(`/accounts/${selectedAccount}/withdrawals/${withdrawalId}`);
      loadWithdrawals();
      loadAccounts(); // Reload accounts to update total capital
      showToast('Withdrawal deleted successfully!', 'success');
    } catch (error) {
      console.error('Error deleting withdrawal:', error);
      showToast('Failed to delete withdrawal', 'error');
    }
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
        setWithdrawals([]);
      }
      loadAccounts();
    } catch (error) {
      showToast(error.response?.data?.error || 'Delete failed', 'error');
    }
  };

  const calculateTotalCapital = (account) => {
    // Use total_capital from backend if available (includes realized P&L)
    // Otherwise fall back to calculating from initial_balance + deposits
    if (account.total_capital !== undefined) {
      return account.total_capital;
    }
    
    // Fallback calculation (for backwards compatibility)
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
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
          <div className="accounts-layout">
            <div className="card accounts-list-card">
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
              <div className="card account-details-card">
                <h2 style={{ marginBottom: '20px' }}>Account Transactions</h2>
                
                <div className="transactions-container">
                  <div className="transaction-section">
                    <div className="transaction-header">
                      <h3>Deposits</h3>
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

                    {!showDepositForm && (
                      <>
                        {deposits.length === 0 ? (
                          <p className="empty-message">No deposits yet. Add your first deposit!</p>
                        ) : (
                          <div className="table-container">
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
                                    <td>{deposit.deposit_date ? (() => {
                                      const [year, month, day] = deposit.deposit_date.split('T')[0].split('-');
                                      return new Date(parseInt(year), parseInt(month) - 1, parseInt(day)).toLocaleDateString();
                                    })() : '-'}</td>
                                    <td className="amount-positive">${parseFloat(deposit.amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                                    <td>{deposit.notes || '-'}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </>
                    )}
                  </div>

                  <div className="transaction-section">
                    <div className="transaction-header">
                      <h3>Withdrawals</h3>
                      <button className="btn btn-primary" onClick={() => setShowWithdrawalForm(!showWithdrawalForm)}>
                        {showWithdrawalForm ? 'Cancel' : 'Add Withdrawal'}
                      </button>
                    </div>

                    {showWithdrawalForm && (
                      <WithdrawalForm
                        accountId={selectedAccount}
                        onSuccess={handleWithdrawalCreated}
                        onCancel={() => setShowWithdrawalForm(false)}
                      />
                    )}

                    {!showWithdrawalForm && (
                      <>
                        {withdrawals.length === 0 ? (
                          <p className="empty-message">No withdrawals yet. Add your first withdrawal!</p>
                        ) : (
                          <div className="table-container">
                            <table>
                              <thead>
                                <tr>
                                  <th>Date</th>
                                  <th>Amount</th>
                                  <th>Notes</th>
                                  <th>Actions</th>
                                </tr>
                              </thead>
                              <tbody>
                                {withdrawals.map((withdrawal) => (
                                  <tr key={withdrawal.id}>
                                    <td>{withdrawal.withdrawal_date ? (() => {
                                      const [year, month, day] = withdrawal.withdrawal_date.split('T')[0].split('-');
                                      return new Date(parseInt(year), parseInt(month) - 1, parseInt(day)).toLocaleDateString();
                                    })() : '-'}</td>
                                    <td className="amount-negative">${parseFloat(withdrawal.amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                                    <td>{withdrawal.notes || '-'}</td>
                                    <td>
                                      <button 
                                        className="btn btn-secondary" 
                                        onClick={() => handleDeleteWithdrawal(withdrawal.id)}
                                        style={{ fontSize: '0.875rem', padding: '0.25rem 0.5rem' }}
                                      >
                                        Delete
                                      </button>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}

export default Accounts;

