# 🛹 RadRide Skateboards

A full-stack **React + Node.js** promotional website for a skateboard business.  
Colorful, dynamic, and built to 10x your business presence.

## 🚀 Features

### Frontend (React)
- **Animated Particle Canvas** – Interactive glowing particles that react to mouse/touch
- **Gradient Text Animations** – Animated shifting gradients on headings
- **Floating Skateboard Icon** – Playful CSS animation in the hero
- **Product Showcase** – 4 decks with hover glow effects and buy buttons
- **Features Grid** – Highlights quality, custom art, shipping, warranty
- **Testimonials** – Star ratings and customer reviews
- **Newsletter Signup** – Email subscription form with API integration
- **Scroll Reveal Animations** – Elements fade and slide up as you scroll
- **Responsive Design** – Works on desktop, tablet, and mobile
- **Hamburger Menu** – Mobile-friendly navigation
- **Order Toast Notifications** – Animated feedback when buying
- **Loading Screen** – Animated skateboard while data loads

### Backend (Node.js + Express)
- **REST API** – `/api/products`, `/api/features`, `/api/testimonials`
- **Newsletter Subscription** – `POST /api/subscribe` with validation
- **Order Simulation** – `POST /api/orders` with product lookup
- **Health Check** – `GET /api/health`
- **CORS enabled** – Works with the React dev server
- **Serves React build** in production mode

## 📁 Project Structure

```
skateboard-business/
├── client/                  # React frontend
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── components/
│       │   ├── Navbar.js / .css
│       │   ├── Hero.js / .css
│       │   ├── Products.js / .css
│       │   ├── Features.js / .css
│       │   ├── Testimonials.js / .css
│       │   ├── Newsletter.js / .css
│       │   ├── Footer.js / .css
│       │   └── ParticleCanvas.js
│       ├── App.js / App.css
│       ├── index.js
│       └── index.css
│       └── package.json
├── server/                  # Node.js backend
│   ├── index.js
│   └── package.json
├── package.json             # Root scripts (concurrently)
└── README.md
```

## 🛠️ Setup & Running

### Prerequisites
- Node.js 18+ and npm

### Install Dependencies
```bash
cd skateboard-business
npm install              # root (concurrently)
npm run install:all      # server + client
```

### Development Mode (run both servers)
```bash
npm start
```
This starts:
- **API server** on `http://localhost:5000`
- **React dev server** on `http://localhost:3000` (proxied to API)

### Production Build
```bash
npm run build
NODE_ENV=production npm run start:server
```
The server will serve the built React app from `client/build/`.

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List all products |
| GET | `/api/products/:id` | Get single product |
| GET | `/api/features` | List features |
| GET | `/api/testimonials` | List testimonials |
| POST | `/api/subscribe` | Subscribe email |
| POST | `/api/orders` | Place an order |
| GET | `/api/health` | Health check |

## 🎨 Color Palette

| Color | Usage |
|-------|-------|
| `#0b0b1a` / `#1a1a2e` | Dark backgrounds |
| `#f7971e` / `#ffd200` | Gold/Orange accents |
| `#ff3c3c` / `#ff6b6b` | Red accents, buttons |
| `#a855f7` | Purple accent (particles) |

## 🔤 Fonts

- **Bangers** – headings (fun, energetic)
- **Montserrat** – body text (clean, modern)

---

Built with ❤️ + React ⚛️ + Node.js 🟢 for shredding! 🛹🔥