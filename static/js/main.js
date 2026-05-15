/**
 * SecureVote – Main JavaScript
 * General UI helpers (no sensitive logic here)
 */

// Auto-dismiss flash alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // Activate Bootstrap tooltips
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));

  // Activate Bootstrap popovers
  const popoverEls = document.querySelectorAll('[data-bs-toggle="popover"]');
  popoverEls.forEach(el => new bootstrap.Popover(el));
  
  // Smooth reveal on scroll
  const revealEls = document.querySelectorAll('.section, .feature-card, .security-card, .hero-card');
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('in-view');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12 });
  revealEls.forEach(el => io.observe(el));

  // Micro-interactions: card hover subtle scale
  document.querySelectorAll('.feature-card, .hero-card').forEach(card => {
    card.addEventListener('mouseenter', () => card.classList.add('hovering'));
    card.addEventListener('mouseleave', () => card.classList.remove('hovering'));
  });

  // Image fallback handler for candidate thumbnails
  document.querySelectorAll('img[data-default-src]').forEach(img => {
    const fallback = img.getAttribute('data-default-src');
    const setFallback = () => {
      if (!fallback) return;
      try {
        if (img.src !== fallback) img.src = fallback;
      } catch (e) { img.src = fallback; }
    };

    // If src is empty or just the uploads folder (no filename), use fallback
    try {
      const src = img.getAttribute('src') || '';
      if (!src || /uploads\/(?:$|\s*$)/.test(src)) setFallback();
    } catch (e) { setFallback(); }

    // On error, replace with fallback
    img.addEventListener('error', function () {
      setFallback();
    });

    // If image loads but has zero natural size, treat as failed
    img.addEventListener('load', function () {
      if (img.naturalWidth === 0 || img.naturalHeight === 0) setFallback();
    });

    // If already completed (from cache), validate immediately
    if (img.complete) {
      if (img.naturalWidth === 0 || img.naturalHeight === 0) setFallback();
    }
  });
});

/* -------------------- Particle background -------------------- */
(() => {
  const canvasWrap = document.getElementById('bg-canvas');
  if (!canvasWrap) return;
  const canvas = document.createElement('canvas');
  canvas.style.position = 'fixed';
  canvas.style.inset = '0';
  canvas.style.zIndex = '0';
  canvas.style.pointerEvents = 'none';
  canvas.style.opacity = '0.18';
  canvas.style.mixBlendMode = 'multiply';
  canvasWrap.appendChild(canvas);
  const ctx = canvas.getContext('2d');

  let w = canvas.width = innerWidth;
  let h = canvas.height = innerHeight;
  window.addEventListener('resize', () => { w = canvas.width = innerWidth; h = canvas.height = innerHeight; });

  const particles = [];
  const count = Math.max(18, Math.floor((w * h) / 160000)); // fewer for subtlety
  for (let i=0; i<count; i++) {
    particles.push({
      x: Math.random()*w,
      y: Math.random()*h,
      r: 0.8 + Math.random()*2.2,
      vx: (Math.random()-0.5) * 0.18,
      vy: (Math.random()-0.5) * 0.18,
      alpha: 0.06 + Math.random()*0.12
    });
  }

  function draw() {
    ctx.clearRect(0,0,w,h);
  // very light wash for depth
  const grad = ctx.createLinearGradient(0,0,w,h);
  grad.addColorStop(0, 'rgba(255,255,255,0)');
  grad.addColorStop(1, 'rgba(245,247,241,0.12)');
  ctx.fillStyle = grad; ctx.fillRect(0,0,w,h);

    for (const p of particles) {
      p.x += p.vx; p.y += p.vy;
      if (p.x < -10) p.x = w + 10; if (p.x > w+10) p.x = -10;
      if (p.y < -10) p.y = h + 10; if (p.y > h+10) p.y = -10;
      ctx.beginPath();
  // soft warm-green particles
  ctx.fillStyle = `rgba(195,204,155,${p.alpha})`;
      ctx.arc(p.x, p.y, p.r, 0, Math.PI*2);
      ctx.fill();
    }
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();

/* -------------------- Utility: smooth section scroll for anchor buttons -------------------- */
document.addEventListener('click', (e) => {
  const a = e.target.closest('a[href^="#"]');
  if (!a) return;
  const target = document.querySelector(a.getAttribute('href'));
  if (target) {
    e.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
});
