import React from "react";
import {
  AbsoluteFill,
  Sequence,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { z } from "zod";
import { WordByWordReveal, TextSlide } from "../components/text/WordByWordReveal";
import { LiveCaption } from "../components/overlays/LiveCaption";

/**
 * Marc's Signal Marketing Reel.
 * Basierend auf dem bastianbarami-Stil:
 * Text-on-Black Hooks + Talking Head mit Live Captions.
 *
 * Format: 1080x1920 (9:16 Instagram Reel)
 * Video: talking-head.mov (42s, eine durchgehende Aufnahme)
 */

export const marcReelSchema = z.object({
  videoFile: z.string(),
});

export const MarcReelComposition: React.FC<
  z.infer<typeof marcReelSchema>
> = ({ videoFile }) => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>

      {/* ============================================ */}
      {/* SZENE 1: TEXT HOOK (0-3s)                    */}
      {/* "Der Hauptgrund warum deine Funnels          */}
      {/*  nicht performen"                            */}
      {/* ============================================ */}
      <Sequence from={0} durationInFrames={3 * fps}>
        <WordByWordReveal
          words={[
            { text: "Der", startFrame: 0 },
            { text: "Hauptgrund", startFrame: 6 },
            { text: "warum", startFrame: 14 },
            { text: "deine", startFrame: 22 },
            { text: "Funnels", startFrame: 30, highlight: true },
            { text: "nicht", startFrame: 42, highlight: true },
            { text: "performen", startFrame: 50, highlight: true },
          ]}
          lineBreakAfter={[2, 3]}
          fontSize={62}
        />
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 2: TALKING HEAD (3-7s)                 */}
      {/* "...liegt daran dass du nicht verstanden      */}
      {/*  hast dass Signal Marketing in 2026 zaehlt"  */}
      {/* ============================================ */}
      <Sequence from={3 * fps} durationInFrames={4 * fps}>
        <TalkingHead videoFile={videoFile} startFromSec={0} />
        <LiveCaption
          captions={[
            { text: "liegt daran", startFrame: 0, endFrame: 18 },
            { text: "dass du", startFrame: 18, endFrame: 30 },
            { text: "nicht verstanden hast", startFrame: 30, endFrame: 50 },
            { text: "dass", startFrame: 50, endFrame: 60 },
            { text: "Signal Marketing", startFrame: 60, endFrame: 82, highlight: true },
            { text: "in 2026", startFrame: 82, endFrame: 100, highlight: true },
            { text: "zaehlt.", startFrame: 100, endFrame: 120 },
          ]}
          fontSize={44}
          positionY={62}
        />
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 3: TEXT STATEMENT (7-9.5s)             */}
      {/* "Signal Marketing > Events"                  */}
      {/* ============================================ */}
      <Sequence from={7 * fps} durationInFrames={Math.round(2.5 * fps)}>
        <WordByWordReveal
          words={[
            { text: "Signal", startFrame: 0, highlight: true },
            { text: "Marketing", startFrame: 10, highlight: true },
            { text: ">", startFrame: 22 },
            { text: "Events", startFrame: 30 },
          ]}
          fontSize={72}
        />
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 4: TALKING HEAD (9.5-16.5s)            */}
      {/* "Die meisten versuchen ihre Kampagnen auf     */}
      {/*  Events zu optimieren statt auf Signale"      */}
      {/* ============================================ */}
      <Sequence from={Math.round(9.5 * fps)} durationInFrames={7 * fps}>
        <TalkingHead videoFile={videoFile} startFromSec={7} />
        <LiveCaption
          captions={[
            { text: "Die meisten", startFrame: 0, endFrame: 20 },
            { text: "versuchen", startFrame: 20, endFrame: 38 },
            { text: "ihre Kampagnen", startFrame: 38, endFrame: 58 },
            { text: "auf Events", startFrame: 58, endFrame: 80 },
            { text: "zu optimieren", startFrame: 80, endFrame: 105 },
            { text: "statt auf", startFrame: 105, endFrame: 125 },
            { text: "Signale.", startFrame: 125, endFrame: 160, highlight: true },
            { text: "Wenn du", startFrame: 165, endFrame: 180 },
            { text: "den Unterschied", startFrame: 180, endFrame: 200 },
            { text: "verstehst", startFrame: 200, endFrame: 210 },
          ]}
          fontSize={44}
          positionY={62}
        />
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 5: TEXT STATEMENT (16.5-19s)            */}
      {/* "Deutlich bessere Ergebnisse"                 */}
      {/* ============================================ */}
      <Sequence from={Math.round(16.5 * fps)} durationInFrames={Math.round(2.5 * fps)}>
        <WordByWordReveal
          words={[
            { text: "Deutlich", startFrame: 0 },
            { text: "bessere", startFrame: 10, highlight: true },
            { text: "Ergebnisse", startFrame: 22, highlight: true },
            { text: "im", startFrame: 36 },
            { text: "Performance", startFrame: 44 },
            { text: "Marketing", startFrame: 54 },
          ]}
          lineBreakAfter={[2]}
          fontSize={60}
        />
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 6: TALKING HEAD (19-26s)               */}
      {/* "Lasst mich kurz erklaeren..."               */}
      {/* ============================================ */}
      <Sequence from={19 * fps} durationInFrames={7 * fps}>
        <TalkingHead videoFile={videoFile} startFromSec={24} />
        <LiveCaption
          captions={[
            { text: "Lasst mich", startFrame: 0, endFrame: 20 },
            { text: "kurz erklaeren.", startFrame: 20, endFrame: 45 },
            { text: "Signale", startFrame: 50, endFrame: 72, highlight: true },
            { text: "sind Events", startFrame: 72, endFrame: 95 },
            { text: "die deutlich", startFrame: 95, endFrame: 115 },
            { text: "tiefer kommen", startFrame: 115, endFrame: 140, highlight: true },
            { text: "aus einem", startFrame: 145, endFrame: 162 },
            { text: "CRM", startFrame: 162, endFrame: 185, highlight: true },
          ]}
          fontSize={44}
          positionY={62}
        />
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 7: TEXT STATEMENT (26-28.5s)            */}
      {/* "Signale kommen aus dem CRM"                 */}
      {/* ============================================ */}
      <Sequence from={26 * fps} durationInFrames={Math.round(2.5 * fps)}>
        <TextSlide
          text="Der Algorithmus kann mit Signalen deutlich mehr arbeiten"
          highlightWords={["Algorithmus", "Signalen"]}
          fontSize={52}
        />
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 8: TALKING HEAD + CTA (28.5-35s)       */}
      {/* "Wie das Ganze geht zeige ich dir im         */}
      {/*  Live-Webinar - meld dich jetzt an"          */}
      {/* ============================================ */}
      <Sequence from={Math.round(28.5 * fps)} durationInFrames={Math.round(6.5 * fps)}>
        <TalkingHead videoFile={videoFile} startFromSec={36.8} />
        <LiveCaption
          captions={[
            { text: "Wie das geht", startFrame: 0, endFrame: 25 },
            { text: "zeige ich dir", startFrame: 25, endFrame: 50 },
            { text: "im", startFrame: 50, endFrame: 60 },
            { text: "Live-Webinar", startFrame: 60, endFrame: 95, highlight: true },
            { text: "Meld dich", startFrame: 105, endFrame: 130 },
            { text: "jetzt an!", startFrame: 130, endFrame: 170, highlight: true },
          ]}
          fontSize={44}
          positionY={62}
        />

        {/* CTA Button Animation */}
        <Sequence from={4 * 30}>
          <CTAButton text="Jetzt anmelden" />
        </Sequence>
      </Sequence>

    </AbsoluteFill>
  );
};

