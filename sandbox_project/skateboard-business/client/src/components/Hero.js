import React from 'react';
import './Hero.css';

export default function Hero() {
  const scrollToProducts = () => {
    const el = document.getElementById('products');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="hero" id="home">
      <div className="hero-content">
        <div className="floating-skate">🛹</div>
        <h1>Ride the Fire</h1>
        <p>
          Premium skateboards built for speed, style, and total domination.<br />
          Whether you're a street legend or a ramp ripper — we've got your board.
        </p>
        <button className="cta-btn" onClick={scrollToProducts}>
          🔥 Shop Now
        </button>
      </div>
    </section>
  );
}
