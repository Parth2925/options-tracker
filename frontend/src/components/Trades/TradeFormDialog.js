import React, { useState, useEffect } from 'react';
import api from '../../utils/api';
import { useToast } from '../../contexts/ToastContext';
import './Trades.css';

function TradeFormDialog({ trade, accounts, stockPositions, onSuccess, onCancel }) {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [dragStartPos, setDragStartPos] = useState(null);
  const [dragStartTarget, setDragStartTarget] = useState(null);
  
  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  // Handle mouse down to track drag operations
  const handleMouseDown = (e) => {
    // Only track if clicking on the overlay itself (not modal content)
    if (e.target.classList.contains('modal-overlay')) {
      setDragStartPos({ x: e.clientX, y: e.clientY });
      setDragStartTarget(e.target);
    }
  };

  // Handle mouse up - only close if it wasn't a drag operation
  const handleMouseUp = (e) => {
    if (dragStartTarget && e.target === dragStartTarget) {
      // Check if mouse moved significantly (more than 5px) - indicates a drag
      const moved = dragStartPos && (
        Math.abs(e.clientX - dragStartPos.x) > 5 || 
        Math.abs(e.clientY - dragStartPos.y) > 5
      );
      
      // Only close if it wasn't a drag operation
      if (!moved) {
        onCancel();
      }
    }
    setDragStartPos(null);
    setDragStartTarget(null);
  };
  
  // Helper function to get today's date in local timezone
  const getTodayLocalDate = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const [formData, setFormData] = useState({
    account_id: accounts && accounts.length === 1 ? accounts[0].id : '', // Only auto-select if there's exactly one account
    symbol: '',
    trade_type: 'CSP',
    strike_price: '',
    expiration_date: '',
    contract_quantity: 1,
    trade_price: '',
    trade_action: 'Sold to Open',
    fees: '',
    trade_date: getTodayLocalDate(),
    stock_position_id: '',
    notes: '',
        // Close details (for editing closed trades)
        close_date: '',
        close_price: '',
        close_fees: '',
        close_premium: '',
        close_method: '',
        assignment_price: '',
  });

  // Initialize form data if editing
  useEffect(() => {
    if (trade) {
      setFormData({
        account_id: trade.account_id || (accounts && accounts.length === 1 ? accounts[0].id : ''), // Only auto-select if there's exactly one account
        symbol: trade.symbol || '',
        trade_type: trade.trade_type || 'CSP',
        strike_price: trade.strike_price || '',
        expiration_date: trade.expiration_date ? trade.expiration_date.split('T')[0] : '',
        contract_quantity: trade.contract_quantity || 1,
        trade_price: trade.trade_price || '',
        trade_action: trade.trade_action || 'Sold to Open',
        fees: trade.fees || '',
        trade_date: trade.trade_date ? trade.trade_date.split('T')[0] : getTodayLocalDate(),
        stock_position_id: trade.stock_position_id || '',
        notes: trade.notes || '',
        // Close details (for editing closed trades)
        close_date: trade.close_date ? trade.close_date.split('T')[0] : '',
        close_price: trade.close_price || '',
        close_fees: trade.close_fees || '',
        close_premium: trade.close_premium || '',
        close_method: trade.close_method || '',
        assignment_price: trade.assignment_price || '',
      });
    } else {
      // For new trades, auto-populate fees from account if available
      if (accounts && accounts.length === 1 && accounts[0].default_fee) {
        setFormData(prev => ({
          ...prev,
          fees: accounts[0].default_fee.toString()
        }));
      }
    }
  }, [trade, accounts]);

  // Filter stock positions based on selected account and symbol
  const getAvailableStockPositions = () => {
    if (!stockPositions || !formData.account_id) return [];
    
    return stockPositions.filter(sp => {
      if (sp.account_id !== parseInt(formData.account_id)) return false;
      if (sp.status !== 'Open') return false;
      if (formData.symbol && sp.symbol.toUpperCase() !== formData.symbol.toUpperCase()) return false;
      return true;
    });
  };

  const availableStockPositions = getAvailableStockPositions();

  // Helper function to calculate close premium (matches backend logic)
  const calculateClosePremium = (closePrice, closeMethod, contractQuantity, closeFees) => {
    if (!closePrice || !closeMethod || !contractQuantity) {
      return null;
    }

    // For expired/assigned/exercise, premium is 0
    if (closeMethod === 'expired' || closeMethod === 'assigned' || closeMethod === 'exercise') {
      return 0;
    }

    const price = parseFloat(closePrice) || 0;
    const qty = parseInt(contractQuantity) || 1;
    const fees = parseFloat(closeFees) || 0;

    // Base premium: price per contract * quantity * 100 (options contract size)
    const basePremium = price * qty * 100;
    
    // Total fees: fee per contract * quantity
    const totalFees = fees * qty;
    
    // Calculate premium based on close method
    let premium = 0;
    if (closeMethod === 'buy_to_close') {
      // Paying premium, add fees (make negative)
      premium = -(basePremium + totalFees);
    } else if (closeMethod === 'sell_to_close') {
      // Receiving premium, subtract fees
      premium = basePremium - totalFees;
    }
    
    // Round to 2 decimal places
    return Math.round(premium * 100) / 100;
  };

  // Auto-calculate close_premium when close_price, close_fees, close_method, or contract_quantity change
  useEffect(() => {
    // Only calculate if editing a closed trade
    if (trade && (trade.status === 'Closed' || trade.status === 'Expired' || trade.status === 'Assigned')) {
      if (formData.close_method && formData.close_price && formData.contract_quantity) {
        const calculatedPremium = calculateClosePremium(
          formData.close_price,
          formData.close_method,
          formData.contract_quantity,
          formData.close_fees || 0
        );
        
        // Update close_premium in real-time (only if calculated value is different)
        if (calculatedPremium !== null) {
          const calculatedPremiumStr = String(calculatedPremium);
          setFormData(prev => {
            // Only update if the calculated value is different from current
            // This prevents infinite loops while allowing real-time updates
            if (prev.close_premium !== calculatedPremiumStr) {
              return { ...prev, close_premium: calculatedPremiumStr };
            }
            return prev;
          });
        }
      } else if (!formData.close_price && formData.close_premium) {
        // Clear close_premium if close_price is cleared
        setFormData(prev => ({ ...prev, close_premium: '' }));
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.close_price, formData.close_fees, formData.close_method, formData.contract_quantity]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // Auto-uppercase symbol input
    const processedValue = name === 'symbol' ? value.toUpperCase() : value;
    
    setFormData(prev => ({
      ...prev,
      [name]: processedValue
    }));
    
    // Clear field error when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }

    // Handle account_id change: update default fee and clear stock_position_id if needed
    if (name === 'account_id' && value) {
      const newAccountId = parseInt(value);
      const selectedAccount = accounts.find(acc => acc.id === newAccountId);
      
      // Always update fee to new account's default fee if it exists
      if (selectedAccount && selectedAccount.default_fee) {
        setFormData(prev => ({
          ...prev,
          fees: selectedAccount.default_fee.toString()
        }));
      }
      
      // Clear stock_position_id if it doesn't belong to new account
      if (formData.stock_position_id) {
        const currentPosition = availableStockPositions.find(
          sp => sp.id === parseInt(formData.stock_position_id)
        );
        if (!currentPosition || currentPosition.account_id !== newAccountId) {
          // Clear stock_position_id if it doesn't belong to the new account
          setFormData(prev => ({
            ...prev,
            stock_position_id: ''
          }));
        }
      }
    }

    // Handle trade_type change: clear stock_position_id if changing away from Covered Call
    if (name === 'trade_type') {
      if (value !== 'Covered Call' && formData.stock_position_id) {
        // Clear stock_position_id if changing away from Covered Call
        setFormData(prev => ({
          ...prev,
          stock_position_id: ''
        }));
      }
    }

    // Auto-update stock_position_id when symbol changes for Covered Calls
    if (name === 'symbol' && formData.trade_type === 'Covered Call') {
      const matchingPosition = availableStockPositions.find(
        sp => sp.symbol.toUpperCase() === processedValue.toUpperCase()
      );
      if (matchingPosition) {
        setFormData(prev => ({
          ...prev,
          stock_position_id: matchingPosition.id.toString()
        }));
      }
    }
  };

  const validateForm = () => {
    const errors = {};

    // Account validation
    if (!formData.account_id) {
      errors.account_id = 'Please select an account';
    }
    
    // Symbol validation
    if (!formData.symbol || formData.symbol.trim() === '') {
      errors.symbol = 'Symbol is required (e.g., AAPL, TSLA)';
    } else if (formData.symbol.trim().length > 10) {
      errors.symbol = 'Symbol must be 10 characters or less';
    }
    
    // Trade type validation
    if (!formData.trade_type) {
      errors.trade_type = 'Please select a trade type';
    }
    
    // Strike price validation
    if (formData.trade_type !== 'Assignment' && !formData.strike_price) {
      errors.strike_price = 'Strike price is required';
    } else if (formData.strike_price) {
      const strike = parseFloat(formData.strike_price);
      if (isNaN(strike) || strike <= 0) {
        errors.strike_price = 'Strike price must be a positive number';
      } else if (strike > 10000) {
        errors.strike_price = 'Strike price seems unusually high. Please verify.';
      }
    }
    
    // Expiration date validation
    if (!formData.expiration_date) {
      errors.expiration_date = 'Expiration date is required';
    } else {
      const expDate = new Date(formData.expiration_date);
      const tradeDate = new Date(formData.trade_date || getTodayLocalDate());
      if (expDate < tradeDate) {
        errors.expiration_date = 'Expiration date must be on or after the trade date';
      }
      // Check if expiration is more than 5 years in the future (likely a mistake)
      const maxDate = new Date();
      maxDate.setFullYear(maxDate.getFullYear() + 5);
      if (expDate > maxDate) {
        errors.expiration_date = 'Expiration date seems too far in the future. Please verify.';
      }
    }
    
    // Contract quantity validation
    if (!formData.contract_quantity || parseInt(formData.contract_quantity) <= 0) {
      errors.contract_quantity = 'Contract quantity must be at least 1';
    } else {
      const qty = parseInt(formData.contract_quantity);
      if (isNaN(qty) || qty <= 0) {
        errors.contract_quantity = 'Contract quantity must be a positive whole number';
      } else if (qty > 1000) {
        errors.contract_quantity = 'Contract quantity seems unusually high. Please verify.';
      }
    }
    
    // Trade price validation
    if (formData.trade_type !== 'Assignment') {
      const tradePriceStr = formData.trade_price ? String(formData.trade_price) : '';
      if (!formData.trade_price || tradePriceStr.trim() === '') {
        errors.trade_price = 'Trade price is required';
      } else {
        const price = parseFloat(formData.trade_price);
        if (isNaN(price) || price <= 0) {
          errors.trade_price = 'Trade price must be a positive number';
        } else if (price > 1000) {
          errors.trade_price = 'Trade price seems unusually high. Please verify.';
        }
      }
      if (!formData.trade_action) {
        errors.trade_action = 'Please select a trade action';
      }
    }
    
    // Covered Call specific validation
    if (formData.trade_type === 'Covered Call') {
      if (!formData.stock_position_id) {
        errors.stock_position_id = 'Please select a stock position. You need to own shares to write a covered call.';
      } else {
        // Check if selected position has enough shares
        const selectedPosition = availableStockPositions.find(sp => sp.id === parseInt(formData.stock_position_id));
        if (selectedPosition) {
          const sharesNeeded = (parseInt(formData.contract_quantity) || 1) * 100;
          if (selectedPosition.available_shares < sharesNeeded) {
            errors.stock_position_id = `Insufficient shares. Need ${sharesNeeded} shares, but only ${selectedPosition.available_shares} available.`;
          }
        }
      }
    }
    
    // Fees validation
    if (formData.fees) {
      const feesStr = String(formData.fees);
      if (feesStr.trim() !== '') {
        const fees = parseFloat(formData.fees);
        if (isNaN(fees)) {
          errors.fees = 'Fees must be a number';
        } else if (fees < 0) {
          errors.fees = 'Fees cannot be negative';
        } else if (fees > 1000) {
          errors.fees = 'Fees seem unusually high. Please verify.';
        }
      }
    }
    
    // Trade date validation
    if (formData.trade_date) {
      const tradeDate = new Date(formData.trade_date);
      const today = new Date();
      today.setHours(23, 59, 59, 999); // End of today
      if (tradeDate > today) {
        errors.trade_date = 'Trade date cannot be in the future';
      }
      // Check if trade date is more than 10 years ago (likely a mistake)
      const minDate = new Date();
      minDate.setFullYear(minDate.getFullYear() - 10);
      if (tradeDate < minDate) {
        errors.trade_date = 'Trade date seems too far in the past. Please verify.';
      }
    }
    
    // Close details validation (when editing closed trades)
    if (trade && (trade.status === 'Closed' || trade.status === 'Expired' || trade.status === 'Assigned')) {
      if (formData.close_date) {
        const closeDate = new Date(formData.close_date);
        const tradeDate = new Date(formData.trade_date || trade.trade_date);
        if (closeDate < tradeDate) {
          errors.close_date = 'Close date cannot be before the trade date';
        }
        const today = new Date();
        today.setHours(23, 59, 59, 999);
        if (closeDate > today) {
          errors.close_date = 'Close date cannot be in the future';
        }
      }
      
      if (formData.close_method === 'buy_to_close' || formData.close_method === 'sell_to_close') {
        if (formData.close_price) {
          const closePriceStr = String(formData.close_price);
          if (closePriceStr.trim() !== '') {
            const price = parseFloat(formData.close_price);
            if (isNaN(price) || price <= 0) {
              errors.close_price = 'Close price must be a positive number';
            }
          }
        }
        if (formData.close_fees) {
          const closeFeesStr = String(formData.close_fees);
          if (closeFeesStr.trim() !== '') {
            const fees = parseFloat(formData.close_fees);
            if (isNaN(fees) || fees < 0) {
              errors.close_fees = 'Close fees must be 0 or greater';
            }
          }
        }
      }
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      const firstError = Object.values(fieldErrors)[0];
      showToast(firstError || 'Please fix the errors in the form', 'error');
      // Scroll to first error field
      const firstErrorField = document.querySelector('.error-field');
      if (firstErrorField) {
        firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
        firstErrorField.focus();
      }
      return;
    }

    setLoading(true);

    try {
      const payload = {
        account_id: parseInt(formData.account_id),
        symbol: formData.symbol.trim().toUpperCase(),
        trade_type: formData.trade_type,
        strike_price: formData.strike_price ? parseFloat(formData.strike_price) : null,
        expiration_date: formData.expiration_date || null,
        contract_quantity: parseInt(formData.contract_quantity) || 1,
        trade_price: formData.trade_type === 'Assignment' ? null : (formData.trade_price ? parseFloat(formData.trade_price) : null),
        trade_action: formData.trade_type === 'Assignment' ? null : formData.trade_action,
        fees: parseFloat(formData.fees) || 0,
        trade_date: formData.trade_date || getTodayLocalDate(),
        stock_position_id: formData.stock_position_id ? parseInt(formData.stock_position_id) : null,
        notes: formData.notes || null,
      };

      // Add close details if editing a closed trade
      if (trade && (trade.status === 'Closed' || trade.status === 'Expired' || trade.status === 'Assigned')) {
        payload.close_date = formData.close_date || null;
        payload.close_method = formData.close_method || null;
        payload.close_price = formData.close_price ? parseFloat(formData.close_price) : null;
        payload.close_fees = formData.close_fees ? parseFloat(formData.close_fees) : null;
        payload.assignment_price = formData.assignment_price ? parseFloat(formData.assignment_price) : null;
        // Only send close_premium if user explicitly entered a value (not empty string)
        // This allows backend to auto-calculate when close_price or close_fees change
        if (formData.close_premium && formData.close_premium !== '') {
          payload.close_premium = parseFloat(formData.close_premium);
        }
        // If close_premium is empty, don't send it so backend can auto-calculate
      }

      if (trade) {
        // Update existing trade
        await api.put(`/trades/${trade.id}`, payload);
        showToast('Trade updated successfully!', 'success');
      } else {
        // Create new trade
        await api.post('/trades', payload);
        showToast('Trade created successfully!', 'success');
      }

      onSuccess();
    } catch (error) {
      console.error('Error saving trade:', error);
      showToast(error.response?.data?.error || `Failed to ${trade ? 'update' : 'create'} trade`, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="modal-overlay" 
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
    >
      <div className="modal-content trade-form-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{trade ? 'Edit Trade' : 'Add New Trade'}</h2>
          <button 
            className="modal-close" 
            onClick={onCancel}
            type="button"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label>Account *</label>
              <select
                name="account_id"
                value={formData.account_id}
                onChange={handleChange}
                required
                className={fieldErrors.account_id ? 'error-field' : ''}
                // Allow editing account - backend will validate relationships
              >
                <option value="">Select Account</option>
                {accounts && accounts.map(account => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
              {fieldErrors.account_id && (
                <div className="field-error">{fieldErrors.account_id}</div>
              )}
            </div>

            <div className="form-group">
              <label>Symbol *</label>
              <input
                type="text"
                name="symbol"
                value={formData.symbol}
                onChange={handleChange}
                placeholder="e.g., AAPL"
                required
                className={fieldErrors.symbol ? 'error-field' : ''}
                style={{ textTransform: 'uppercase' }}
              />
              {fieldErrors.symbol && (
                <div className="field-error">{fieldErrors.symbol}</div>
              )}
            </div>

            <div className="form-group">
              <label>Trade Type *</label>
              <select
                name="trade_type"
                value={formData.trade_type}
                onChange={handleChange}
                required
                className={fieldErrors.trade_type ? 'error-field' : ''}
                // Allow editing trade type - backend will handle validation
              >
                <option value="CSP">Cash-Secured Put (CSP)</option>
                <option value="Covered Call">Covered Call</option>
                <option value="LEAPS">LEAPS</option>
              </select>
              {fieldErrors.trade_type && (
                <div className="field-error">{fieldErrors.trade_type}</div>
              )}
            </div>

            <div className="form-group">
              <label>Strike Price *</label>
              <input
                type="number"
                name="strike_price"
                value={formData.strike_price}
                onChange={handleChange}
                step="0.01"
                placeholder="e.g., 150.00"
                required
                className={fieldErrors.strike_price ? 'error-field' : ''}
              />
              {fieldErrors.strike_price && (
                <div className="field-error">{fieldErrors.strike_price}</div>
              )}
            </div>

            <div className="form-group">
              <label>Expiration Date *</label>
              <input
                type="date"
                name="expiration_date"
                value={formData.expiration_date}
                onChange={handleChange}
                required
                className={fieldErrors.expiration_date ? 'error-field' : ''}
              />
              {fieldErrors.expiration_date && (
                <div className="field-error">{fieldErrors.expiration_date}</div>
              )}
            </div>

            <div className="form-group">
              <label>Contracts *</label>
              <input
                type="number"
                name="contract_quantity"
                value={formData.contract_quantity}
                onChange={handleChange}
                min="1"
                required
                className={fieldErrors.contract_quantity ? 'error-field' : ''}
              />
              {fieldErrors.contract_quantity && (
                <div className="field-error">{fieldErrors.contract_quantity}</div>
              )}
            </div>

            {formData.trade_type !== 'Assignment' && (
              <>
                <div className="form-group">
                  <label>Trade Price *</label>
                  <input
                    type="number"
                    name="trade_price"
                    value={formData.trade_price}
                    onChange={handleChange}
                    step="0.01"
                    placeholder="e.g., 2.50"
                    required
                    className={fieldErrors.trade_price ? 'error-field' : ''}
                  />
                  {fieldErrors.trade_price && (
                    <div className="field-error">{fieldErrors.trade_price}</div>
                  )}
                </div>

                <div className="form-group">
                  <label>Trade Action *</label>
                  <select
                    name="trade_action"
                    value={formData.trade_action}
                    onChange={handleChange}
                    required
                    className={fieldErrors.trade_action ? 'error-field' : ''}
                  >
                    <option value="Sold to Open">Sold to Open</option>
                    <option value="Bought to Open">Bought to Open</option>
                  </select>
                  {fieldErrors.trade_action && (
                    <div className="field-error">{fieldErrors.trade_action}</div>
                  )}
                </div>
              </>
            )}

            <div className="form-group">
              <label>Fees</label>
              <input
                type="number"
                name="fees"
                value={formData.fees}
                onChange={handleChange}
                step="0.01"
                placeholder="e.g., 0.65"
                className={fieldErrors.fees ? 'error-field' : ''}
              />
              {fieldErrors.fees && (
                <div className="field-error">{fieldErrors.fees}</div>
              )}
            </div>

            {formData.trade_type === 'Covered Call' && (
              <div className="form-group">
                <label>Stock Position *</label>
                <select
                  name="stock_position_id"
                  value={formData.stock_position_id}
                  onChange={handleChange}
                  required
                  className={fieldErrors.stock_position_id ? 'error-field' : ''}
                >
                  <option value="">Select Stock Position</option>
                  {availableStockPositions.map(sp => {
                    const availableShares = sp.available_shares !== undefined ? sp.available_shares : sp.shares;
                    return (
                      <option key={sp.id} value={sp.id}>
                        {sp.symbol} - {sp.shares} shares @ ${sp.cost_basis_per_share} (Available: {availableShares})
                      </option>
                    );
                  })}
                </select>
                {fieldErrors.stock_position_id && (
                  <div className="field-error">{fieldErrors.stock_position_id}</div>
                )}
                {formData.trade_type === 'Covered Call' && !fieldErrors.stock_position_id && availableStockPositions.length === 0 && (
                  <div className="field-error" style={{ color: 'orange' }}>
                    No available stock positions found. Please create a stock position first.
                  </div>
                )}
              </div>
            )}

            <div className="form-group">
              <label>Trade Date</label>
              <input
                type="date"
                name="trade_date"
                value={formData.trade_date}
                onChange={handleChange}
              />
            </div>

            {/* Close details section - only show for closed trades */}
            {trade && (trade.status === 'Closed' || trade.status === 'Expired' || trade.status === 'Assigned') && (
              <>
                <div style={{ marginTop: '24px', marginBottom: '16px', paddingTop: '24px', borderTop: '1px solid var(--border-color)' }}>
                  <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)' }}>
                    Close Details
                  </h3>
                </div>

                <div className="form-group">
                  <label>Close Date</label>
                  <input
                    type="date"
                    name="close_date"
                    value={formData.close_date}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label>Close Method</label>
                  <select
                    name="close_method"
                    value={formData.close_method}
                    onChange={handleChange}
                  >
                    <option value="">Select Close Method</option>
                    <option value="buy_to_close">Buy to Close</option>
                    <option value="sell_to_close">Sell to Close</option>
                    <option value="expired">Expired</option>
                    <option value="assigned">Assigned</option>
                    <option value="exercise">Exercise</option>
                  </select>
                </div>

                {(formData.close_method === 'assigned' || formData.close_method === 'called_away') && (
                  <div className="form-group">
                    <label>{formData.close_method === 'called_away' ? 'Call Price *' : 'Assignment Price *'}</label>
                    <input
                      type="number"
                      name="assignment_price"
                      value={formData.assignment_price}
                      onChange={handleChange}
                      step="0.01"
                      placeholder={trade?.strike_price || 'e.g., 100.00'}
                      required
                    />
                    <small style={{ display: 'block', marginTop: '4px', color: 'var(--text-secondary)', fontSize: '12px' }}>
                      {formData.close_method === 'called_away' 
                        ? 'Price at which shares were called away (usually the strike price)'
                        : 'Price at which shares were assigned (usually the strike price)'}
                    </small>
                  </div>
                )}

                {formData.close_method && formData.close_method !== 'expired' && formData.close_method !== 'assigned' && formData.close_method !== 'called_away' && formData.close_method !== 'exercise' && (
                  <>
                    <div className="form-group">
                      <label>Close Price (per contract)</label>
                      <input
                        type="number"
                        name="close_price"
                        value={formData.close_price}
                        onChange={handleChange}
                        step="0.01"
                        placeholder="e.g., 2.50"
                      />
                    </div>

                    <div className="form-group">
                      <label>Close Fees</label>
                      <input
                        type="number"
                        name="close_fees"
                        value={formData.close_fees}
                        onChange={handleChange}
                        step="0.01"
                        placeholder="e.g., 0.65"
                      />
                    </div>
                  </>
                )}

                <div className="form-group">
                  <label>Close Premium</label>
                  <input
                    type="number"
                    name="close_premium"
                    value={formData.close_premium}
                    onChange={handleChange}
                    step="0.01"
                    placeholder="e.g., -250.00 (negative for buy to close)"
                  />
                  <small style={{ display: 'block', marginTop: '4px', color: 'var(--text-secondary)', fontSize: '12px' }}>
                    Negative for buy to close, positive for sell to close, 0 for expired/assigned/exercise
                  </small>
                </div>
              </>
            )}

            <div className="form-group">
              <label>Notes</label>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                rows="3"
                placeholder="Optional notes about this trade"
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Saving...' : (trade ? 'Update' : 'Create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default TradeFormDialog;
