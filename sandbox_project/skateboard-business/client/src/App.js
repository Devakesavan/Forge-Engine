import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CartProvider } from './CartContext';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Products from './components/Products';
import Features from './components/Features';
import Testimonials from './components/Testimonials';
import Newsletter from './components/Newsletter';
import Footer from './components/Footer';
import ParticleCanvas from './components/ParticleCanvas';
import ProductDetail from './components/ProductDetail';
import CartPage from './components/CartPage';
import './App.css';

function HomePage({ products, features, testimonials }) {
  return (
    <>
      <Hero />
      <Products products={products} />
      <Features features={features} />
      <Testimonials testimonials={testimonials} />
      <Newsletter />
    </>
  );
}

function App() {
  const [products, setProducts] = useState([]);
  const [features, setFeatures] = useState([]);
  const [testimonials, setTestimonials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const base = process.env.REACT_APP_API_URL || '';
        const [productsRes, featuresRes, testimonialsRes] = await Promise.all([
          fetch(`${base}/api/products`),
          fetch(`${base}/api/features`),
          fetch(`${base}/api/testimonials`),
        ]);
        if (!productsRes.ok || !featuresRes.ok || !testimonialsRes.ok) {
          throw new Error('Failed to load data');
        }
        const productsData = await productsRes.json();
        const featuresData = await featuresRes.json();
        const testimonialsData = await testimonialsRes.json();
        setProducts(productsData);
        setFeatures(featuresData);
        setTestimonials(testimonialsData);
      } catch (err) {
        console.error('Fetch error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Fallback static data if API is unreachable
  const fallbackProducts = [
    { id: 1, name: 'Street Ripper', tagline: 'Lightweight maple deck, perfect for flips & grinds.', price: 89.99, icon: '🛹', category: 'street', description: 'The Street Ripper is our flagship deck — 7-ply Canadian maple with a medium concave for the perfect balance of pop and control. Designed for street skaters who demand precision on flip tricks, grinds, and manuals. Features reinforced truck mounts and a durable grip tape that lasts season after season.' },
    { id: 2, name: 'Inferno Cruiser', tagline: 'Wide cruiser with soft wheels — smooth ride, blazing style.', price: 109.99, icon: '🔥', category: 'cruiser', description: 'The Inferno Cruiser combines a wide, stable deck with soft 78A wheels for the smoothest ride on rough pavement. Perfect for commuting, carving, and cruising in style. The unique flame graphic is heat-pressed and will never fade. Includes precision bearings for effortless rolling.' },
    { id: 3, name: 'Thunder Pro', tagline: 'Pro-level stiffness & pop for vert ramps and bowls.', price: 129.99, icon: '⚡', category: 'pro', description: 'Built for the vert ramp and bowl riders, the Thunder Pro features an extra-stiff 8-ply construction with carbon fiber reinforcement. The steep kicktail and symmetrical nose give you maximum pop for aerial tricks. Trusted by pro riders worldwide for competition-level performance.' },
    { id: 4, name: 'Skull Crusher', tagline: 'Heavy-duty longboard for downhill speed demons.', price: 149.99, icon: '💀', category: 'longboard', description: 'The Skull Crusher is a downhill longboard built for speed and stability. The 40-inch deck features a drop-through truck mount for a lower center of gravity, making high-speed runs feel locked in. Equipped with 83A downhill wheels and precision trucks for carving at 40+ mph.' },
  ];
  const fallbackFeatures = [
    { icon: '🏆', title: 'Pro Quality', desc: '7-ply Canadian maple decks tested by pro riders.' },
    { icon: '🎨', title: 'Custom Art', desc: 'Unique, hand-drawn graphics on every deck.' },
    { icon: '🚀', title: 'Fast Shipping', desc: 'Free express shipping on all orders over $99.' },
    { icon: '💯', title: 'Lifetime Warranty', desc: 'We stand by our boards — no questions asked.' },
  ];
  const fallbackTestimonials = [
    { id: 1, stars: 5, text: "Best board I've ever ridden. The pop is insane!", author: 'Jake T.' },
    { id: 2, stars: 5, text: 'Custom artwork turned heads at the skatepark!', author: 'Maya R.' },
    { id: 3, stars: 5, text: 'Fastest shipping ever. Ordered Monday, arrived Wednesday!', author: 'Carlos M.' },
  ];

  const displayProducts = products.length > 0 ? products : fallbackProducts;
  const displayFeatures = features.length > 0 ? features : fallbackFeatures;
  const displayTestimonials = testimonials.length > 0 ? testimonials : fallbackTestimonials;

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#0b0b1a' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '4rem', animation: 'float 1.5s ease-in-out infinite' }}>🛹</div>
          <p style={{ color: '#ffd200', fontFamily: 'Bangers, cursive', fontSize: '2rem', marginTop: 20, letterSpacing: 2 }}>Loading...</p>
          <style>{`@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }`}</style>
        </div>
      </div>
    );
  }

  return (
    <CartProvider>
      <Router>
        <div className="App">
          <ParticleCanvas />
          <Navbar />
          <Routes>
            <Route
              path="/"
              element={
                <HomePage
                  products={displayProducts}
                  features={displayFeatures}
                  testimonials={displayTestimonials}
                />
              }
            />
            <Route
              path="/product/:id"
              element={<ProductDetail products={displayProducts} />}
            />
            <Route path="/cart" element={<CartPage />} />
          </Routes>
          <Footer />
        </div>
      </Router>
    </CartProvider>
  );
}

export default App;
