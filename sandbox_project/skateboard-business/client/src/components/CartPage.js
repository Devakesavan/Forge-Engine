import React from 'react';
import { Link } from 'react-router-dom';
import { useCart } from '../CartContext';
import './CartPage.css';

export default function CartPage() {
  const { cart, addToCart, removeFromCart, updateQuantity, clearCart } = useCart();

  const handleCheckout = () => {
    if (cart.items.length === 0) return;
    const itemsList = cart.items
      .map((i) => `${i.icon} ${i.name} x${i.quantity} = $${(i.price * i.quantity).toFixed(2)}`)
      .join('\n');
    alert(
      `🛹 ORDER SUMMARY\n\n${itemsList}\n\n──────────────\nTotal: $${cart.totalPrice.toFixed(2)}\n\n🔥 Thanks for shopping RadRide! Your boards will ship ASAP.`
    );
    clearCart();
  };

  return (
    <section className="cart-page">
      <div className="cart-backdrop" />

      <div className="cart-container">
        <div className="cart-header">
          <h1 className="cart-title">🛒 Your Cart</h1>
          {cart.items.length > 0 && (
            <button className="clear-cart-btn" onClick={clearCart}>
              🗑️ Clear All
            </button>
          )}
        </div>

        {cart.items.length === 0 ? (
          <div className="cart-empty">
            <div className="empty-icon">🛹</div>
            <h2>Your cart is empty</h2>
            <p>Time to grab a new deck!</p>
            <Link to="/" className="shop-link">← Shop Decks</Link>
          </div>
        ) : (
          <>
            <div className="cart-items">
              {cart.items.map((item) => (
                <div className="cart-item" key={item.id}>
                  <div className="cart-item-icon">{item.icon}</div>

                  <div className="cart-item-info">
                    <h3 className="cart-item-name">{item.name}</h3>
                    <p className="cart-item-tagline">{item.tagline}</p>
                    <div className="cart-item-price">
                      ${(item.price * item.quantity).toFixed(2)}
                    </div>
                  </div>

                  <div className="cart-item-controls">
                    <div className="qty-controls">
                      <button
                        className="qty-btn"
                        onClick={() => updateQuantity(item.id, item.quantity - 1)}
                        disabled={item.quantity <= 1}
                      >
                        −
                      </button>
                      <span className="qty-value">{item.quantity}</span>
                      <button
                        className="qty-btn"
                        onClick={() => updateQuantity(item.id, item.quantity + 1)}
                      >
                        +
                      </button>
                    </div>
                    <button
                      className="remove-btn"
                      onClick={() => removeFromCart(item.id)}
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="cart-summary">
              <div className="summary-row">
                <span>Total Items</span>
                <span>{cart.totalItems}</span>
              </div>
              <div className="summary-row total">
                <span>Total Price</span>
                <span>${cart.totalPrice.toFixed(2)}</span>
              </div>
              <button className="checkout-btn" onClick={handleCheckout}>
                🔥 Checkout — ${cart.totalPrice.toFixed(2)}
              </button>
              <Link to="/" className="continue-shopping">
                ← Continue Shopping
              </Link>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
