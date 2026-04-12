import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

/**
 * Animierter Gradient-Hintergrund mit sanfter Farbbewegung.
 */

interface GradientBackgroundProps {
  colors?: string[];
  speed?: number;
  type?: "linear" | "radial" | "conic";
}

export const GradientBackground: React.FC<GradientBackgroundProps> = ({
  colors = ["#0f172a", "#1e1b4b", "#312e81", "#1e1b4b", "#0f172a"],
  speed = 0.5,
  type = "linear",
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const angle = frame * speed;
  const colorString = colors.join(", ");

  const gradients: Record<string, string> = {
    linear: `linear-gradient(${angle}deg, ${colorString})`,
    radial: `radial-gradient(ellipse at ${50 + Math.sin(frame * 0.02) * 30}% ${50 + Math.cos(frame * 0.015) * 30}%, ${colorString})`,
    conic: `conic-gradient(from ${angle}deg at 50% 50%, ${colorString})`,
  };

  return (
    <div
      style={{
        width,
        height,
        background: gradients[type],
        position: "absolute",
        top: 0,
        left: 0,
      }}
    />
  );
};
