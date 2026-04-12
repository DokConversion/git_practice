import React, { useMemo } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  random,
} from "remotion";
import { z } from "zod";
import { audioVisualizerSchema } from "../schemas.js";
import { GradientBackground } from "../components/effects/GradientBackground.js";

/**
 * Audio-Visualizer Komposition.
 * Inspiriert von FelippeChemello/podcast-maker und remotion-audio-visualizers.
 */

export const AudioVisualizerComposition: React.FC<
  z.infer<typeof audioVisualizerSchema>
> = ({ barCount, barColor, backgroundColor }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const bars = useMemo(() => {
    return Array.from({ length: barCount }).map((_, i) => ({
      baseHeight: random(`bar-height-${i}`) * 0.5 + 0.2,
      frequency: random(`bar-freq-${i}`) * 3 + 1,
      phase: random(`bar-phase-${i}`) * Math.PI * 2,
    }));
  }, [barCount]);

  const barWidth = (width * 0.8) / barCount;
  const gap = barWidth * 0.2;
  const effectiveBarWidth = barWidth - gap;
  const startX = width * 0.1;

  return (
    <AbsoluteFill style={{ backgroundColor }}>
      <GradientBackground
        colors={[backgroundColor, "#1a1a2e", backgroundColor]}
        speed={0.1}
        type="radial"
      />

      <AbsoluteFill>
        {bars.map((bar, i) => {
          const animatedHeight =
            bar.baseHeight *
            (0.5 +
              0.5 *
                Math.sin(
                  (frame / fps) * bar.frequency * Math.PI * 2 + bar.phase
                ));

          const barHeight = animatedHeight * height * 0.6;
          const x = startX + i * barWidth;
          const y = height / 2 - barHeight / 2;
          const hueShift = (i / barCount) * 60;

          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: x,
                top: y,
                width: effectiveBarWidth,
                height: barHeight,
                backgroundColor: barColor,
                borderRadius: effectiveBarWidth / 2,
                filter: `hue-rotate(${hueShift}deg)`,
                opacity: 0.8 + animatedHeight * 0.2,
                boxShadow: `0 0 ${10 + animatedHeight * 20}px ${barColor}66`,
              }}
            />
          );
        })}
      </AbsoluteFill>

      <AbsoluteFill
        style={{ justifyContent: "center", alignItems: "center" }}
      >
        <div
          style={{
            fontSize: 36,
            fontWeight: 600,
            color: "rgba(255, 255, 255, 0.15)",
            fontFamily: "Inter, system-ui, sans-serif",
            textTransform: "uppercase",
            letterSpacing: 16,
          }}
        >
          Audio Visualizer
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
