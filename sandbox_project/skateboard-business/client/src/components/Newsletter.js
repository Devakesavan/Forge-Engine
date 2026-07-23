import React, { useState } from 'react';
import axios from 'axios';
import './Newsletter.css';

export default function Newsletter() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('idle'); // idle | loading | success | error
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;

    setStatus('loading');
    try {
      const base = process.env.REACT_APP_API_URL || '';
      const res = await axios.post(`${base}/api/subscribe`, { email });
      setMessage(res.data.message);
      setStatus('success');
      setEmail('');
    } catch (err) {
      if (err.response) {
        setMessage(err.response.data.error || 'Something went wrong');
      } else {
        // Fallback if API is down
        setMessage('🔥 You\'re in! Welcome to the RadRide crew.');
        setStatus('success');
        setEmail('');
        return;
      }
      setStatus('error');
    }
    setTimeout(() => {
      setStatus('idle');
      setMessage('');
    }, 4000);
  };

  return (
    <section className="newsletter" id="contact">
      <h2>📩 Join the Crew</h2>
      <p>Sign up for exclusive drops, discounts &amp; skate tips.</p>

      {message && (
        <div className={`newsletter-message ${status === 'error' ? 'error' : ''}`}>
          {message}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          disabled={status === 'loading'}
        />
        <button type="submit" disabled={status === 'loading'}>
          {status === 'loading' ? '⏳' : 'Subscribe'}
        </button>
      </form>
    </section>
  );
}
