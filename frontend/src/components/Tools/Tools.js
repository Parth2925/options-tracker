import React, { useState } from 'react';
import Navbar from '../Layout/Navbar';
import VIXCalculator from './VIXCalculator';

function Tools() {
  return (
    <>
      <Navbar />
      <div className="container">
        <h1>Tools</h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '30px' }}>
          Useful calculators and tools for options traders.
        </p>
        
        <VIXCalculator />
      </div>
    </>
  );
}

export default Tools;

