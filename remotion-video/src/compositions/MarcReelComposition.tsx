import React from "react";
import {
  AbsoluteFill,
  Sequence,
  Audio,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  Easing,
  random,
} from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/Poppins";

// Lade Poppins Font
const { fontFamily } = loadFont("normal", {
  weights: ["300", "400", "600", "700", "800"],
});

const FONT = fontFamily;

export const marcReelSchema = z.object({
  videoFile: z.string(),
});

export const MarcReelComposition: React.FC<
  z.infer<typeof marcReelSchema>
> = ({ videoFile }) => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000", fontFamily: FONT }}>

      {/* === DURCHGEHENDE AUDIO-SPUR === */}
      <Audio src={staticFile(videoFile)} volume={1} />

      {/* ============================================ */}
      {/* SZENE 1: TEXT HOOK (0-3s)                    */}
      {/* Animierter Gradient-Hintergrund              */}
      {/* ============================================ */}
      <Sequence from={0} durationInFrames={3 * fps}>
        <AbsoluteFill>
          <AnimatedGradientBg
            colors={["#0a0a0a", "#1a0a2e", "#0a0a0a"]}
          />
          <AbsoluteFill style={{
            justifyContent: "center",
            alignItems: "center",
            padding: "0 60px",
          }}>
            <AnimatedWords
              words={[
                { text: "Der Hauptgrund", delay: 0 },
                { text: "warum deine", delay: 8 },
                { text: "Funnels nicht", delay: 16, highlight: true },
                { text: "performen", delay: 26, highlight: true },
              ]}
            />
          </AbsoluteFill>
        </AbsoluteFill>
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 2: TALKING HEAD (3-7.5s)               */}
      {/* ============================================ */}
      <Sequence from={3 * fps} durationInFrames={Math.round(4.5 * fps)}>
        <TalkingHead videoFile={videoFile} startFromSec={0} />
        <CaptionOverlay
          words={[
            { text: "liegt daran", start: 0, end: 20 },
            { text: "dass du nicht", start: 20, end: 42 },
            { text: "verstanden hast", start: 42, end: 65 },
            { text: "Signal Marketing", start: 65, end: 90, highlight: true },
            { text: "in 2026 zaehlt", start: 90, end: 130, highlight: true },
          ]}
        />
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 3: B-ROLL - Signal Wave Animation      */}
      {/* (7.5-10s)                                    */}
      {/* ============================================ */}
      <Sequence from={Math.round(7.5 * fps)} durationInFrames={Math.round(2.5 * fps)}>
        <SignalWaveBRoll />
        <AbsoluteFill style={{
          justifyContent: "center",
          alignItems: "center",
          zIndex: 10,
        }}>
          <AnimatedWords
            words={[
              { text: "Signal Marketing", delay: 0, highlight: true },
              { text: ">", delay: 12 },
              { text: "Events", delay: 20 },
            ]}
            size={68}
          />
        </AbsoluteFill>
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 4: TALKING HEAD (10-14s)               */}
      {/* ============================================ */}
      <Sequence from={10 * fps} durationInFrames={4 * fps}>
        <TalkingHead videoFile={videoFile} startFromSec={7} />
        <CaptionOverlay
          words={[
            { text: "Die meisten", start: 0, end: 18 },
            { text: "versuchen", start: 18, end: 34 },
            { text: "Kampagnen auf", start: 34, end: 55 },
            { text: "Events", start: 55, end: 72 },
            { text: "zu optimieren", start: 72, end: 95 },
            { text: "statt auf Signale", start: 95, end: 120, highlight: true },
          ]}
        />
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 5: B-ROLL - Dashboard Mockup (14-16s)  */}
      {/* ============================================ */}
      <Sequence from={14 * fps} durationInFrames={2 * fps}>
        <DashboardBRoll />
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 6: TALKING HEAD (16-19.5s)             */}
      {/* ============================================ */}
      <Sequence from={16 * fps} durationInFrames={Math.round(3.5 * fps)}>
        <TalkingHead videoFile={videoFile} startFromSec={14} />
        <CaptionOverlay
          words={[
            { text: "Wenn du den", start: 0, end: 22 },
            { text: "Unterschied", start: 22, end: 42, highlight: true },
            { text: "verstehst", start: 42, end: 62 },
            { text: "deutlich bessere", start: 68, end: 90, highlight: true },
            { text: "Ergebnisse", start: 90, end: 105, highlight: true },
          ]}
        />
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 7: TEXT + Animated Metrics (19.5-22s)   */}
      {/* ============================================ */}
      <Sequence from={Math.round(19.5 * fps)} durationInFrames={Math.round(2.5 * fps)}>
        <AbsoluteFill>
          <AnimatedGradientBg
            colors={["#0a0a0a", "#0a1628", "#0a0a0a"]}
          />
          <MetricsBRoll />
          <AbsoluteFill style={{
            justifyContent: "center",
            alignItems: "center",
            zIndex: 10,
          }}>
            <AnimatedWords
              words={[
                { text: "Deutlich bessere", delay: 0, highlight: true },
                { text: "Ergebnisse im", delay: 14 },
                { text: "Performance Marketing", delay: 26 },
              ]}
              size={52}
            />
          </AbsoluteFill>
        </AbsoluteFill>
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 8: TALKING HEAD (22-28s)               */}
      {/* "Signale kommen tiefer aus dem CRM"          */}
      {/* ============================================ */}
      <Sequence from={22 * fps} durationInFrames={6 * fps}>
        <TalkingHead videoFile={videoFile} startFromSec={24} />
        <CaptionOverlay
          words={[
            { text: "Lasst mich", start: 0, end: 18 },
            { text: "kurz erklaeren", start: 18, end: 40 },
            { text: "Signale sind Events", start: 46, end: 72, highlight: true },
            { text: "die deutlich", start: 72, end: 92 },
            { text: "tiefer kommen", start: 92, end: 115, highlight: true },
            { text: "aus einem CRM", start: 120, end: 150, highlight: true },
            { text: "Der Algorithmus", start: 155, end: 175 },
          ]}
        />
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 9: B-ROLL - CRM Flow (28-30s)          */}
      {/* ============================================ */}
      <Sequence from={28 * fps} durationInFrames={2 * fps}>
        <CRMFlowBRoll />
        <AbsoluteFill style={{
          justifyContent: "center",
          alignItems: "center",
          zIndex: 10,
        }}>
          <AnimatedWords
            words={[
              { text: "CRM", delay: 0, highlight: true },
              { text: "→ Algorithmus", delay: 10 },
              { text: "→ Ergebnisse", delay: 22, highlight: true },
            ]}
            size={52}
          />
        </AbsoluteFill>
      </Sequence>

      {/* ============================================ */}
      {/* SZENE 10: TALKING HEAD + CTA (30-38s)        */}
      {/* ============================================ */}
      <Sequence from={30 * fps} durationInFrames={8 * fps}>
        <TalkingHead videoFile={videoFile} startFromSec={36.8} />
        <CaptionOverlay
          words={[
            { text: "Wie das geht", start: 0, end: 25 },
            { text: "zeige ich dir", start: 25, end: 48 },
            { text: "im Live-Webinar", start: 48, end: 80, highlight: true },
            { text: "Meld dich", start: 90, end: 115 },
            { text: "jetzt an!", start: 115, end: 160, highlight: true },
          ]}
        />
        <Sequence from={4 * fps}>
          <CTAButton text="Jetzt anmelden" />
        </Sequence>
      </Sequence>

    </AbsoluteFill>
  );
};

