import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  Easing,
} from "remotion";

/**
 * Professioneller Text-Reveal Effekt.
 * Inspiriert von remocn (kapishdima/remocn) - Blur Reveal + Tracking In Patterns.
 */

interface TextRevealProps {
  text: string;
  fontSize?: number;
  color?: string;
  fontWeight?: number;
  fontFamily?: string;
  variant?: "blur" | "slide-up" | "letter-by-letter" | "typewriter" | "glitch";
  delay?: number;
}

export const TextReveal: React.FC<TextRevealProps> = ({
  text,
  fontSize = 80,
  color = "#ffffff",
  fontWeight = 700,
  fontFamily = "Inter, system-ui, sans-serif",
  variant = "blur",
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const adjustedFrame = Math.max(0, frame - delay);

  if (variant === "blur") {
    return (
      <BlurReveal
        text={text}
        frame={adjustedFrame}
        fps={fps}
        fontSize={fontSize}
        color={color}
        fontWeight={fontWeight}
        fontFamily={fontFamily}
      />
    );
  }

  if (variant === "slide-up") {
    return (
      <SlideUpReveal
        text={text}
        frame={adjustedFrame}
        fps={fps}
        fontSize={fontSize}
        color={color}
        fontWeight={fontWeight}
        fontFamily={fontFamily}
      />
    );
  }

  if (variant === "letter-by-letter") {
    return (
      <LetterByLetter
        text={text}
        frame={adjustedFrame}
        fps={fps}
        fontSize={fontSize}
        color={color}
        fontWeight={fontWeight}
        fontFamily={fontFamily}
      />
    );
  }

  if (variant === "typewriter") {
    return (
      <Typewriter
        text={text}
        frame={adjustedFrame}
        fps={fps}
        fontSize={fontSize}
        color={color}
        fontWeight={fontWeight}
        fontFamily={fontFamily}
      />
    );
  }

  // glitch
  return (
    <GlitchText
      text={text}
      frame={adjustedFrame}
      fps={fps}
      fontSize={fontSize}
      color={color}
      fontWeight={fontWeight}
      fontFamily={fontFamily}
    />
  );
};

// --- Blur Reveal (remocn-style) ---
const BlurReveal: React.FC<{
  text: string;
  frame: number;
  fps: number;
  fontSize: number;
  color: string;
  fontWeight: number;
  fontFamily: string;
}> = ({ text, frame, fps, fontSize, color, fontWeight, fontFamily }) => {
  const progress = spring({ frame, fps, config: { damping: 15, stiffness: 80 } });
  const blur = interpolate(progress, [0, 1], [20, 0]);
  const opacity = interpolate(progress, [0, 0.6], [0, 1], {
    extrapolateRight: "clamp",
  });
  const scale = interpolate(progress, [0, 1], [0.8, 1]);

  return (
    <div
      style={{
        fontSize,
        color,
        fontWeight,
        fontFamily,
        filter: `blur(${blur}px)`,
        opacity,
        transform: `scale(${scale})`,
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </div>
  );
};

// --- Slide Up Reveal ---
const SlideUpReveal: React.FC<{
  text: string;
  frame: number;
  fps: number;
  fontSize: number;
  color: string;
  fontWeight: number;
  fontFamily: string;
}> = ({ text, frame, fps, fontSize, color, fontWeight, fontFamily }) => {
  const progress = spring({
    frame,
    fps,
    config: { damping: 12, mass: 0.5, stiffness: 100 },
  });
  const translateY = interpolate(progress, [0, 1], [60, 0]);
  const opacity = progress;

  return (
    <div style={{ overflow: "hidden" }}>
      <div
        style={{
          fontSize,
          color,
          fontWeight,
          fontFamily,
          transform: `translateY(${translateY}px)`,
          opacity,
        }}
      >
        {text}
      </div>
    </div>
  );
};

// --- Letter by Letter ---
const LetterByLetter: React.FC<{
  text: string;
  frame: number;
  fps: number;
  fontSize: number;
  color: string;
  fontWeight: number;
  fontFamily: string;
}> = ({ text, frame, fps, fontSize, color, fontWeight, fontFamily }) => {
  const letters = text.split("");

  return (
    <div style={{ display: "flex", fontFamily }}>
      {letters.map((letter, i) => {
        const letterDelay = i * 2;
        const adjustedFrame = Math.max(0, frame - letterDelay);
        const progress = spring({
          frame: adjustedFrame,
          fps,
          config: { damping: 12, stiffness: 200 },
        });

        return (
          <span
            key={`${i}-${letter}`}
            style={{
              fontSize,
              color,
              fontWeight,
              opacity: progress,
              transform: `translateY(${interpolate(progress, [0, 1], [20, 0])}px)`,
              display: "inline-block",
              whiteSpace: "pre",
            }}
          >
            {letter}
          </span>
        );
      })}
    </div>
  );
};

// --- Typewriter ---
const Typewriter: React.FC<{
  text: string;
  frame: number;
  fps: number;
  fontSize: number;
  color: string;
  fontWeight: number;
  fontFamily: string;
}> = ({ text, frame, fps, fontSize, color, fontWeight, fontFamily }) => {
  const charsPerSecond = 25;
  const charsPerFrame = charsPerSecond / fps;
  const visibleChars = Math.min(Math.floor(frame * charsPerFrame), text.length);
  const showCursor = frame % (fps / 2) < fps / 4;

  return (
    <div
      style={{
        fontSize,
        color,
        fontWeight,
        fontFamily: `"Fira Code", ${fontFamily}`,
        whiteSpace: "nowrap",
      }}
    >
      {text.slice(0, visibleChars)}
      {visibleChars < text.length && (
        <span style={{ opacity: showCursor ? 1 : 0 }}>|</span>
      )}
    </div>
  );
};

// --- RGB Glitch Text (remocn-style) ---
const GlitchText: React.FC<{
  text: string;
  frame: number;
  fps: number;
  fontSize: number;
  color: string;
  fontWeight: number;
  fontFamily: string;
}> = ({ text, frame, fps, fontSize, color, fontWeight, fontFamily }) => {
  const progress = spring({ frame, fps, config: { damping: 20, stiffness: 100 } });
  const glitchIntensity = interpolate(progress, [0, 0.5, 1], [8, 3, 0], {
    extrapolateRight: "clamp",
  });

  const offsetR = Math.sin(frame * 0.3) * glitchIntensity;
  const offsetB = Math.cos(frame * 0.5) * glitchIntensity;

  return (
    <div style={{ position: "relative" }}>
      {/* Red channel */}
      <div
        style={{
          position: "absolute",
          fontSize,
          fontWeight,
          fontFamily,
          color: "rgba(255, 0, 0, 0.7)",
          transform: `translate(${offsetR}px, ${-offsetR * 0.5}px)`,
          mixBlendMode: "screen",
        }}
      >
        {text}
      </div>
      {/* Blue channel */}
      <div
        style={{
          position: "absolute",
          fontSize,
          fontWeight,
          fontFamily,
          color: "rgba(0, 0, 255, 0.7)",
          transform: `translate(${offsetB}px, ${offsetB * 0.5}px)`,
          mixBlendMode: "screen",
        }}
      >
        {text}
      </div>
      {/* Main text */}
      <div
        style={{
          fontSize,
          fontWeight,
          fontFamily,
          color,
          opacity: progress,
        }}
      >
        {text}
      </div>
    </div>
  );
};
