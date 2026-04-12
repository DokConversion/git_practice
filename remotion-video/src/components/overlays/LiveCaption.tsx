import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";

/**
 * Live-Caption Overlay fuer Talking-Head Szenen.
 * Im bastianbarami-Stil: einzelnes Wort, zentriert, weiss, bold.
 * Woerter wechseln synchron zum Sprechen.
 */

interface CaptionWord {
  text: string;
  /** Frame ab dem das Wort gezeigt wird */
  startFrame: number;
  /** Frame bis zu dem das Wort gezeigt wird */
  endFrame: number;
  /** Optional: Wort hervorheben */
  highlight?: boolean;
}

interface LiveCaptionProps {
  captions: CaptionWord[];
  fontSize?: number;
  fontFamily?: string;
  color?: string;
  highlightColor?: string;
  /** Position: Prozent von oben */
  positionY?: number;
  /** Hintergrund-Pill hinter dem Text */
  showBackground?: boolean;
}

export const LiveCaption: React.FC<LiveCaptionProps> = ({
  captions,
  fontSize = 48,
  fontFamily = "'Inter', 'Helvetica Neue', sans-serif",
  color = "#ffffff",
  highlightColor = "#D4A537",
  positionY = 60,
  showBackground = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Finde das aktuelle Wort
  const currentCaption = captions.find(
    (c) => frame >= c.startFrame && frame < c.endFrame
  );

  if (!currentCaption) return null;

  // Animation beim Erscheinen
  const age = frame - currentCaption.startFrame;
  const progress = spring({
    frame: age,
    fps,
    config: { damping: 20, stiffness: 300, mass: 0.4 },
  });

  const opacity = interpolate(progress, [0, 1], [0, 1]);
  const scale = interpolate(progress, [0, 1], [0.85, 1]);
  const textColor = currentCaption.highlight ? highlightColor : color;

  return (
    <div
      style={{
        position: "absolute",
        top: `${positionY}%`,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 10,
      }}
    >
      <div
        style={{
          opacity,
          transform: `scale(${scale})`,
        }}
      >
        {showBackground && (
          <div
            style={{
              position: "absolute",
              inset: "-8px -20px",
              backgroundColor: "rgba(0, 0, 0, 0.6)",
              borderRadius: 8,
              backdropFilter: "blur(4px)",
            }}
          />
        )}
        <span
          style={{
            fontSize,
            fontFamily,
            fontWeight: 700,
            color: textColor,
            textShadow: "0 2px 8px rgba(0,0,0,0.8), 0 0 30px rgba(0,0,0,0.5)",
            position: "relative",
            letterSpacing: "-0.02em",
          }}
        >
          {currentCaption.text}
        </span>
      </div>
    </div>
  );
};

/**
 * Multi-Word Caption: Zeigt mehrere Woerter gleichzeitig an,
 * mit Hervorhebung des aktuellen Worts.
 */
interface MultiWordCaptionProps {
  /** Gruppen von Woertern die zusammen erscheinen */
  phrases: {
    words: string[];
    startFrame: number;
    endFrame: number;
    /** Index des aktuell gesprochenen Worts (wird hervorgehoben) */
    activeWordIndex?: number;
  }[];
  fontSize?: number;
  fontFamily?: string;
  color?: string;
  activeColor?: string;
  positionY?: number;
}

export const MultiWordCaption: React.FC<MultiWordCaptionProps> = ({
  phrases,
  fontSize = 42,
  fontFamily = "'Inter', 'Helvetica Neue', sans-serif",
  color = "rgba(255,255,255,0.6)",
  activeColor = "#ffffff",
  positionY = 60,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const currentPhrase = phrases.find(
    (p) => frame >= p.startFrame && frame < p.endFrame
  );

  if (!currentPhrase) return null;

  const age = frame - currentPhrase.startFrame;
  const progress = spring({
    frame: age,
    fps,
    config: { damping: 25, stiffness: 250 },
  });

  return (
    <div
      style={{
        position: "absolute",
        top: `${positionY}%`,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        gap: 12,
        opacity: interpolate(progress, [0, 1], [0, 1]),
        zIndex: 10,
      }}
    >
      {currentPhrase.words.map((word, i) => (
        <span
          key={i}
          style={{
            fontSize,
            fontFamily,
            fontWeight: 700,
            color:
              i === currentPhrase.activeWordIndex ? activeColor : color,
            textShadow: "0 2px 8px rgba(0,0,0,0.8)",
            transition: "color 0.1s",
          }}
        >
          {word}
        </span>
      ))}
    </div>
  );
};