// ===========================
// KOMPONENTEN
// ===========================

// --- Animated Words (Text-on-Black Szenen) ---

const AnimatedWords: React.FC<{
  words: { text: string; delay: number; highlight?: boolean }[];
  size?: number;
}> = ({ words, size = 58 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 8,
    }}>
      {words.map((word, i) => {
        const age = Math.max(0, frame - word.delay);
        const progress = spring({
          frame: age,
          fps,
          config: { damping: 18, stiffness: 180, mass: 0.5 },
        });

        return (
          <div
            key={i}
            style={{
              fontSize: size,
              fontWeight: word.highlight ? 700 : 300,
              color: word.highlight ? "#D4A537" : "#ffffff",
              opacity: interpolate(progress, [0, 1], [0, 1]),
              transform: `translateY(${interpolate(progress, [0, 1], [25, 0])}px) scale(${interpolate(progress, [0, 1], [0.9, 1])})`,
              fontFamily: FONT,
              textAlign: "center",
              letterSpacing: "-0.02em",
            }}
          >
            {word.text}
          </div>
        );
      })}
    </div>
  );
};

// --- Caption Overlay (fuer Talking Head) ---

const CaptionOverlay: React.FC<{
  words: { text: string; start: number; end: number; highlight?: boolean }[];
}> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const current = words.find((w) => frame >= w.start && frame < w.end);
  if (!current) return null;

  const age = frame - current.start;
  const progress = spring({
    frame: age,
    fps,
    config: { damping: 22, stiffness: 280, mass: 0.4 },
  });

  return (
    <div style={{
      position: "absolute",
      top: "58%",
      left: 0,
      right: 0,
      display: "flex",
      justifyContent: "center",
      zIndex: 10,
    }}>
      <div style={{
        opacity: interpolate(progress, [0, 1], [0, 1]),
        transform: `scale(${interpolate(progress, [0, 1], [0.88, 1])})`,
      }}>
        <span style={{
          fontSize: 46,
          fontWeight: current.highlight ? 700 : 600,
          color: current.highlight ? "#D4A537" : "#ffffff",
          fontFamily: FONT,
          textShadow: "0 2px 12px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.6)",
          letterSpacing: "-0.01em",
        }}>
          {current.text}
        </span>
      </div>
    </div>
  );
};

