import React, { useMemo } from "react";
import { useCurrentFrame, useVideoConfig, interpolate, random } from "remotion";

/**
 * Animierter Partikel-Hintergrund.
 * Fuer professionelle Intros und Uebergaenge.
 */

interface Particle {
  x: number;
  y: number;
  size: number;
  speed: number;
  opacity: number;
  angle: number;
}

interface ParticleBackgroundProps {
  count?: number;
  color?: string;
  maxSize?: number;
  speed?: number;
  connected?: boolean;
  connectionDistance?: number;
}

export const ParticleBackground: React.FC<ParticleBackgroundProps> = ({
  count = 50,
  color = "#6366f1",
  maxSize = 4,
  speed = 1,
  connected = true,
  connectionDistance = 150,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const particles = useMemo<Particle[]>(() => {
    return Array.from({ length: count }).map((_, i) => ({
      x: random(`particle-x-${i}`) * width,
      y: random(`particle-y-${i}`) * height,
      size: random(`particle-size-${i}`) * maxSize + 1,
      speed: (random(`particle-speed-${i}`) * 0.5 + 0.5) * speed,
      opacity: random(`particle-opacity-${i}`) * 0.5 + 0.3,
      angle: random(`particle-angle-${i}`) * Math.PI * 2,
    }));
  }, [count, width, height, maxSize, speed]);

  const getPosition = (p: Particle) => {
    const x = (p.x + Math.cos(p.angle) * frame * p.speed) % width;
    const y = (p.y + Math.sin(p.angle) * frame * p.speed) % height;
    return {
      x: x < 0 ? x + width : x,
      y: y < 0 ? y + height : y,
    };
  };

  const positions = particles.map(getPosition);

  return (
    <svg width={width} height={height} style={{ position: "absolute", top: 0, left: 0 }}>
      {/* Verbindungslinien */}
      {connected &&
        positions.map((pos1, i) =>
          positions.slice(i + 1).map((pos2, j) => {
            const dx = pos1.x - pos2.x;
            const dy = pos1.y - pos2.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist > connectionDistance) return null;
            const lineOpacity = interpolate(
              dist,
              [0, connectionDistance],
              [0.3, 0],
              { extrapolateRight: "clamp" }
            );
            return (
              <line
                key={`${i}-${j}`}
                x1={pos1.x}
                y1={pos1.y}
                x2={pos2.x}
                y2={pos2.y}
                stroke={color}
                strokeWidth={1}
                opacity={lineOpacity}
              />
            );
          })
        )}

      {/* Partikel */}
      {positions.map((pos, i) => (
        <circle
          key={i}
          cx={pos.x}
          cy={pos.y}
          r={particles[i].size}
          fill={color}
          opacity={particles[i].opacity}
        />
      ))}
    </svg>
  );
};
