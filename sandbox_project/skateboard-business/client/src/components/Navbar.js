import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useCart } from '../CartContext';
import './Navbar.css';

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { cart } = useCart();
  const location = useLocation();

  const isHome = location.pathname === '/';

  const scrollTo = (id) => {
    setMenuOpen(false);
    if (!isHome) {
      window.location.href = `/#${id}`;
      return;
    }
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <nav className="navbar">
      <Link to="/" className="logo" onClick={() => setMenuOpen(false)}>
        🛹 Rad<span>Ride</span>
      </Link>
      <ul className={`nav-links ${menuOpen ? 'active' : ''}`}>
        <li>
          {isHome ? (
            <a href="#home" onClick={(e) => { e.preventDefault(); scrollTo('home'); }}>Home</a>
          ) : (
            <Link to="/" onClick={() => setMenuOpen(false)}>Home</Link>
          )}
        </li>
        <li>
          {isHome ? (
            <a href="#products" onClick={(e) => { e.preventDefault(); scrollTo('products'); }}>Decks</a>
          ) : (
            <Link to="/" onClick={() => setMenuOpen(false)}>Decks</Link>
          )}
        </li>
        <li>
          {isHome ? (
            <a href="#features" onClick={(e) => { e.preventDefault(); scrollTo('features'); }}>Why Us</a>
          ) : (
            <Link to="/" onClick={() => setMenuOpen(false)}>Why Us</Link>
          )}
        </li>
        <li>
          {isHome ? (
            <a href="#testimonials" onClick={(e) => { e.preventDefault(); scrollTo('testimonials'); }}>Reviews</a>
          ) : (
            <Link to="/" onClick={() => setMenuOpen(false)}>Reviews</Link>
          )}
        </li>
        <li className="nav-cart-item">
          <Link to="/cart" className="cart-link" onClick={() => setMenuOpen(false)}>
            🛒 Cart
            {cart.totalItems > 0 && <span className="cart-badge">{cart.totalItems}</span>}
          </Link>
        </li>
      </ul>
      <div className="hamburger" onClick={() => setMenuOpen(!menuOpen)}>
        <span></span><span></span><span></span>
      </div>
      {/* Mobile cart icon */}
      <Link to="/cart" className="mobile-cart" onClick={() => setMenuOpen(false)}>
        🛒
        {cart.totalItems > 0 && <span className="cart-badge mobile">{cart.totalItems}</span>}
      </Link>
    </nav>
  );
}
