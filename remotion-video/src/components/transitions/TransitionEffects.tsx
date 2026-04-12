import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from "remotion";

/**
 * Professionelle Uebergangseffekte.
 * Inspiriert von designcombo/react-video-editor und @remotion/transitions.
 */

// --- Wipe Transition ---
interface WipeProps {
  direction?: "left" | "right" | "up" | "down";
  children: React.ReactNode;
}

export const WipeIn: React.FC<WipeProps> = ({
  direction = "left",
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame, fps, config: { damping: 20, stiffness: 80 } });

  const clipPaths: Record<string, string> = {
    left: `inset(0 ${100 - progress * 100}% 0 0)`,
    right: `inset(0 0 0 ${100 - progress * 100}%)`,
    up: `inset(0 0 ${100 - progress * 100}% 0)`,
    down: `inset(${100 - progress * 100}% 0 0 0)`,
  };

  return (
    <div style={{ clipPath: clipPaths[direction], width: "100%", height: "100%" }}>
      {children}
    </div>
  );
};

// --- Zoom Transition ---
interface ZoomTransitionProps {
  children: React.ReactNode;
  startScale?: number;
}

export const ZoomIn: React.FC<ZoomTransitionProps> = ({
  children,
  startScale = 0.3,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({
    frame,
    fps,
    config: { damping: 10, mass: 0.6, stiffness: 100 },
  });

  const scale = interpolate(progress, [0, 1], [startScale, 1]);
  const opacity = interpolate(progress, [0, 0.3], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        transform: `scale(${scale})`,
        opacity,
        width: "100%",
        height: "100%",
      }}
    >
      {children}
    </div>
  );
};

// --- Crossfade ---
interface CrossfadeProps {
  durationInFrames: number;
  children: [React.ReactNode, React.ReactNode];
}

export const Crossfade: React.FC<CrossfadeProps> = ({
  durationInFrames,
  children,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <div style={{ position: "absolute", inset: 0, opacity: 1 - opacity }}>
        {children[0]}
      </div>
      <div style={{ position: "absolute", inset: 0, opacity }}>
        {children[1]}
      </div>
    </div>
  );
};

// --- Circle Reveal ---
interface CircleRevealProps {
  children: React.ReactNode;
  originX?: number;
  originY?: number;
}

export const CircleReveal: React.FC<CircleRevealProps> = ({
  children,
  originX = 50,
  originY = 50,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame, fps, config: { damping: 15, stiffness: 60 } });
  const radius = progress * 150;

  return (
    <div
      style={{
        clipPath: `circle(${radius}% at ${originX}% ${originY}%)`,
        width: "100%",
        height: "100%",
      }}
    >
      {children}
    </div>
  );
};

// --- Glitch Transition ---
interface GlitchTransitionProps {
  children: React.ReactNode;
  intensity?: number;
}

export const GlitchTransition: React.FC<GlitchTransitionProps> = ({
  children,
  intensity = 1,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame, fps, config: { damping: 25, stiffness: 200 } });

  const sliceCount = 8;
  const glitchAmount = (1 - progress) * 30 * intensity;

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", overflow: "hidden" }}>
      {Array.from({ length: sliceCount }).map((_, i) => {
        const sliceHeight = 100 / sliceCount;
        const offset =
          Math.sin(frame * 0.5 + i * 2.1) * glitchAmount *
          (i % 2 === 0 ? 1 : -1);

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              top: `${i * sliceHeight}%`,
              left: 0,
              width: "100%",
              height: `${sliceHeight + 0.5}%`,
              overflow: "hidden",
              transform: `translateX(${offset}px)`,
            }}
          >
            <div
              style={{
                position: "absolute",
                top: `-${i * sliceHeight}%`,
                left: 0,
                width: "100%",
                height: `${sliceCount * 100}%`,
                transformOrigin: "top left",
                transform: `scaleY(${1 / sliceCount})`,
              }}
            >
              <div style={{ width: "100%", height: "100%", transform: `scaleY(${sliceCount})` }}>
                {children}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
