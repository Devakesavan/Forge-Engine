import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { config } from 'dotenv';

config();

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const clientDist = process.env.CLIENT_DIST || path.join(__dirname, '..', 'client', 'dist');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('dev'));
app.use(express.json());

// In-memory data store (replace with database in production)
let menuItems = [
  {
    id: 1,
    name: 'Espresso',
    description: 'Rich and bold single-origin espresso shot',
    price: 3.50,
    category: 'coffee',
    image: 'https://images.unsplash.com/photo-1510707577719-ae7c14805e3a?w=400&h=300&fit=crop',
    available: true
  },
  {
    id: 2,
    name: 'Cappuccino',
    description: 'Espresso with steamed milk and velvety foam',
    price: 4.50,
    category: 'coffee',
    image: 'https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=400&h=300&fit=crop',
    available: true
  },
  {
    id: 3,
    name: 'Latte',
    description: 'Smooth espresso with steamed milk and light foam',
    price: 4.75,
    category: 'coffee',
    image: 'https://images.unsplash.com/photo-1541167760496-1628856ab772?w=400&h=300&fit=crop',
    available: true
  },
  {
    id: 4,
    name: 'Cold Brew',
    description: 'Steeped 12 hours for smooth, low-acid flavor',
    price: 4.25,
    category: 'coffee',
    image: 'https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?w=400&h=300&fit=crop',
    available: true
  },
  {
    id: 5,
    name: 'Mocha',
    description: 'Espresso with chocolate syrup and steamed milk',
    price: 5.25,
    category: 'coffee',
    image: 'https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=400&h=300&fit=crop',
    available: true
  },
  {
    id: 6,
    name: 'Croissant',
    description: 'Buttery, flaky French pastry baked fresh daily',
    price: 3.75,
    category: 'pastry',
    image: 'https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400&h=300&fit=crop',
    available: true
  },
  {
    id: 7,
    name: 'Blueberry Muffin',
    description: 'Moist muffin bursting with fresh blueberries',
    price: 3.50,
    category: 'pastry',
    image: 'https://images.unsplash.com/photo-1607958996333-41aef7caefaa?w=400&h=300&fit=crop',
    available: true
  },
  {
    id: 8,
    name: 'Cinnamon Roll',
    description: 'Warm, gooey roll with cream cheese frosting',
    price: 4.00,
    category: 'pastry',
    image: 'https://images.unsplash.com/photo-1509365465985-25d11c17e812?w=400&h=300&fit=crop',
    available: true
  },
  {
    id: 9,
    name: 'Avocado Toast',
    description: 'Sourdough with smashed avocado, chili flakes, and lemon',
    price: 8.50,
    category: 'food',
    image: 'https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=400&h=300&fit=crop',
    available: true
  },
  {
    id: 10,
    name: 'Breakfast Sandwich',
    description: 'Egg, cheddar, and bacon on a brioche bun',
    price: 7.75,
    category: 'food',
    image: 'https://images.unsplash.com/photo-1550507992-eb63ffee0847?w=400&h=300&fit=crop',
    available: true
  },
  {
    id: 11,
    name: 'Greek Yogurt Parfait',
    description: 'Honey Greek yogurt, granola, and seasonal berries',
    price: 6.50,
    category: 'food',
    image: 'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&h=300&fit=crop',
    available: true
  },
  {
    id: 12,
    name: 'Matcha Latte',
    description: 'Ceremonial grade matcha with steamed oat milk',
    price: 5.50,
    category: 'coffee',
    image: 'https://images.unsplash.com/photo-1515823064-d6e0c04616a7?w=400&h=300&fit=crop',
    available: true
  }
];

let orders = [];
let orderIdCounter = 1;

// Routes
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Get all menu items
app.get('/api/menu', (req, res) => {
  const { category, available } = req.query;
  let filtered = [...menuItems];
  
  if (category) {
    filtered = filtered.filter(item => item.category === category);
  }
  if (available !== undefined) {
    filtered = filtered.filter(item => item.available === (available === 'true'));
  }
  
  res.json(filtered);
});

// Get menu item by ID
app.get('/api/menu/:id', (req, res) => {
  const item = menuItems.find(m => m.id === parseInt(req.params.id));
  if (!item) {
    return res.status(404).json({ error: 'Menu item not found' });
  }
  res.json(item);
});

// Create new order
app.post('/api/orders', [
  // Validation would go here with express-validator
], (req, res) => {
  const { items, customerName, customerEmail, customerPhone, notes } = req.body;
  
  if (!items || !Array.isArray(items) || items.length === 0) {
    return res.status(400).json({ error: 'Order must contain at least one item' });
  }
  
  // Validate items exist and calculate total
  let total = 0;
  const orderItems = [];
  
  for (const item of items) {
    const menuItem = menuItems.find(m => m.id === item.id);
    if (!menuItem) {
      return res.status(400).json({ error: `Menu item with id ${item.id} not found` });
    }
    if (!menuItem.available) {
      return res.status(400).json({ error: `${menuItem.name} is currently unavailable` });
    }
    const quantity = item.quantity || 1;
    total += menuItem.price * quantity;
    orderItems.push({
      menuItemId: menuItem.id,
      name: menuItem.name,
      price: menuItem.price,
      quantity
    });
  }
  
  const order = {
    id: orderIdCounter++,
    items: orderItems,
    total: parseFloat(total.toFixed(2)),
    customerName: customerName || 'Guest',
    customerEmail: customerEmail || '',
    customerPhone: customerPhone || '',
    notes: notes || '',
    status: 'pending',
    createdAt: new Date().toISOString()
  };
  
  orders.push(order);
  res.status(201).json(order);
});

// Get all orders (admin)
app.get('/api/orders', (req, res) => {
  res.json(orders);
});

// Get order by ID
app.get('/api/orders/:id', (req, res) => {
  const order = orders.find(o => o.id === parseInt(req.params.id));
  if (!order) {
    return res.status(404).json({ error: 'Order not found' });
  }
  res.json(order);
});

// Update order status (admin)
app.patch('/api/orders/:id/status', (req, res) => {
  const { status } = req.body;
  const validStatuses = ['pending', 'preparing', 'ready', 'completed', 'cancelled'];
  
  if (!validStatuses.includes(status)) {
    return res.status(400).json({ error: 'Invalid status' });
  }
  
  const order = orders.find(o => o.id === parseInt(req.params.id));
  if (!order) {
    return res.status(404).json({ error: 'Order not found' });
  }
  
  order.status = status;
  order.updatedAt = new Date().toISOString();
  res.json(order);
});

// Serve the built React client alongside the API (same origin)
if (fs.existsSync(clientDist)) {
  app.use(express.static(clientDist));
  app.get(/^(?!\/api).*/, (req, res) => {
    res.sendFile(path.join(clientDist, 'index.html'));
  });
}

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
