import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useCart } from '../CartContext';
import './ProductDetail.css';

export default function ProductDetail({ products }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToCart, cart } = useCart();
  const [added, setAdded] = useState(false);

  const product = products.find((p) => p.id === Number(id));

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [id]);

  if (!product) {
    return (
      <div className="detail-not-found">
        <div className="detail-not-found-content">
          <div style={{ fontSize: '4rem', marginBottom: 20 }}>🔍</div>
          <h2>Product Not Found</h2>
          <p>The skateboard you're looking for rolled away!</p>
          <Link to="/" className="back-home-btn">← Back to Shop</Link>
        </div>
      </div>
    );
  }

  const handleAddToCart = () => {
    addToCart({
      id: product.id,
      name: product.name,
      price: product.price,
      icon: product.icon,
      tagline: product.tagline,
    });
    setAdded(true);
    setTimeout(() => setAdded(false), 2500);
  };

  const cartItem = cart.items.find((i) => i.id === product.id);
  const inCartQuantity = cartItem ? cartItem.quantity : 0;

  return (
    <section className="product-detail">
      <div className="detail-backdrop" />

      <div className="detail-container">
        <button className="detail-back-btn" onClick={() => navigate(-1)}>
          ← Back
        </button>

        <div className="detail-card">
          <div className="detail-icon">{product.icon}</div>

          <div className="detail-info">
            <span className="detail-category">{product.category || 'deck'}</span>
            <h1 className="detail-name">{product.name}</h1>
            <div className="detail-price">${product.price.toFixed(2)}</div>

            <div className="detail-divider" />

            <p className="detail-description">
              {product.description || product.tagline}
            </p>

            <div className="detail-specs">
              <div className="spec-item">
                <span className="spec-label">Deck</span>
                <span className="spec-value">7-ply Maple</span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Wheels</span>
                <span className="spec-value">52mm 99A</span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Bearings</span>
                <span className="spec-value">ABEC-7</span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Warranty</span>
                <span className="spec-value">Lifetime</span>
              </div>
            </div>

            <div className="detail-actions">
              <button
                className={`add-to-cart-btn ${added ? 'added' : ''}`}
                onClick={handleAddToCart}
              >
                {added ? '✅ Added!' : '🛒 Add to Cart'}
              </button>

              <Link to="/cart" className="view-cart-btn">
                View Cart ({cart.totalItems})
              </Link>
            </div>

            {inCartQuantity > 0 && (
              <div className="in-cart-notice">
                🛹 {inCartQuantity} in your cart
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
