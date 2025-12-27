import React, { useState } from 'react';
import Navbar from '../Layout/Navbar';
import Footer from '../Layout/Footer';
import VIXCalculator from './VIXCalculator';

function Tools() {
  return (
    <div className="page-wrapper">
      <Navbar />
      <div className="container">
        <h1>Tools</h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '30px' }}>
          Useful calculators and tools for options traders.
        </p>
        
        <VIXCalculator />
      </div>
      <Footer />
    </div>
  );
}

export default Tools;

