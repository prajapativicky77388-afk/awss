"use client";

import { useMemo } from "react";

interface RainEffectProps {
  intensity: number; // 0-100+ mm/hr
  active: boolean;
}

export default function RainEffect({ intensity, active }: RainEffectProps) {
  const drops = useMemo(() => {
    if (!active || intensity <= 0) return [];
    const count = Math.min(80, Math.floor(intensity * 0.8));
    return Array.from({ length: count }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      height: 15 + Math.random() * 25,
      duration: 0.4 + Math.random() * 0.6,
      delay: Math.random() * 2,
      opacity: 0.3 + Math.random() * 0.5,
    }));
  }, [intensity, active]);

  if (!active || intensity <= 0) return null;

  return (
    <div className="rain-overlay">
      {drops.map((drop) => (
        <div
          key={drop.id}
          className="raindrop"
          style={{
            left: `${drop.left}%`,
            height: `${drop.height}px`,
            animationDuration: `${drop.duration}s`,
            animationDelay: `${drop.delay}s`,
            opacity: drop.opacity,
          }}
        />
      ))}
    </div>
  );
}