// --- Talking Head mit Video ---

const TalkingHead: React.FC<{
  videoFile: string;
  startFromSec: number;
}> = ({ videoFile, startFromSec }) => {
  return (
    <AbsoluteFill>
      <OffthreadVideo
        src={staticFile(videoFile)}
        startFrom={Math.round(startFromSec * 30)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
      />
      {/* Cinematische Vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.5) 100%)",
          pointerEvents: "none",
        }}
      />
      {/* Unterer Gradient fuer bessere Text-Lesbarkeit */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 40%)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};

// --- CTA Button ---

const CTAButton: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 100 },
  });

  const scale = interpolate(progress, [0, 1], [0.5, 1]);
  const opacity = progress;

  // Pulsierender Glow-Effekt
  const pulse = Math.sin(frame * 0.15) * 0.3 + 0.7;

  return (
    <div
      style={{
        position: "absolute",
        bottom: "12%",
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        zIndex: 20,
        opacity,
        transform: `scale(${scale})`,
      }}
    >
      <div
        style={{
          backgroundColor: "#D4A537",
          color: "#000000",
          fontSize: 32,
          fontWeight: 800,
          fontFamily: "'Inter', 'Helvetica Neue', sans-serif",
          padding: "18px 48px",
          borderRadius: 50,
          boxShadow: `0 0 ${20 + pulse * 20}px rgba(212, 165, 55, ${pulse * 0.6})`,
          letterSpacing: "0.5px",
        }}
      >
        {text}
      </div>
    </div>
  );
};
