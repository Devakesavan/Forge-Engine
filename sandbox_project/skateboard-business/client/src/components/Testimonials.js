import React, { useEffect, useRef } from 'react';
import './Testimonials.css';

export default function Testimonials({ testimonials }) {
  const sectionRef = useRef(null);

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

  const renderStars = (count) => '★'.repeat(count);

  return (
    <section className="testimonials" id="testimonials" ref={sectionRef}>
      <h2 className="section-title">💬 Rave Reviews</h2>
      <div className="testi-grid">
        {testimonials.map((t) => (
          <div className="testi-card reveal" key={t.id}>
            <div className="stars">{renderStars(t.stars)}</div>
            <p>"{t.text}"</p>
            <div className="author">– {t.author}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
