import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";

/**
 * Professionelle Lower Third Overlays.
 * Inspiriert von designcombo/react-video-editor und broadcast-design Patterns.
 */

interface LowerThirdProps {
  title: string;
  subtitle?: string;
  accentColor?: string;
  backgroundColor?: string;
  textColor?: string;
  position?: "left" | "center" | "right";
  variant?: "modern" | "minimal" | "broadcast";
}

export const LowerThird: React.FC<LowerThirdProps> = ({
  title,
  subtitle,
  accentColor = "#6366f1",
  backgroundColor = "rgba(0, 0, 0, 0.85)",
  textColor = "#ffffff",
  position = "left",
  variant = "modern",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const slideProgress = spring({
    frame,
    fps,
    config: { damping: 15, mass: 0.8, stiffness: 100 },
  });

  const barProgress = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: { damping: 20, stiffness: 120 },
  });

  const textOpacity = interpolate(frame, [8, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const positionStyles: Record<string, React.CSSProperties> = {
    left: { left: 80, right: "auto" },
    center: { left: "50%", transform: `translateX(-50%) translateY(${interpolate(slideProgress, [0, 1], [40, 0])}px)` },
    right: { right: 80, left: "auto" },
  };

  if (variant === "minimal") {
    return (
      <div
        style={{
          position: "absolute",
          bottom: 100,
          ...positionStyles[position],
          display: "flex",
          alignItems: "center",
          gap: 16,
          opacity: slideProgress,
          transform: position !== "center"
            ? `translateX(${interpolate(slideProgress, [0, 1], [-30, 0])}px)`
            : positionStyles[position].transform,
        }}
      >
        <div
          style={{
            width: 4,
            height: 50 * barProgress,
            backgroundColor: accentColor,
            borderRadius: 2,
          }}
        />
        <div>
          <div
            style={{
              fontSize: 32,
              fontWeight: 700,
              color: textColor,
              fontFamily: "Inter, system-ui, sans-serif",
              opacity: textOpacity,
            }}
          >
            {title}
          </div>
          {subtitle && (
            <div
              style={{
                fontSize: 20,
                fontWeight: 400,
                color: `${textColor}bb`,
                fontFamily: "Inter, system-ui, sans-serif",
                opacity: textOpacity,
                marginTop: 4,
              }}
            >
              {subtitle}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (variant === "broadcast") {
    return (
      <div
        style={{
          position: "absolute",
          bottom: 80,
          left: 60,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Accent bar */}
        <div
          style={{
            width: 400 * barProgress,
            height: 4,
            backgroundColor: accentColor,
            marginBottom: 0,
          }}
        />
        {/* Title bar */}
        <div
          style={{
            backgroundColor: accentColor,
            padding: "12px 24px",
            transform: `translateX(${interpolate(slideProgress, [0, 1], [-100, 0])}%)`,
          }}
        >
          <span
            style={{
              fontSize: 28,
              fontWeight: 700,
              color: "#ffffff",
              fontFamily: "Inter, system-ui, sans-serif",
              opacity: textOpacity,
            }}
          >
            {title}
          </span>
        </div>
        {/* Subtitle bar */}
        {subtitle && (
          <div
            style={{
              backgroundColor,
              padding: "8px 24px",
              transform: `translateX(${interpolate(slideProgress, [0, 1], [-100, 0])}%)`,
            }}
          >
            <span
              style={{
                fontSize: 20,
                fontWeight: 400,
                color: textColor,
                fontFamily: "Inter, system-ui, sans-serif",
                opacity: textOpacity,
              }}
            >
              {subtitle}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Modern (default)
  return (
    <div
      style={{
        position: "absolute",
        bottom: 80,
        ...positionStyles[position],
        backgroundColor,
        backdropFilter: "blur(20px)",
        borderRadius: 12,
        padding: "20px 32px",
        borderLeft: `4px solid ${accentColor}`,
        transform: position !== "center"
          ? `translateX(${interpolate(slideProgress, [0, 1], [-40, 0])}px)`
          : positionStyles[position].transform,
        opacity: slideProgress,
      }}
    >
      <div
        style={{
          fontSize: 30,
          fontWeight: 700,
          color: textColor,
          fontFamily: "Inter, system-ui, sans-serif",
          opacity: textOpacity,
        }}
      >
        {title}
      </div>
      {subtitle && (
        <div
          style={{
            fontSize: 18,
            fontWeight: 400,
            color: `${textColor}99`,
            fontFamily: "Inter, system-ui, sans-serif",
            opacity: textOpacity,
            marginTop: 6,
          }}
        >
          {subtitle}
        </div>
      )}
    </div>
  );
};
