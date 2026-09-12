import { html } from "lit";

const particles = [
  { x: 5, y: 66, size: 2, duration: 7.8, delay: -1.2, drift: 48, opacity: 0.62 },
  { x: 13, y: 30, size: 1.5, duration: 9.3, delay: -4.5, drift: 62, opacity: 0.48 },
  { x: 21, y: 62, size: 2.6, duration: 6.9, delay: -2.7, drift: 44, opacity: 0.7 },
  { x: 29, y: 22, size: 1.8, duration: 8.7, delay: -6.3, drift: 56, opacity: 0.5 },
  { x: 37, y: 72, size: 1.4, duration: 10.2, delay: -3.9, drift: 70, opacity: 0.4 },
  { x: 45, y: 42, size: 2.3, duration: 7.4, delay: -5.1, drift: 50, opacity: 0.64 },
  { x: 54, y: 18, size: 1.6, duration: 9.8, delay: -1.7, drift: 64, opacity: 0.48 },
  { x: 63, y: 67, size: 2.1, duration: 8.1, delay: -7.2, drift: 58, opacity: 0.56 },
  { x: 72, y: 35, size: 1.3, duration: 10.8, delay: -4.1, drift: 74, opacity: 0.4 },
  { x: 80, y: 70, size: 2.5, duration: 7.1, delay: -2.2, drift: 46, opacity: 0.68 },
  { x: 88, y: 26, size: 1.7, duration: 9.1, delay: -5.8, drift: 60, opacity: 0.48 },
  { x: 94, y: 58, size: 2.2, duration: 8.4, delay: -3.3, drift: 54, opacity: 0.58 },
] as const;

const sparkles = [
  { x: 24, y: -9, size: 2.1, duration: 4.8, delay: -1.4 },
  { x: 49, y: -14, size: 1.6, duration: 5.4, delay: -3.2 },
  { x: 73, y: -8, size: 2.4, duration: 4.4, delay: -2.1 },
  { x: 91, y: -12, size: 1.8, duration: 5.8, delay: -4.7 },
] as const;

export function renderParticles() {
  return particles.map(
    (particle) => html`
      <span
        class="particle"
        style="--x:${particle.x}%;--y:${particle.y}%;--size:${particle.size}px;--duration:${particle.duration}s;--delay:${particle.delay}s;--drift:${particle.drift}px;--opacity:${particle.opacity}"
      ></span>
    `,
  );
}

export function renderSparkles() {
  return sparkles.map(
    (sparkle) => html`
      <span
        class="sparkle"
        style="--x:${sparkle.x}%;--y:${sparkle.y}px;--size:${sparkle.size}px;--duration:${sparkle.duration}s;--delay:${sparkle.delay}s"
      ></span>
    `,
  );
}
