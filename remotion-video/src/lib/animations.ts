import { interpolate, spring, Easing } from "remotion";

/**
 * Professionelle Animations-Utilities.
 * Inspiriert von: remotion-dev/template, florentpergoud/remotion-audiogram,
 * marcusstenbeck/remotion-template, JonnyBurger/remotion-trailer
 */

// --- Spring Presets ---

export const SPRING_PRESETS = {
  smooth: { damping: 12, mass: 0.5, stiffness: 80 },
  bouncy: { damping: 8, mass: 0.8, stiffness: 200 },
  snappy: { damping: 20, mass: 0.4, stiffness: 300 },
  gentle: { damping: 15, mass: 1, stiffness: 60 },
  elastic: { damping: 5, mass: 0.6, stiffness: 150 },
} as const;

export type SpringPreset = keyof typeof SPRING_PRESETS;

// --- Fade Animations ---

export function fadeIn(
  frame: number,
  fps: number,
  delay: number = 0,
  duration: number = 20
) {
  return interpolate(frame, [delay, delay + duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
}

export function fadeOut(
  frame: number,
  fps: number,
  startFrame: number,
  duration: number = 20
) {
  return interpolate(frame, [startFrame, startFrame + duration], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.in(Easing.cubic),
  });
}

// --- Slide Animations ---

export type SlideDirection = "left" | "right" | "up" | "down";

export function slideIn(
  frame: number,
  fps: number,
  direction: SlideDirection = "left",
  preset: SpringPreset = "smooth"
) {
  const springConfig = SPRING_PRESETS[preset];
  const progress = spring({ frame, fps, config: springConfig });

  const offsets: Record<SlideDirection, { x: number; y: number }> = {
    left: { x: -100, y: 0 },
    right: { x: 100, y: 0 },
    up: { x: 0, y: -100 },
    down: { x: 0, y: 100 },
  };

  const offset = offsets[direction];
  return {
    x: interpolate(progress, [0, 1], [offset.x, 0]),
    y: interpolate(progress, [0, 1], [offset.y, 0]),
    opacity: progress,
  };
}

// --- Scale Animations ---

export function scaleIn(
  frame: number,
  fps: number,
  preset: SpringPreset = "bouncy"
) {
  const progress = spring({
    frame,
    fps,
    config: SPRING_PRESETS[preset],
  });

  return {
    scale: interpolate(progress, [0, 1], [0, 1]),
    opacity: interpolate(progress, [0, 0.5], [0, 1], {
      extrapolateRight: "clamp",
    }),
  };
}

// --- Typewriter Effect ---

export function typewriter(
  text: string,
  frame: number,
  fps: number,
  charsPerSecond: number = 30
) {
  const charsPerFrame = charsPerSecond / fps;
  const visibleChars = Math.floor(frame * charsPerFrame);
  return text.slice(0, Math.min(visibleChars, text.length));
}

// --- Stagger Animation (fuer Listen) ---

export function stagger(
  frame: number,
  fps: number,
  index: number,
  delayPerItem: number = 5,
  preset: SpringPreset = "smooth"
) {
  const delay = index * delayPerItem;
  const adjustedFrame = Math.max(0, frame - delay);

  const progress = spring({
    frame: adjustedFrame,
    fps,
    config: SPRING_PRESETS[preset],
  });

  return {
    opacity: progress,
    translateY: interpolate(progress, [0, 1], [30, 0]),
    scale: interpolate(progress, [0, 1], [0.9, 1]),
  };
}

// --- Camera Shake ---

export function cameraShake(
  frame: number,
  intensity: number = 5,
  speed: number = 0.5
) {
  const x = Math.sin(frame * speed * 1.1) * intensity;
  const y = Math.cos(frame * speed * 0.9) * intensity;
  const rotation = Math.sin(frame * speed * 0.7) * (intensity * 0.1);

  return { x, y, rotation };
}

// --- Easing Helpers ---

export function smoothStep(
  frame: number,
  start: number,
  end: number
): number {
  return interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.25, 0.1, 0.25, 1),
  });
}
