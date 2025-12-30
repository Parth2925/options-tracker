import React, { useState, useEffect } from 'react';
import Navbar from '../Layout/Navbar';
import Footer from '../Layout/Footer';
import api from '../../utils/api';
import AccountFormDialog from './AccountFormDialog';
import DepositFormDialog from './DepositFormDialog';
import WithdrawalFormDialog from './WithdrawalFormDialog';
import { useToast } from '../../contexts/ToastContext';
import './Accounts.css';

function Accounts() {
  const { showToast } = useToast();
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [deposits, setDeposits] = useState([]);
  const [withdrawals, setWithdrawals] = useState([]);
  const [showAccountForm, setShowAccountForm] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
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
    const wasEditing = !!editingAccount;
    setShowAccountForm(false);
    setEditingAccount(null);
    loadAccounts();
    showToast(wasEditing ? 'Account updated successfully!' : 'Account created successfully!', 'success');
  };

  const handleEditAccount = (account, e) => {
    e.stopPropagation(); // Prevent account selection when clicking edit
    setEditingAccount(account);
    setShowAccountForm(true);
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
    <div className="page-wrapper">
      <Navbar />
      <div className="container">
        <div className="page-header">
          <h1>Accounts</h1>
          <div className="page-header-actions">
            <button className="btn btn-primary" onClick={() => {
              setEditingAccount(null);
              setShowAccountForm(true);
            }}>
              Add Account
            </button>
          </div>
        </div>

        {showAccountForm && (
          <AccountFormDialog
            account={editingAccount}
            onSuccess={handleAccountCreated}
            onCancel={() => {
              setShowAccountForm(false);
              setEditingAccount(null);
            }}
          />
        )}

        {loading ? (
          <div className="loading">Loading accounts...</div>
        ) : (
          <div className="accounts-layout">
            <div className="card accounts-list-card">
              <h2>Your Accounts</h2>
              {accounts.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">📊</div>
                  <div className="empty-state-message">No accounts yet</div>
                  <div className="empty-state-hint">Create your first account to get started!</div>
                </div>
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
                        <div className="action-buttons">
                          <button
                            className="action-button action-button-edit"
                            onClick={(e) => handleEditAccount(account, e)}
                            title="Edit account"
                          >
                            <span className="action-button-icon">✏️</span>
                            <span>Edit</span>
                          </button>
                          <button
                            className="action-button action-button-delete"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteAccount(account.id);
                            }}
                            title="Delete account"
                          >
                            <span className="action-button-icon">🗑️</span>
                            <span>Delete</span>
                          </button>
                        </div>
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
                      <button className="btn btn-primary" onClick={() => setShowDepositForm(true)}>
                        Add Deposit
                      </button>
                    </div>

                    {showDepositForm && (
                      <DepositFormDialog
                        accountId={selectedAccount}
                        onSuccess={handleDepositCreated}
                        onCancel={() => setShowDepositForm(false)}
                      />
                    )}

                    {!showDepositForm && (
                      <>
                        {deposits.length === 0 ? (
                          <div className="empty-state">
                            <div className="empty-state-icon">💰</div>
                            <div className="empty-state-message">No deposits yet</div>
                            <div className="empty-state-hint">Add your first deposit to track your account balance</div>
                          </div>
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
                      <button className="btn btn-primary" onClick={() => setShowWithdrawalForm(true)}>
                        Add Withdrawal
                      </button>
                    </div>

                    {showWithdrawalForm && (
                      <WithdrawalFormDialog
                        accountId={selectedAccount}
                        onSuccess={handleWithdrawalCreated}
                        onCancel={() => setShowWithdrawalForm(false)}
                      />
                    )}

                    {!showWithdrawalForm && (
                      <>
                        {withdrawals.length === 0 ? (
                          <div className="empty-state">
                            <div className="empty-state-icon">💸</div>
                            <div className="empty-state-message">No withdrawals yet</div>
                            <div className="empty-state-hint">Track your withdrawals to maintain accurate account balance</div>
                          </div>
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
      <Footer />
    </div>
  );
}

export default Accounts;

