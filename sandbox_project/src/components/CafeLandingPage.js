import React from 'react';

const CafeLandingPage = () => {
  return (
    <div className="hero">
      <h1>Welcome to Our Modern Neighborhood Cafe</h1>
      <p>Enjoy delicious food and drinks in a cozy atmosphere.</p>
    </div>
    <div className="menu-highlights">
      <h2>Menu Highlights</h2>
      <ul>
        <li>Coffee</li>
        <li>Tea</li>
        <li>Sandwiches</li>
      </ul>
    </div>
    <div className="opening-hours">
      <h2>Opening Hours</h2>
      <p>Monday to Friday: 8 AM - 6 PM</p>
      <p>Saturday and Sunday: 10 AM - 4 PM</p>
    </div>
    <div className="location">
      <h2>Location</h2>
      <p>123 Main St, Neighborhood, City</p>
    </div>
    <div className="contact-cta">
      <h2>Contact Us</h2>
      <p>Email: info@neighborhoodcafe.com</p>
      <p>Phone: (555) 123-4567</p>
    </div>
  );
};

export default CafeLandingPage;