// --- Talking Head ---

const TalkingHead: React.FC<{
  videoFile: string;
  startFromSec: number;
}> = ({ videoFile, startFromSec }) => {
  return (
    <AbsoluteFill>
      <OffthreadVideo
        src={staticFile(videoFile)}
        startFrom={Math.round(startFromSec * 30)}
        muted
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
      <AbsoluteFill style={{
        background: "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.5) 100%)",
        pointerEvents: "none",
      }} />
      <AbsoluteFill style={{
        background: "linear-gradient(to top, rgba(0,0,0,0.75) 0%, transparent 35%)",
        pointerEvents: "none",
      }} />
    </AbsoluteFill>
  );
};

// --- Animated Gradient Background ---

const AnimatedGradientBg: React.FC<{
  colors: string[];
}> = ({ colors }) => {
  const frame = useCurrentFrame();
  const angle = frame * 0.5;
  return (
    <AbsoluteFill style={{
      background: `linear-gradient(${angle}deg, ${colors.join(", ")})`,
    }} />
  );
};

// --- B-ROLL: Signal Wave Animation ---

const SignalWaveBRoll: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const points = 80;
  const pathData = Array.from({ length: points }).map((_, i) => {
    const x = (i / points) * width;
    const y = height / 2 +
      Math.sin((i / points) * 6 + frame * 0.08) * 80 +
      Math.sin((i / points) * 3 + frame * 0.05) * 40;
    return `${i === 0 ? "M" : "L"} ${x} ${y}`;
  }).join(" ");

  return (
    <AbsoluteFill style={{ backgroundColor: "#050510" }}>
      <svg width={width} height={height}>
        {/* Glow */}
        <path d={pathData} fill="none" stroke="#D4A53744" strokeWidth={20} />
        <path d={pathData} fill="none" stroke="#D4A53788" strokeWidth={6} />
        <path d={pathData} fill="none" stroke="#D4A537" strokeWidth={2} />
        {/* Zweite Welle */}
        {(() => {
          const p2 = Array.from({ length: points }).map((_, i) => {
            const x = (i / points) * width;
            const y = height / 2 +
              Math.cos((i / points) * 4 + frame * 0.06) * 60 +
              Math.sin((i / points) * 7 + frame * 0.1) * 30;
            return `${i === 0 ? "M" : "L"} ${x} ${y}`;
          }).join(" ");
          return (
            <>
              <path d={p2} fill="none" stroke="#6366f144" strokeWidth={12} />
              <path d={p2} fill="none" stroke="#6366f1" strokeWidth={2} />
            </>
          );
        })()}
      </svg>
      {/* Particles */}
      {Array.from({ length: 20 }).map((_, i) => {
        const x = random(`sw-x-${i}`) * width;
        const baseY = random(`sw-y-${i}`) * height;
        const y = baseY + Math.sin(frame * 0.05 + i) * 20;
        const size = random(`sw-s-${i}`) * 4 + 1;
        return (
          <div key={i} style={{
            position: "absolute",
            left: x, top: y,
            width: size, height: size,
            borderRadius: "50%",
            backgroundColor: "#D4A537",
            opacity: 0.3 + random(`sw-o-${i}`) * 0.4,
          }} />
        );
      })}
    </AbsoluteFill>
  );
};

// --- B-ROLL: Dashboard Mockup ---

