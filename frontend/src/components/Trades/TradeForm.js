import React, { useState, useEffect } from 'react';
import api from '../../utils/api';
import './Trades.css';

function TradeForm({ accounts, trade, trades, onSuccess, onCancel }) {
  // Helper function to get today's date in local timezone (YYYY-MM-DD format)
  const getTodayLocalDate = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const [formData, setFormData] = useState({
    account_id: accounts.length > 0 ? accounts[0].id : '',
    symbol: '',
    trade_type: 'CSP',
    position_type: 'Open',
    strike_price: '',
    expiration_date: '',
    contract_quantity: 1,
    trade_price: '',
    trade_action: 'Sold to Open',
    fees: '',
    assignment_price: '',
    trade_date: getTodayLocalDate(),
    close_date: '',
    status: 'Open',
    parent_trade_id: '',
    notes: '',
  });
  const [calculatedPremium, setCalculatedPremium] = useState(0);
  const [calculatedRealizedPnl, setCalculatedRealizedPnl] = useState(0);
  const [parentTrade, setParentTrade] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  
  // Filter available parent trades based on trade type and action
  const getAvailableParentTrades = () => {
    if (!trades || !formData.symbol) return [];
    
    return trades.filter(t => {
      // Don't show the trade being edited
      if (t.id === trade?.id) return false;
      
      // Must be same symbol
      if (t.symbol !== formData.symbol) return false;
      
      // If closing a position (Bought to Close or Sold to Close), show positions with remaining open quantity
      // OR include the current parent trade even if it's closed (for editing purposes)
      if (formData.trade_action === 'Bought to Close' || formData.trade_action === 'Sold to Close') {
        // Include if it's the current parent trade (for editing)
        const isCurrentParent = trade && trade.parent_trade_id && t.id === trade.parent_trade_id;
        if (isCurrentParent) return true;
        
        // Include if it matches type and has remaining open quantity
        if (t.trade_type === formData.trade_type && t.trade_action && 
            (t.trade_action === 'Sold to Open' || t.trade_action === 'Bought to Open')) {
          // Check if there are remaining open contracts
          const remainingQty = t.remaining_open_quantity !== undefined 
            ? t.remaining_open_quantity 
            : (t.contract_quantity || 0);
          
          return remainingQty > 0;
        }
        return false;
      }
      
      // If creating Assignment, show open CSPs
      // OR include the current parent trade even if it's closed (for editing purposes)
      if (formData.trade_type === 'Assignment') {
        const isCurrentParent = trade && trade.parent_trade_id && t.id === trade.parent_trade_id;
        return (t.trade_type === 'CSP' && t.status === 'Open') || isCurrentParent;
      }
      
      // If creating Covered Call, show Assignment trades (stock positions)
      // OR include the current parent trade even if it's closed (for editing purposes)
      if (formData.trade_type === 'Covered Call') {
        const isCurrentParent = trade && trade.parent_trade_id && t.id === trade.parent_trade_id;
        return (t.trade_type === 'Assignment' && t.status === 'Assigned') || isCurrentParent;
      }
      
      return false;
    });
  };
  
  const availableParentTrades = getAvailableParentTrades();

  // Helper function to parse date string without timezone issues
  const parseDateString = (dateStr) => {
    if (!dateStr) return '';
    // If date string is in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss), extract just the date part
    const dateOnly = dateStr.split('T')[0];
    // Return as-is (YYYY-MM-DD format) - no timezone conversion needed
    return dateOnly;
  };

  // Load trade data if editing
  useEffect(() => {
    if (trade) {
      setFormData({
        account_id: trade.account_id,
        symbol: trade.symbol,
        trade_type: trade.trade_type,
        position_type: trade.position_type,
        strike_price: trade.strike_price || '',
        expiration_date: parseDateString(trade.expiration_date),
        contract_quantity: trade.contract_quantity || 1,
        trade_price: trade.trade_price || '',
        trade_action: trade.trade_action || 'Sold to Open',
        fees: trade.fees || '',
        assignment_price: trade.assignment_price || '',
        trade_date: parseDateString(trade.trade_date) || getTodayLocalDate(),
        close_date: parseDateString(trade.close_date),
        status: trade.status || 'Open',
        parent_trade_id: trade.parent_trade_id || '',
        notes: trade.notes || '',
      });
      if (trade.trade_price && trade.trade_action) {
        calculatePremium(trade.trade_price, trade.trade_action, trade.contract_quantity || 1, trade.fees || 0);
      }
      // Load parent trade if exists
      if (trade.parent_trade_id) {
        const parent = trades?.find(t => t.id === trade.parent_trade_id);
        setParentTrade(parent || null);
        if (parent && (trade.trade_action === 'Bought to Close' || trade.trade_action === 'Sold to Close')) {
          const closingPremium = trade.premium || 0;
          const parentPremium = parent.premium || 0;
          const parentQty = parent.contract_quantity || 1;
          const closingQty = trade.contract_quantity || 1;
          
          // Calculate proportional opening premium for the closed contracts
          const openingPremiumPerContract = parentPremium / parentQty;
          const openingPremiumForClosed = openingPremiumPerContract * closingQty;
          
          // Unified formula: Realized P&L = Opening Premium + Closing Premium
          setCalculatedRealizedPnl(openingPremiumForClosed + closingPremium);
        }
      }
    }
  }, [trade, trades]);

  const calculatePremium = (tradePrice, tradeAction, contractQty, fees) => {
    if (!tradePrice || !tradeAction || !contractQty) {
      setCalculatedPremium(0);
      return 0;
    }

    const price = parseFloat(tradePrice) || 0;
    const qty = parseInt(contractQty) || 1;
    const fee = parseFloat(fees) || 0;

    // Base premium: price per contract * quantity * 100 (options contract size)
    const basePremium = price * qty * 100;
    const totalFees = fee * qty;

    // Calculate based on trade action
    let premium = 0;
    if (tradeAction === 'Sold to Open' || tradeAction === 'Sold to Close') {
      // Receiving premium, subtract fees
      premium = basePremium - totalFees;
    } else if (tradeAction === 'Bought to Close' || tradeAction === 'Bought to Open') {
      // Paying premium, add fees (make negative)
      premium = -(basePremium + totalFees);
    }

    setCalculatedPremium(premium);
    return premium;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // Clear field error when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
    
    // Auto-set position_type based on trade_action
    let updatedData = { [name]: value };
    if (name === 'trade_action') {
      if (value === 'Bought to Close' || value === 'Sold to Close') {
        updatedData.position_type = 'Close';
      } else if (value === 'Sold to Open' || value === 'Bought to Open') {
        updatedData.position_type = 'Open';
      }
    }
    
    setFormData((prev) => ({
      ...prev,
      ...updatedData,
    }));

    // Recalculate premium when relevant fields change
    if (name === 'trade_price' || name === 'trade_action' || name === 'contract_quantity' || name === 'fees') {
      const newData = { ...formData, ...updatedData };
      const newPremium = calculatePremium(
        newData.trade_price,
        newData.trade_action,
        newData.contract_quantity,
        newData.fees
      );
      
      // If closing a trade, recalculate realized P&L (handle partial closes)
      if (parentTrade && (newData.trade_action === 'Bought to Close' || newData.trade_action === 'Sold to Close')) {
        const parentPremium = parentTrade.premium || 0;
        const parentQty = parentTrade.contract_quantity || 1;
        const closingQty = parseInt(newData.contract_quantity) || 1;
        
        // Calculate proportional opening premium for the closed contracts
        const openingPremiumPerContract = parentPremium / parentQty;
        const openingPremiumForClosed = openingPremiumPerContract * closingQty;
        
        // Unified formula: Realized P&L = Opening Premium + Closing Premium
        // This works for all scenarios because premiums are already signed correctly
        setCalculatedRealizedPnl(openingPremiumForClosed + newPremium);
      }
    }
    
    // Update parent trade when parent_trade_id changes
    if (name === 'parent_trade_id') {
      const selectedParent = trades?.find(t => t.id === parseInt(value));
      setParentTrade(selectedParent || null);
      
      // Auto-fill strike price and expiration from parent trade
      if (selectedParent) {
        const remainingQty = selectedParent.remaining_open_quantity !== undefined 
          ? selectedParent.remaining_open_quantity 
          : (selectedParent.contract_quantity || 0);
        
        setFormData((prev) => {
          const updates = {
            ...prev,
            strike_price: selectedParent.strike_price || prev.strike_price,
            expiration_date: selectedParent.expiration_date ? parseDateString(selectedParent.expiration_date) : prev.expiration_date,
            symbol: selectedParent.symbol || prev.symbol, // Also match symbol
            contract_quantity: Math.min(prev.contract_quantity || 1, remainingQty), // Don't exceed remaining
          };
          
          // For Assignment trades, auto-fill assignment_price from parent's strike_price
          if (prev.trade_type === 'Assignment' && selectedParent.strike_price) {
            updates.assignment_price = selectedParent.strike_price;
            updates.status = 'Assigned'; // Auto-set status to Assigned
          }
          
          return updates;
        });
      }
      
      // If closing a trade, calculate realized P&L (handle partial closes)
      if (selectedParent && (formData.trade_action === 'Bought to Close' || formData.trade_action === 'Sold to Close')) {
        const parentPremium = selectedParent.premium || 0;
        const parentQty = selectedParent.contract_quantity || 1;
        const closingQty = parseInt(formData.contract_quantity) || 1;
        
        // Calculate proportional opening premium for the closed contracts
        const openingPremiumPerContract = parentPremium / parentQty;
        const openingPremiumForClosed = openingPremiumPerContract * closingQty;
        
        // Unified formula: Realized P&L = Opening Premium + Closing Premium
        setCalculatedRealizedPnl(openingPremiumForClosed + calculatedPremium);
      }
    }
    
    // Auto-set status to 'Assigned' when trade_type changes to Assignment
    if (name === 'trade_type' && value === 'Assignment') {
      setFormData((prev) => ({
        ...prev,
        status: 'Assigned',
        trade_action: '', // Clear trade_action for Assignment
        trade_price: '', // Clear trade_price for Assignment
        assignment_price: parentTrade?.strike_price || prev.assignment_price || '', // Auto-fill from parent if available
      }));
    }
  };

  // Validation function
  const validateForm = () => {
    const errors = {};
    
    // Account is always required
    if (!formData.account_id) {
      errors.account_id = 'Please select an account';
    }
    
    // Symbol is always required
    if (!formData.symbol || formData.symbol.trim() === '') {
      errors.symbol = 'Symbol is required (e.g., AAPL, MSFT)';
    }
    
    // Trade type is always required
    if (!formData.trade_type) {
      errors.trade_type = 'Please select a trade type';
    }
    
    // Trade action is required for non-Assignment trades
    if (formData.trade_type !== 'Assignment' && !formData.trade_action) {
      errors.trade_action = 'Please select a trade action';
    }
    
    // Trade price is required for non-Assignment trades
    if (formData.trade_type !== 'Assignment') {
      if (!formData.trade_price || formData.trade_price === '') {
        errors.trade_price = 'Trade price is required (price per contract)';
      } else if (parseFloat(formData.trade_price) <= 0) {
        errors.trade_price = 'Trade price must be greater than 0';
      }
    }
    
    // Assignment price is required for Assignment trades
    if (formData.trade_type === 'Assignment') {
      if (!formData.assignment_price || formData.assignment_price === '') {
        errors.assignment_price = 'Assignment price is required (usually the strike price)';
      } else if (parseFloat(formData.assignment_price) <= 0) {
        errors.assignment_price = 'Assignment price must be greater than 0';
      }
    }
    
    // Trade date is always required
    if (!formData.trade_date) {
      errors.trade_date = 'Trade date is required';
    }
    
    // Contract quantity validation
    if (!formData.contract_quantity || parseInt(formData.contract_quantity) < 1) {
      errors.contract_quantity = 'Contract quantity must be at least 1';
    }
    
    // Parent trade validation for closing trades
    if (formData.trade_action === 'Bought to Close' || formData.trade_action === 'Sold to Close') {
      if (!formData.parent_trade_id) {
        errors.parent_trade_id = 'Please select the opening trade you are closing';
      } else if (parentTrade) {
        const remainingQty = parentTrade.remaining_open_quantity !== undefined 
          ? parentTrade.remaining_open_quantity 
          : (parentTrade.contract_quantity || 0);
        const closingQty = parseInt(formData.contract_quantity) || 0;
        
        if (closingQty > remainingQty) {
          errors.contract_quantity = `Cannot close ${closingQty} contracts. Only ${remainingQty} contracts remaining open.`;
        }
      }
    }
    
    // Parent trade validation for Assignment trades
    if (formData.trade_type === 'Assignment') {
      if (!formData.parent_trade_id) {
        errors.parent_trade_id = 'Please select the CSP that was assigned';
      }
    }
    
    // Parent trade validation for Covered Call trades
    if (formData.trade_type === 'Covered Call' && !formData.parent_trade_id) {
      errors.parent_trade_id = 'Please select the assignment (stock position) to sell calls on';
    }
    
    // Fees validation (if provided, must be non-negative)
    if (formData.fees && parseFloat(formData.fees) < 0) {
      errors.fees = 'Fees cannot be negative';
    }
    
    // Strike price validation (if provided, must be positive)
    if (formData.strike_price && parseFloat(formData.strike_price) <= 0) {
      errors.strike_price = 'Strike price must be greater than 0';
    }
    
    // Date validation: close_date should not be before trade_date
    if (formData.close_date && formData.trade_date) {
      const tradeDate = new Date(formData.trade_date);
      const closeDate = new Date(formData.close_date);
      if (closeDate < tradeDate) {
        errors.close_date = 'Close date cannot be before trade date';
      }
    }
    
    // Expiration date validation: should not be before trade_date
    if (formData.expiration_date && formData.trade_date) {
      const tradeDate = new Date(formData.trade_date);
      const expDate = new Date(formData.expiration_date);
      if (expDate < tradeDate) {
        errors.expiration_date = 'Expiration date cannot be before trade date';
      }
    }
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setFieldErrors({});
    
    // Validate form before submitting
    if (!validateForm()) {
      // Scroll to first error
      const firstErrorField = Object.keys(fieldErrors)[0];
      if (firstErrorField) {
        const element = document.querySelector(`[name="${firstErrorField}"]`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          element.focus();
        }
      }
      return;
    }
    
    setLoading(true);

    try {
      const payload = {
        ...formData,
        account_id: parseInt(formData.account_id),
        strike_price: formData.strike_price ? parseFloat(formData.strike_price) : null,
        expiration_date: formData.expiration_date || null,
        contract_quantity: parseInt(formData.contract_quantity) || 1,
        // For Assignment trades, don't send trade_price or trade_action
        trade_price: formData.trade_type === 'Assignment' ? null : (formData.trade_price ? parseFloat(formData.trade_price) : null),
        trade_action: formData.trade_type === 'Assignment' ? null : formData.trade_action,
        fees: parseFloat(formData.fees) || 0,
        assignment_price: formData.assignment_price ? parseFloat(formData.assignment_price) : null,
        close_date: formData.close_date || null,
        open_date: formData.open_date || null,
        parent_trade_id: formData.parent_trade_id ? parseInt(formData.parent_trade_id) : null,
        // Ensure status is 'Assigned' for Assignment trades
        status: formData.trade_type === 'Assignment' ? 'Assigned' : formData.status,
      };

      let response;
      if (trade) {
        // Update existing trade
        response = await api.put(`/trades/${trade.id}`, payload);
      } else {
        // Create new trade
        response = await api.post('/trades', payload);
      }

      onSuccess();
    } catch (err) {
      setError(err.response?.data?.error || `Failed to ${trade ? 'update' : 'create'} trade`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>{trade ? 'Edit Trade' : 'Add New Trade'}</h2>
      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '15px' }}>
          <div className="form-group">
            <label>Account *</label>
            <select
              name="account_id"
              value={formData.account_id}
              onChange={handleChange}
              required
            >
              <option value="">Select Account</option>
              {accounts.map((acc) => (
                <option key={acc.id} value={acc.id}>
                  {acc.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Symbol *</label>
            <input
              type="text"
              name="symbol"
              value={formData.symbol}
              onChange={handleChange}
              required
              placeholder="AAPL"
              className={fieldErrors.symbol ? 'error-field' : ''}
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
            >
              <option value="CSP">Cash-Secured Put (CSP)</option>
              <option value="Covered Call">Covered Call</option>
              <option value="LEAPS">LEAPS</option>
              <option value="Assignment">Assignment</option>
              <option value="Rollover">Rollover</option>
            </select>
            {fieldErrors.trade_type && (
              <div className="field-error">{fieldErrors.trade_type}</div>
            )}
          </div>

          {formData.trade_type !== 'Assignment' && (
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
                <option value="Bought to Close">Bought to Close</option>
                <option value="Bought to Open">Bought to Open</option>
                <option value="Sold to Close">Sold to Close</option>
              </select>
              {fieldErrors.trade_action && (
                <div className="field-error">{fieldErrors.trade_action}</div>
              )}
            </div>
          )}

          {(formData.trade_action === 'Bought to Close' || 
            formData.trade_action === 'Sold to Close' || 
            formData.trade_type === 'Assignment' || 
            formData.trade_type === 'Covered Call') && (
            <div className="form-group">
              <label>Parent Trade (Link to existing trade) *</label>
              <select
                name="parent_trade_id"
                value={formData.parent_trade_id}
                onChange={handleChange}
                required={formData.trade_action === 'Bought to Close' || formData.trade_action === 'Sold to Close' || formData.trade_type === 'Assignment' || formData.trade_type === 'Covered Call'}
                className={fieldErrors.parent_trade_id ? 'error-field' : ''}
              >
                <option value="">Select Parent Trade</option>
                {availableParentTrades.length === 0 ? (
                  <option value="" disabled>
                    No available parent trades (create the opening trade first)
                  </option>
                ) : (
                  availableParentTrades.map((parentTrade) => {
                    const remainingQty = parentTrade.remaining_open_quantity !== undefined 
                      ? parentTrade.remaining_open_quantity 
                      : (parentTrade.contract_quantity || 0);
                    return (
                      <option key={parentTrade.id} value={parentTrade.id}>
                        {parentTrade.trade_type} - {parentTrade.symbol} @ ${parentTrade.strike_price || 'N/A'} 
                        ({parentTrade.status}) - {remainingQty} contracts open - {parentTrade.trade_date ? (() => {
                          const [year, month, day] = parentTrade.trade_date.split('T')[0].split('-');
                          return new Date(parseInt(year), parseInt(month) - 1, parseInt(day)).toLocaleDateString();
                        })() : '-'}
                      </option>
                    );
                  })
                )}
              </select>
              {fieldErrors.parent_trade_id && (
                <div className="field-error">{fieldErrors.parent_trade_id}</div>
              )}
              <small style={{ color: '#666', fontSize: '12px' }}>
                {formData.trade_action === 'Bought to Close' || formData.trade_action === 'Sold to Close' 
                  ? 'Select the opening trade you are closing'
                  : formData.trade_type === 'Assignment'
                  ? 'Select the CSP that was assigned'
                  : 'Select the assignment (stock position) to sell calls on'}
              </small>
            </div>
          )}

          {formData.trade_type !== 'Assignment' && (
            <div className="form-group">
              <label>Position Type</label>
              <select
                name="position_type"
                value={formData.position_type}
                onChange={handleChange}
              >
                <option value="Open">Open</option>
                <option value="Close">Close</option>
              </select>
            </div>
          )}

          <div className="form-group">
            <label>Strike Price</label>
            <input
              type="number"
              step="0.01"
              name="strike_price"
              value={formData.strike_price}
              onChange={handleChange}
              placeholder="150.00"
              className={fieldErrors.strike_price ? 'error-field' : ''}
            />
            {fieldErrors.strike_price && (
              <div className="field-error">{fieldErrors.strike_price}</div>
            )}
          </div>

          <div className="form-group">
            <label>Expiration Date</label>
            <input
              type="date"
              name="expiration_date"
              value={formData.expiration_date}
              onChange={handleChange}
              className={fieldErrors.expiration_date ? 'error-field' : ''}
            />
            {fieldErrors.expiration_date && (
              <div className="field-error">{fieldErrors.expiration_date}</div>
            )}
          </div>

          <div className="form-group">
            <label>Contract Quantity</label>
            <input
              type="number"
              name="contract_quantity"
              value={formData.contract_quantity}
              onChange={handleChange}
              min="1"
              max={parentTrade && (formData.trade_action === 'Bought to Close' || formData.trade_action === 'Sold to Close')
                ? (parentTrade.remaining_open_quantity !== undefined ? parentTrade.remaining_open_quantity : parentTrade.contract_quantity)
                : undefined}
              className={fieldErrors.contract_quantity ? 'error-field' : ''}
            />
            {fieldErrors.contract_quantity && (
              <div className="field-error">{fieldErrors.contract_quantity}</div>
            )}
            {parentTrade && (formData.trade_action === 'Bought to Close' || formData.trade_action === 'Sold to Close') && !fieldErrors.contract_quantity && (
              <small style={{ color: '#666', fontSize: '12px', display: 'block', marginTop: '5px' }}>
                {parentTrade.remaining_open_quantity !== undefined 
                  ? `${parentTrade.remaining_open_quantity} contracts remaining open`
                  : `${parentTrade.contract_quantity} contracts total`}
              </small>
            )}
          </div>

          {formData.trade_type !== 'Assignment' && (
            <div className="form-group">
              <label>Trade Price (per contract) *</label>
              <input
                type="number"
                step="0.01"
                name="trade_price"
                value={formData.trade_price}
                onChange={handleChange}
                required
                placeholder="5.00"
                className={fieldErrors.trade_price ? 'error-field' : ''}
              />
              {fieldErrors.trade_price && (
                <div className="field-error">{fieldErrors.trade_price}</div>
              )}
              {!fieldErrors.trade_price && (
                <small style={{ color: '#666', fontSize: '12px' }}>
                  Price per contract (e.g., $5.00)
                </small>
              )}
            </div>
          )}

          <div className="form-group">
            <label>Fees (per contract)</label>
            <input
              type="number"
              step="0.01"
              name="fees"
              value={formData.fees}
              onChange={handleChange}
              placeholder="0.50"
              className={fieldErrors.fees ? 'error-field' : ''}
            />
            {fieldErrors.fees && (
              <div className="field-error">{fieldErrors.fees}</div>
            )}
            {!fieldErrors.fees && (
              <small style={{ color: '#666', fontSize: '12px' }}>
                Fee per contract (e.g., $0.50)
              </small>
            )}
          </div>

          {formData.trade_type !== 'Assignment' && (
            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label>Calculated Premium</label>
              <div style={{
                padding: '10px',
                backgroundColor: calculatedPremium >= 0 ? '#d4edda' : '#f8d7da',
                color: calculatedPremium >= 0 ? '#155724' : '#721c24',
                borderRadius: '4px',
                fontWeight: 'bold',
                fontSize: '16px'
              }}>
                ${calculatedPremium.toFixed(2)}
                <small style={{ display: 'block', fontSize: '12px', fontWeight: 'normal', marginTop: '5px' }}>
                  {calculatedPremium >= 0 ? 'Premium Received' : 'Premium Paid'}
                </small>
              </div>
              <small style={{ color: '#666', fontSize: '12px', display: 'block', marginTop: '5px' }}>
                Formula: (Trade Price × Quantity × 100) {formData.trade_action?.includes('Sold') ? '-' : '+'} (Fees × Quantity)
              </small>
            </div>
          )}
          
          {formData.trade_type === 'Assignment' && parentTrade && (
            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label>Assignment Information</label>
              <div style={{
                padding: '15px',
                backgroundColor: '#f8f9fa',
                borderRadius: '4px',
                border: '1px solid #dee2e6'
              }}>
                <div style={{ marginBottom: '10px' }}>
                  <strong>Parent CSP Premium Received:</strong> ${(parentTrade.premium || 0).toFixed(2)}
                  <small style={{ display: 'block', color: '#666', fontSize: '12px', marginTop: '3px' }}>
                    This premium is the realized P&L for the CSP that was assigned. The Assignment trade itself has no P&L.
                  </small>
                </div>
                <div>
                  <strong>Assignment Price:</strong> ${formData.assignment_price || parentTrade.strike_price || 'N/A'}
                  <small style={{ display: 'block', color: '#666', fontSize: '12px', marginTop: '3px' }}>
                    Price at which you were assigned {formData.contract_quantity * 100} shares
                  </small>
                </div>
              </div>
            </div>
          )}

          {/* Show opening premium and realized P&L when closing a trade */}
          {(formData.trade_action === 'Bought to Close' || formData.trade_action === 'Sold to Close') && parentTrade && (
            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label>Realized P&L Calculation</label>
              <div style={{
                padding: '15px',
                backgroundColor: '#f8f9fa',
                borderRadius: '4px',
                border: '1px solid #dee2e6'
              }}>
                <div style={{ marginBottom: '10px' }}>
                  <strong>Opening Premium:</strong> ${(parentTrade.premium || 0).toFixed(2)} ({parentTrade.contract_quantity || 1} contracts)
                  <small style={{ display: 'block', color: '#666', fontSize: '12px', marginTop: '3px' }}>
                    From trade on {parentTrade.trade_date ? (() => {
                      const [year, month, day] = parentTrade.trade_date.split('T')[0].split('-');
                      return new Date(parseInt(year), parseInt(month) - 1, parseInt(day)).toLocaleDateString();
                    })() : '-'}
                    {formData.contract_quantity && parseInt(formData.contract_quantity) < (parentTrade.contract_quantity || 1) && (
                      <span style={{ display: 'block', marginTop: '3px' }}>
                        Proportional premium for {formData.contract_quantity} contracts: ${((parentTrade.premium || 0) / (parentTrade.contract_quantity || 1) * parseInt(formData.contract_quantity)).toFixed(2)}
                      </span>
                    )}
                  </small>
                </div>
                <div style={{ marginBottom: '10px' }}>
                  <strong>Closing Premium:</strong> ${calculatedPremium.toFixed(2)}
                </div>
                <div style={{
                  padding: '10px',
                  backgroundColor: calculatedRealizedPnl >= 0 ? '#d4edda' : '#f8d7da',
                  color: calculatedRealizedPnl >= 0 ? '#155724' : '#721c24',
                  borderRadius: '4px',
                  fontWeight: 'bold',
                  fontSize: '16px',
                  marginTop: '10px'
                }}>
                  <strong>Realized P&L:</strong> ${calculatedRealizedPnl.toFixed(2)}
                  <small style={{ display: 'block', fontSize: '12px', fontWeight: 'normal', marginTop: '5px' }}>
                    Formula: Opening Premium - Closing Premium
                  </small>
                </div>
              </div>
            </div>
          )}

          <div className="form-group">
            <label>Assignment Price {formData.trade_type === 'Assignment' && '*'}</label>
            <input
              type="number"
              step="0.01"
              name="assignment_price"
              value={formData.assignment_price}
              onChange={handleChange}
              required={formData.trade_type === 'Assignment'}
              placeholder={formData.trade_type === 'Assignment' ? "Price at which stock was assigned (usually the strike price)" : "For assignments only"}
              className={fieldErrors.assignment_price ? 'error-field' : ''}
            />
            {fieldErrors.assignment_price && (
              <div className="field-error">{fieldErrors.assignment_price}</div>
            )}
            {formData.trade_type === 'Assignment' && !fieldErrors.assignment_price && (
              <small style={{ color: '#666', fontSize: '12px' }}>
                The price at which you were assigned the stock (typically the strike price of the CSP)
              </small>
            )}
          </div>

          <div className="form-group">
            <label>Trade Date *</label>
            <input
              type="date"
              name="trade_date"
              value={formData.trade_date}
              onChange={handleChange}
              required
              className={fieldErrors.trade_date ? 'error-field' : ''}
            />
            {fieldErrors.trade_date && (
              <div className="field-error">{fieldErrors.trade_date}</div>
            )}
            {!fieldErrors.trade_date && (
              <small style={{ color: '#666', fontSize: '12px', display: 'block', marginTop: '5px' }}>
                Date when this trade was executed/entered
              </small>
            )}
          </div>

          <div className="form-group">
            <label>Close Date</label>
            <input
              type="date"
              name="close_date"
              value={formData.close_date}
              onChange={handleChange}
              className={fieldErrors.close_date ? 'error-field' : ''}
            />
            {fieldErrors.close_date && (
              <div className="field-error">{fieldErrors.close_date}</div>
            )}
            {!fieldErrors.close_date && (
              <small style={{ color: '#666', fontSize: '12px', display: 'block', marginTop: '5px' }}>
                Date when position was closed (used for return calculations). For closing trades, this is typically the same as Trade Date.
              </small>
            )}
          </div>

          <div className="form-group">
            <label>Status</label>
            <select
              name="status"
              value={formData.status}
              onChange={handleChange}
              disabled={formData.trade_type === 'Assignment'}
            >
              <option value="Open">Open</option>
              <option value="Closed">Closed</option>
              <option value="Assigned">Assigned</option>
            </select>
            {formData.trade_type === 'Assignment' && (
              <small style={{ color: '#666', fontSize: '12px', display: 'block', marginTop: '5px' }}>
                Assignment trades are automatically set to 'Assigned' status
              </small>
            )}
          </div>
        </div>

        <div className="form-group">
          <label>Notes</label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows="3"
            placeholder="Additional notes about this trade..."
          />
        </div>

        {error && <div className="error">{error}</div>}

        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? (trade ? 'Updating...' : 'Creating...') : (trade ? 'Update Trade' : 'Create Trade')}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default TradeForm;
