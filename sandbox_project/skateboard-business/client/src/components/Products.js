import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './Products.css';

export default function Products({ products }) {
  const navigate = useNavigate();
  const sectionRef = useRef(null);

  // Scroll reveal
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.querySelectorAll('.reveal').forEach((el, i) => {
              setTimeout(() => el.classList.add('visible'), i * 150);
            });
          }
        });
      },
      { threshold: 0.1 }
    );
    if (sectionRef.current) observer.observe(sectionRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <section className="products" id="products" ref={sectionRef}>
      <h2 className="section-title">🔥 Pro Decks</h2>

      <div className="product-grid">
        {products.map((product) => (
          <div className="product-card reveal" key={product.id}>
            <div className="icon">{product.icon}</div>
            <h3>{product.name}</h3>
            <p>{product.tagline}</p>
            <div className="price">${product.price.toFixed(2)}</div>
            <button
              className="buy-btn"
              onClick={() => navigate(`/product/${product.id}`)}
            >
              View Details
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