const DashboardBRoll: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({ frame, fps, config: { damping: 15, stiffness: 80 } });

  const bars = [
    { label: "Click Events", value: 35, color: "#ef4444" },
    { label: "Form Submits", value: 52, color: "#f59e0b" },
    { label: "CRM Signale", value: 89, color: "#22c55e" },
  ];

  return (
    <AbsoluteFill style={{
      backgroundColor: "#0a0f1a",
      justifyContent: "center",
      alignItems: "center",
      padding: 60,
    }}>
      {/* Header */}
      <div style={{
        position: "absolute",
        top: "25%",
        fontSize: 28,
        fontWeight: 300,
        color: "#64748b",
        fontFamily: FONT,
        opacity: progress,
        letterSpacing: "0.1em",
        textTransform: "uppercase",
      }}>
        Performance Vergleich
      </div>

      {/* Bars */}
      <div style={{
        display: "flex",
        flexDirection: "column",
        gap: 40,
        width: "80%",
        marginTop: 40,
      }}>
        {bars.map((bar, i) => {
          const barDelay = i * 8;
          const barAge = Math.max(0, frame - barDelay);
          const barProgress = spring({
            frame: barAge, fps,
            config: { damping: 12, stiffness: 60 },
          });
          const width = bar.value * barProgress;

          return (
            <div key={i}>
              <div style={{
                fontSize: 22, fontWeight: 400, color: "#94a3b8",
                marginBottom: 10, fontFamily: FONT,
                opacity: barProgress,
              }}>
                {bar.label}
              </div>
              <div style={{
                height: 36, borderRadius: 8,
                backgroundColor: "#1e293b",
                overflow: "hidden",
              }}>
                <div style={{
                  height: "100%",
                  width: `${width}%`,
                  backgroundColor: bar.color,
                  borderRadius: 8,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "flex-end",
                  paddingRight: 12,
                }}>
                  <span style={{
                    fontSize: 18, fontWeight: 700,
                    color: "#fff", fontFamily: FONT,
                  }}>
                    {Math.round(width)}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// --- B-ROLL: Metrics Animation ---

const MetricsBRoll: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  return (
    <AbsoluteFill style={{ opacity: 0.15 }}>
      {Array.from({ length: 12 }).map((_, i) => {
        const x = random(`m-x-${i}`) * width;
        const y = random(`m-y-${i}`) * height;
        const size = random(`m-s-${i}`) * 60 + 30;
        const speed = random(`m-sp-${i}`) * 0.5 + 0.3;
        const floatY = Math.sin(frame * speed * 0.1 + i) * 15;

        return (
          <div key={i} style={{
            position: "absolute",
            left: x, top: y + floatY,
            width: size, height: size,
            borderRadius: 12,
            border: "1px solid #D4A53733",
            backgroundColor: "#D4A53708",
          }} />
        );
      })}
    </AbsoluteFill>
  );
};

// --- B-ROLL: CRM Flow ---

const CRMFlowBRoll: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const steps = [
    { icon: "📊", label: "CRM", delay: 0 },
    { icon: "⚡", label: "Signal", delay: 8 },
    { icon: "🎯", label: "Algorithmus", delay: 16 },
    { icon: "📈", label: "Performance", delay: 24 },
  ];

  return (
    <AbsoluteFill style={{
      backgroundColor: "#050510",
      justifyContent: "center",
      alignItems: "center",
    }}>
      <div style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 30,
      }}>
        {steps.map((step, i) => {
          const age = Math.max(0, frame - step.delay);
          const progress = spring({
            frame: age, fps,
            config: { damping: 15, stiffness: 150 },
          });

          return (
            <React.Fragment key={i}>
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
                opacity: progress,
                transform: `translateX(${interpolate(progress, [0, 1], [-30, 0])}px)`,
              }}>
                <div style={{
                  width: 56, height: 56,
                  borderRadius: 14,
                  backgroundColor: "#1a1a2e",
                  border: "1px solid #D4A53744",
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  fontSize: 28,
                }}>
                  {step.icon}
                </div>
                <span style={{
                  fontSize: 26, fontWeight: 500,
                  color: "#e2e8f0", fontFamily: FONT,
                }}>
                  {step.label}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div style={{
                  width: 2, height: 20,
                  backgroundColor: "#D4A53744",
                  opacity: progress,
                }} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// --- CTA Button ---

const CTAButton: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame, fps,
    config: { damping: 12, stiffness: 100 },
  });

  const pulse = Math.sin(frame * 0.15) * 0.3 + 0.7;

  return (
    <div style={{
      position: "absolute",
      bottom: "12%",
      left: 0, right: 0,
      display: "flex",
      justifyContent: "center",
      zIndex: 20,
      opacity: progress,
      transform: `scale(${interpolate(progress, [0, 1], [0.5, 1])})`,
    }}>
      <div style={{
        backgroundColor: "#D4A537",
        color: "#000000",
        fontSize: 32,
        fontWeight: 800,
        fontFamily: FONT,
        padding: "18px 48px",
        borderRadius: 50,
        boxShadow: `0 0 ${20 + pulse * 20}px rgba(212, 165, 55, ${pulse * 0.6})`,
      }}>
        {text}
      </div>
    </div>
  );
};
