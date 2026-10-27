import React, { useEffect, useRef } from 'react';

export function BackgroundCanvas({ theme = 'dark' }) {
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Mouse parallax tracking
    let mouseX = width / 2;
    let mouseY = height / 2;
    let targetMouseX = mouseX;
    let targetMouseY = mouseY;

    const handleMouseMove = (e) => {
      targetMouseX = e.clientX;
      targetMouseY = e.clientY;
    };

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('resize', handleResize, { passive: true });

    // 3 parallax layers: Layer 0 (far/dim), Layer 1 (mid), Layer 2 (near/bright)
    const particleCount = width < 768 ? 40 : 80;
    const particles = [];

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        radius: Math.random() * 1.6 + 0.6,
        layer: i % 3, // 0, 1, or 2
        speedX: (Math.random() - 0.5) * 0.15,
        speedY: (Math.random() - 0.5) * 0.15,
        baseAlpha: Math.random() * 0.5 + 0.25,
        pulseSpeed: Math.random() * 0.02 + 0.005,
        pulseOffset: Math.random() * Math.PI * 2
      });
    }

    let isVisible = !document.hidden;
    const handleVisibility = () => {
      isVisible = !document.hidden;
      if (isVisible) loop();
    };
    document.addEventListener('visibilitychange', handleVisibility);

    let time = 0;

    const loop = () => {
      if (!isVisible) return;

      time += 0.016;

      // Smooth mouse easing
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      ctx.clearRect(0, 0, width, height);

      const isDark = theme === 'dark';
      const starColor = isDark ? [201, 162, 75] : [148, 113, 36]; // Antique gold
      const dustColor = isDark ? [150, 175, 195] : [100, 120, 140];

      // Draw faint constellation linkages in dark mode
      if (isDark) {
        ctx.lineWidth = 0.5;
        for (let i = 0; i < particles.length; i++) {
          for (let j = i + 1; j < particles.length; j++) {
            const p1 = particles[i];
            const p2 = particles[j];
            if (p1.layer === p2.layer && p1.layer > 0) {
              const dx = p1.x - p2.x;
              const dy = p1.y - p2.y;
              const dist = Math.sqrt(dx * dx + dy * dy);
              if (dist < 110) {
                const linkAlpha = (1 - dist / 110) * 0.08;
                ctx.strokeStyle = `rgba(${starColor[0]}, ${starColor[1]}, ${starColor[2]}, ${linkAlpha})`;
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
              }
            }
          }
        }
      }

      // Render particles with depth parallax
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        if (!isReducedMotion) {
          p.x += p.speedX;
          p.y += p.speedY;

          // Screen wrap
          if (p.x < 0) p.x = width;
          if (p.x > width) p.x = 0;
          if (p.y < 0) p.y = height;
          if (p.y > height) p.y = 0;
        }

        // Parallax offset per layer
        const parallaxFactor = (p.layer + 1) * 0.015;
        const offsetX = (mouseX - width / 2) * parallaxFactor;
        const offsetY = (mouseY - height / 2) * parallaxFactor;

        const drawX = p.x + offsetX;
        const drawY = p.y + offsetY;

        // Twinkle pulse
        const twinkle = Math.sin(time * p.pulseSpeed * 60 + p.pulseOffset) * 0.25;
        const alpha = Math.max(0.1, Math.min(0.9, p.baseAlpha + twinkle));

        const col = p.layer === 2 ? starColor : dustColor;

        ctx.beginPath();
        ctx.arc(drawX, drawY, p.radius * (0.8 + (p.layer * 0.2)), 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${col[0]}, ${col[1]}, ${col[2]}, ${alpha * (isDark ? 0.8 : 0.6)})`;
        ctx.fill();

        // Subtle halo around brighter stars
        if (p.layer === 2 && isDark) {
          ctx.beginPath();
          ctx.arc(drawX, drawY, p.radius * 2.8, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${starColor[0]}, ${starColor[1]}, ${starColor[2]}, ${alpha * 0.15})`;
          ctx.fill();
        }
      }

      animFrameRef.current = requestAnimationFrame(loop);
    };

    loop();

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('visibilitychange', handleVisibility);
    };
  }, [theme]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 0,
        opacity: 0.95
      }}
      aria-hidden="true"
    />
  );
}
