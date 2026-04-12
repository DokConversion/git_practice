import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";

/**
 * Ken Burns Effekt - Professionelles Panning und Zooming fuer Bilder/Videos.
 * Standard-Technik bei Dokumentationen und professionellen Videos.
 */

interface KenBurnsProps {
  children: React.ReactNode;
  zoomStart?: number;
  zoomEnd?: number;
  panDirection?: "left" | "right" | "up" | "down" | "center";
  panAmount?: number;
}

export const KenBurns: React.FC<KenBurnsProps> = ({
  children,
  zoomStart = 1,
  zoomEnd = 1.2,
  panDirection = "left",
  panAmount = 10,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.quad),
  });

  const scale = interpolate(progress, [0, 1], [zoomStart, zoomEnd]);

  const panOffsets: Record<string, { x: number; y: number }> = {
    left: { x: -panAmount * progress, y: 0 },
    right: { x: panAmount * progress, y: 0 },
    up: { x: 0, y: -panAmount * progress },
    down: { x: 0, y: panAmount * progress },
    center: { x: 0, y: 0 },
  };

  const { x, y } = panOffsets[panDirection];

  return (
    <div style={{ width: "100%", height: "100%", overflow: "hidden" }}>
      <div
        style={{
          width: "100%",
          height: "100%",
          transform: `scale(${scale}) translate(${x}%, ${y}%)`,
          transformOrigin: "center center",
        }}
      >
        {children}
      </div>
    </div>
  );
};
