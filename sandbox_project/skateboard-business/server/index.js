const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// -------------------------------------------------------
// In-memory data store (simulates a database)
// -------------------------------------------------------
const products = [
  {
    id: 1,
    name: 'Street Ripper',
    tagline: 'Lightweight maple deck, perfect for flips & grinds.',
    price: 89.99,
    icon: '🛹',
    category: 'street',
    description: 'The Street Ripper is our flagship deck — 7-ply Canadian maple with a medium concave for the perfect balance of pop and control. Designed for street skaters who demand precision on flip tricks, grinds, and manuals. Features reinforced truck mounts and a durable grip tape that lasts season after season.',
  },
  {
    id: 2,
    name: 'Inferno Cruiser',
    tagline: 'Wide cruiser with soft wheels — smooth ride, blazing style.',
    price: 109.99,
    icon: '🔥',
    category: 'cruiser',
    description: 'The Inferno Cruiser combines a wide, stable deck with soft 78A wheels for the smoothest ride on rough pavement. Perfect for commuting, carving, and cruising in style. The unique flame graphic is heat-pressed and will never fade. Includes precision bearings for effortless rolling.',
  },
  {
    id: 3,
    name: 'Thunder Pro',
    tagline: 'Pro-level stiffness & pop for vert ramps and bowls.',
    price: 129.99,
    icon: '⚡',
    category: 'pro',
    description: 'Built for the vert ramp and bowl riders, the Thunder Pro features an extra-stiff 8-ply construction with carbon fiber reinforcement. The steep kicktail and symmetrical nose give you maximum pop for aerial tricks. Trusted by pro riders worldwide for competition-level performance.',
  },
  {
    id: 4,
    name: 'Skull Crusher',
    tagline: 'Heavy-duty longboard for downhill speed demons.',
    price: 149.99,
    icon: '💀',
    category: 'longboard',
    description: 'The Skull Crusher is a downhill longboard built for speed and stability. The 40-inch deck features a drop-through truck mount for a lower center of gravity, making high-speed runs feel locked in. Equipped with 83A downhill wheels and precision trucks for carving at 40+ mph.',
  },
];

const features = [
  { icon: '🏆', title: 'Pro Quality', desc: '7-ply Canadian maple decks tested by pro riders.' },
  { icon: '🎨', title: 'Custom Art', desc: 'Unique, hand-drawn graphics on every deck.' },
  { icon: '🚀', title: 'Fast Shipping', desc: 'Free express shipping on all orders over $99.' },
  { icon: '💯', title: 'Lifetime Warranty', desc: 'We stand by our boards — no questions asked.' },
];

const testimonials = [
  { id: 1, stars: 5, text: "Best board I've ever ridden. The pop is insane and the grip is unreal!", author: 'Jake T.' },
  { id: 2, stars: 5, text: 'The custom artwork turned heads at the skatepark. Everyone asked where I got it.', author: 'Maya R.' },
  { id: 3, stars: 5, text: 'Fastest shipping ever. Ordered on Monday, had it by Wednesday. Love it!', author: 'Carlos M.' },
];

const subscribers = [];

// -------------------------------------------------------
// API Routes
// -------------------------------------------------------

// GET /api/products
app.get('/api/products', (req, res) => {
  const { category } = req.query;
  let result = products;
  if (category) {
    result = products.filter((p) => p.category === category);
  }
  res.json(result);
});

// GET /api/products/:id
app.get('/api/products/:id', (req, res) => {
  const product = products.find((p) => p.id === Number(req.params.id));
  if (!product) return res.status(404).json({ error: 'Product not found' });
  res.json(product);
});

// GET /api/features
app.get('/api/features', (req, res) => {
  res.json(features);
});

// GET /api/testimonials
app.get('/api/testimonials', (req, res) => {
  res.json(testimonials);
});

// POST /api/subscribe
app.post('/api/subscribe', (req, res) => {
  const { email } = req.body;
  if (!email) return res.status(400).json({ error: 'Email is required' });

  // Simple email format check
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return res.status(400).json({ error: 'Invalid email format' });
  }

  if (subscribers.find((s) => s.email === email)) {
    return res.status(409).json({ error: 'Email already subscribed' });
  }

  subscribers.push({ email, subscribedAt: new Date().toISOString() });
  console.log(`📩 New subscriber: ${email} (total: ${subscribers.length})`);
  res.status(201).json({ message: 'Successfully subscribed! Welcome to the RadRide crew 🔥' });
});

// POST /api/orders (simulate a purchase)
app.post('/api/orders', (req, res) => {
  const { productId, quantity = 1 } = req.body;
  if (!productId) return res.status(400).json({ error: 'productId is required' });

  const product = products.find((p) => p.id === Number(productId));
  if (!product) return res.status(404).json({ error: 'Product not found' });

  const total = (product.price * quantity).toFixed(2);
  console.log(`🛒 Order placed: ${product.name} x${quantity} = $${total}`);

  res.status(201).json({
    message: `Order placed! ${product.name} x${quantity} — total $${total}. Shipping soon! 🛹`,
    order: { product: product.name, quantity, total: `$${total}` },
  });
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', subscribers: subscribers.length });
});

// -------------------------------------------------------
// Serve React build in production
// -------------------------------------------------------
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '..', 'client', 'build')));
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'client', 'build', 'index.html'));
  });
}

// -------------------------------------------------------
// Start server
// -------------------------------------------------------
app.listen(PORT, () => {
  console.log(`\n🛹 RadRide API server running on http://localhost:${PORT}`);
  console.log(`   Health check: http://localhost:${PORT}/api/health\n`);
});
