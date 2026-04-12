import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { z } from "zod";
import { splitScreenSchema } from "../schemas.js";

export const SplitScreenComposition: React.FC<
  z.infer<typeof splitScreenSchema>
> = ({ splitRatio, direction }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 80 },
  });

  const splitPosition = interpolate(progress, [0, 1], [0, splitRatio * 100]);
  const isHorizontal = direction === "horizontal";

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f172a" }}>
      {/* Linke/Obere Seite */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: isHorizontal ? `${splitPosition}%` : "100%",
          height: isHorizontal ? "100%" : `${splitPosition}%`,
          background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
          overflow: "hidden",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <div
          style={{
            fontSize: 48,
            fontWeight: 700,
            color: "#ffffff",
            fontFamily: "Inter, system-ui, sans-serif",
            opacity: interpolate(progress, [0.3, 0.7], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          Vorher
        </div>
      </div>

      {/* Rechte/Untere Seite */}
      <div
        style={{
          position: "absolute",
          top: isHorizontal ? 0 : `${splitPosition}%`,
          left: isHorizontal ? `${splitPosition}%` : 0,
          width: isHorizontal ? `${100 - splitPosition}%` : "100%",
          height: isHorizontal ? "100%" : `${100 - splitPosition}%`,
          background: "linear-gradient(135deg, #f59e0b, #ef4444)",
          overflow: "hidden",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <div
          style={{
            fontSize: 48,
            fontWeight: 700,
            color: "#ffffff",
            fontFamily: "Inter, system-ui, sans-serif",
            opacity: interpolate(progress, [0.5, 0.9], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          Nachher
        </div>
      </div>

      {/* Split-Linie */}
      <div
        style={{
          position: "absolute",
          top: isHorizontal ? 0 : `${splitPosition}%`,
          left: isHorizontal ? `${splitPosition}%` : 0,
          width: isHorizontal ? 4 : "100%",
          height: isHorizontal ? "100%" : 4,
          backgroundColor: "#ffffff",
          boxShadow: "0 0 20px rgba(255,255,255,0.5)",
          transform: isHorizontal ? "translateX(-2px)" : "translateY(-2px)",
        }}
      />
    </AbsoluteFill>
  );
};
