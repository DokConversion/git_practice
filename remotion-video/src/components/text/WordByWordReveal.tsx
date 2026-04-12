import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  Easing,
} from "remotion";

/**
 * Word-by-Word Text Reveal auf schwarzem Hintergrund.
 * Exakt im Stil von bastianbarami Value Reels:
 * - Woerter erscheinen einzeln, synchron zum Sprechen
 * - Bestimmte Woerter in Gold hervorgehoben
 * - Saubere Serif-Font, zentriert
 */

interface WordRevealProps {
  /** Array von Woertern mit Timing und optionalem Highlight */
  words: {
    text: string;
    /** Frame ab dem das Wort erscheint */
    startFrame: number;
    /** Optional: Wort in Akzentfarbe hervorheben */
    highlight?: boolean;
  }[];
  fontSize?: number;
  fontFamily?: string;
  color?: string;
  highlightColor?: string;
  lineBreakAfter?: number[];
}

export const WordByWordReveal: React.FC<WordRevealProps> = ({
  words,
  fontSize = 64,
  fontFamily = "'Georgia', 'Times New Roman', serif",
  color = "#ffffff",
  highlightColor = "#D4A537",
  lineBreakAfter = [],
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        backgroundColor: "#000000",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 60px",
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          alignItems: "center",
          gap: "8px 14px",
          maxWidth: "90%",
        }}
      >
        {words.map((word, i) => {
          const isVisible = frame >= word.startFrame;
          if (!isVisible) return null;

          const age = frame - word.startFrame;
          const progress = spring({
            frame: age,
            fps,
            config: { damping: 18, stiffness: 200, mass: 0.5 },
          });

          const opacity = interpolate(progress, [0, 1], [0, 1]);
          const scale = interpolate(progress, [0, 1], [0.7, 1]);
          const blur = interpolate(progress, [0, 1], [8, 0]);

          const wordColor = word.highlight ? highlightColor : color;
          const needsBreak = lineBreakAfter.includes(i);

          return (
            <React.Fragment key={i}>
              <span
                style={{
                  fontSize,
                  fontFamily,
                  fontWeight: word.highlight ? 700 : 500,
                  color: wordColor,
                  opacity,
                  transform: `scale(${scale})`,
                  filter: `blur(${blur}px)`,
                  display: "inline-block",
                  whiteSpace: "nowrap",
                }}
              >
                {word.text}
              </span>
              {needsBreak && (
                <div style={{ width: "100%", height: 0 }} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

/**
 * Einfache Text-Slide Variante: Ganzer Satz erscheint auf einmal
 * mit elegantem Fade-In.
 */
interface TextSlideProps {
  text: string;
  fontSize?: number;
  fontFamily?: string;
  color?: string;
  highlightWords?: string[];
  highlightColor?: string;
}

export const TextSlide: React.FC<TextSlideProps> = ({
  text,
  fontSize = 56,
  fontFamily = "'Georgia', 'Times New Roman', serif",
  color = "#ffffff",
  highlightWords = [],
  highlightColor = "#D4A537",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 80 },
  });

  const opacity = interpolate(progress, [0, 1], [0, 1]);
  const translateY = interpolate(progress, [0, 1], [20, 0]);

  const words = text.split(" ");

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        backgroundColor: "#000000",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 60px",
      }}
    >
      <div
        style={{
          opacity,
          transform: `translateY(${translateY}px)`,
          textAlign: "center",
          lineHeight: 1.4,
        }}
      >
        {words.map((word, i) => {
          const isHighlight = highlightWords.some(
            (hw) => word.toLowerCase().replace(/[,.\-!?]/g, "") === hw.toLowerCase()
          );

          return (
            <span
              key={i}
              style={{
                fontSize,
                fontFamily,
                fontWeight: isHighlight ? 700 : 500,
                color: isHighlight ? highlightColor : color,
              }}
            >
              {word}{" "}
            </span>
          );
        })}
      </div>
    </div>
  );
};
