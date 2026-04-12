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
  random,
} from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/Poppins";

const { fontFamily: FONT } = loadFont("normal", {
  weights: ["300", "400", "600", "700", "800"],
});

export const marcReelSchema = z.object({
  videoFile: z.string(),
});

/**
 * Marc's Signal Marketing Reel - V3
 *
 * ARCHITEKTUR: Video + Audio laufen DURCHGEHEND.
 * Text-Slides und B-Roll sind Overlays die drueber gelegt werden.
 * So bleibt alles synchron.
 *
 * Timestamps aus Whisper-Transkription:
 * 00:00-04.8  "Der Hauptgrund warum deine Funnels nicht performen
 *              liegt daran dass du nicht verstanden hast dass Signal"
 * 04.8-07.0   "Marketing in 2026 zaehlt."
 * 07.0-11.5   "Die meisten versuchen ihre Kampagnen..."
 * 11.5-16.4   "...auf Events zu optimieren statt auf Signale."
 * 16.4-21.6   "Wenn du den Unterschied verstehst..."
 * 21.6-24.0   "...bessere Ergebnisse im Performance Marketing."
 * 24.2-25.5   "Lasst mich kurz erklaeren."
 * 25.5-32.4   "Signale sind Events die tiefer kommen aus CRM..."
 * 32.4-36.8   "...Algorithmus mehr arbeiten kann..."
 * 36.8-42.0   "Live-Webinar, meld dich jetzt an."
 */

export const MarcReelComposition: React.FC<
  z.infer<typeof marcReelSchema>
> = ({ videoFile }) => {
  const { fps } = useVideoConfig();
  const sec = (s: number) => Math.round(s * fps);

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000", fontFamily: FONT }}>

      {/* ========================================= */}
      {/* LAYER 1: VIDEO - laeuft DURCHGEHEND       */}
      {/* ========================================= */}
      <OffthreadVideo
        src={staticFile(videoFile)}
        muted
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />

      {/* Cinematische Vignette (immer sichtbar) */}
      <AbsoluteFill style={{
        background: "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.5) 100%)",
        pointerEvents: "none",
      }} />
      <AbsoluteFill style={{
        background: "linear-gradient(to top, rgba(0,0,0,0.75) 0%, transparent 35%)",
        pointerEvents: "none",
      }} />

      {/* ========================================= */}
      {/* LAYER 2: AUDIO - laeuft DURCHGEHEND       */}
      {/* ========================================= */}
      <Audio src={staticFile(videoFile)} volume={1} />

      {/* ========================================= */}
      {/* LAYER 3: OVERLAYS (Text + B-Roll)         */}
      {/* Diese ueberdecken das Video temporaer      */}
      {/* ========================================= */}

      {/* --- 0:00-0:02 TEXT HOOK --- */}
      {/* Audio sagt: "Der Hauptgrund warum deine Funnels nicht performen" */}
      <Sequence from={sec(0)} durationInFrames={sec(2)}>
        <FadeOverlay>
          <AnimatedGradientBg colors={["#0a0a0a", "#1a0a2e", "#0a0a0a"]} />
          <CenterContent>
            <AnimatedWords words={[
              { text: "Der Hauptgrund", delay: 0 },
              { text: "warum deine", delay: 8 },
              { text: "Funnels nicht", delay: 16, highlight: true },
              { text: "performen", delay: 26, highlight: true },
            ]} />
          </CenterContent>
        </FadeOverlay>
      </Sequence>

      {/* --- 0:02-0:07 TALKING HEAD (sichtbar) --- */}
      {/* Audio: "...liegt daran... Signal Marketing in 2026 zaehlt" */}
      <Sequence from={sec(2)} durationInFrames={sec(5)}>
        <CaptionOverlay words={[
          { text: "liegt daran", start: 0, end: sec(0.8) },
          { text: "dass du nicht", start: sec(0.8), end: sec(1.8) },
          { text: "verstanden hast", start: sec(1.8), end: sec(2.8) },
          { text: "Signal Marketing", start: sec(2.8), end: sec(4), highlight: true },
          { text: "in 2026 zaehlt", start: sec(4), end: sec(5), highlight: true },
        ]} />
      </Sequence>

      {/* --- 0:07-0:09 B-ROLL: Signal Wave --- */}
      {/* Audio: "Schau, die meisten versuchen noch immer..." */}
      <Sequence from={sec(7)} durationInFrames={sec(2)}>
        <FadeOverlay>
          <SignalWaveBRoll />
          <CenterContent>
            <AnimatedWords words={[
              { text: "Signal Marketing", delay: 0, highlight: true },
              { text: ">", delay: 10 },
              { text: "Events", delay: 18 },
            ]} size={68} />
          </CenterContent>
        </FadeOverlay>
      </Sequence>

      {/* --- 0:09-0:16 TALKING HEAD --- */}
      {/* Audio: "...Kampagnen auf Events optimieren statt auf Signale" */}
      <Sequence from={sec(9)} durationInFrames={sec(7)}>
        <CaptionOverlay words={[
          { text: "die meisten versuchen", start: 0, end: sec(1.5) },
          { text: "ihre Kampagnen", start: sec(1.5), end: sec(2.8) },
          { text: "auf Events", start: sec(2.8), end: sec(4) },
          { text: "zu optimieren", start: sec(4), end: sec(5.2) },
          { text: "statt auf", start: sec(5.2), end: sec(6) },
          { text: "Signale", start: sec(6), end: sec(7), highlight: true },
        ]} />
      </Sequence>

      {/* --- 0:16-0:18 B-ROLL: Dashboard --- */}
      {/* Audio: "Wenn du den Unterschied verstehst..." */}
      <Sequence from={sec(16)} durationInFrames={sec(2)}>
        <FadeOverlay>
          <DashboardBRoll />
        </FadeOverlay>
      </Sequence>

      {/* --- 0:18-0:24 TALKING HEAD --- */}
      {/* Audio: "...deutlich bessere Ergebnisse... Lasst mich erklaeren" */}
      <Sequence from={sec(18)} durationInFrames={sec(6)}>
        <CaptionOverlay words={[
          { text: "deutlich bessere", start: 0, end: sec(1.5), highlight: true },
          { text: "Ergebnisse", start: sec(1.5), end: sec(3), highlight: true },
          { text: "im Performance Marketing", start: sec(3), end: sec(5) },
          { text: "Lasst mich erklaeren", start: sec(5.2), end: sec(6) },
        ]} />
      </Sequence>

      {/* --- 0:24-0:26 B-ROLL: CRM Flow --- */}
      {/* Audio: "Signale sind Events die tiefer kommen..." */}
      <Sequence from={sec(24)} durationInFrames={sec(2)}>
        <FadeOverlay>
          <CRMFlowBRoll />
        </FadeOverlay>
      </Sequence>

      {/* --- 0:26-0:37 TALKING HEAD --- */}
      {/* Audio: "...aus einem CRM... Algorithmus... Live-Webinar" */}
      <Sequence from={sec(26)} durationInFrames={sec(11)}>
        <CaptionOverlay words={[
          { text: "aus einem CRM", start: 0, end: sec(1.8), highlight: true },
          { text: "der Algorithmus", start: sec(2), end: sec(3.5) },
          { text: "kann damit", start: sec(3.5), end: sec(4.8) },
          { text: "deutlich mehr", start: sec(4.8), end: sec(6.2), highlight: true },
          { text: "arbeiten", start: sec(6.2), end: sec(7.5) },
          { text: "Wie das geht", start: sec(8), end: sec(9.2) },
          { text: "zeige ich dir", start: sec(9.2), end: sec(10) },
          { text: "im Live-Webinar", start: sec(10), end: sec(11), highlight: true },
        ]} />
      </Sequence>

      {/* --- 0:37-0:42 CTA --- */}
      <Sequence from={sec(37)} durationInFrames={sec(5)}>
        <CaptionOverlay words={[
          { text: "Meld dich", start: 0, end: sec(1.5) },
          { text: "jetzt an!", start: sec(1.5), end: sec(5), highlight: true },
        ]} />
        <Sequence from={sec(1)}>
          <CTAButton text="Jetzt anmelden" />
        </Sequence>
      </Sequence>

    </AbsoluteFill>
  );
};

// ===========================
// HELPER KOMPONENTEN
// ===========================

// --- Overlay mit Fade-In/Out ---
const FadeOverlay: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 8, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp" }
  );

  return (
    <AbsoluteFill style={{ opacity: Math.min(fadeIn, fadeOut), zIndex: 5 }}>
      {children}
    </AbsoluteFill>
  );
};

// --- Center Content ---
const CenterContent: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{
    justifyContent: "center",
    alignItems: "center",
    padding: "0 60px",
    zIndex: 10,
  }}>
    {children}
  </AbsoluteFill>
);

// --- Animated Words (Text Slides) ---
const AnimatedWords: React.FC<{
  words: { text: string; delay: number; highlight?: boolean }[];
  size?: number;
}> = ({ words, size = 58 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
      {words.map((word, i) => {
        const progress = spring({
          frame: Math.max(0, frame - word.delay),
          fps,
          config: { damping: 18, stiffness: 180, mass: 0.5 },
        });
        return (
          <div key={i} style={{
            fontSize: size,
            fontWeight: word.highlight ? 700 : 300,
            color: word.highlight ? "#D4A537" : "#ffffff",
            opacity: progress,
            transform: `translateY(${interpolate(progress, [0, 1], [25, 0])}px)`,
            fontFamily: FONT,
            textAlign: "center",
          }}>
            {word.text}
          </div>
        );
      })}
    </div>
  );
};

// --- Caption Overlay (Talking Head) ---
const CaptionOverlay: React.FC<{
  words: { text: string; start: number; end: number; highlight?: boolean }[];
}> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const current = words.find((w) => frame >= w.start && frame < w.end);
  if (!current) return null;

  const progress = spring({
    frame: frame - current.start,
    fps,
    config: { damping: 22, stiffness: 280, mass: 0.4 },
  });

  return (
    <div style={{
      position: "absolute", top: "58%",
      left: 0, right: 0,
      display: "flex", justifyContent: "center",
      zIndex: 10,
    }}>
      <div style={{
        opacity: progress,
        transform: `scale(${interpolate(progress, [0, 1], [0.88, 1])})`,
      }}>
        <span style={{
          fontSize: 46,
          fontWeight: current.highlight ? 700 : 600,
          color: current.highlight ? "#D4A537" : "#ffffff",
          fontFamily: FONT,
          textShadow: "0 2px 12px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.6)",
        }}>
          {current.text}
        </span>
      </div>
    </div>
  );
};

// --- Animated Gradient Background ---
const AnimatedGradientBg: React.FC<{ colors: string[] }> = ({ colors }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{
      background: `linear-gradient(${frame * 0.5}deg, ${colors.join(", ")})`,
    }} />
  );
};

// --- B-ROLL: Signal Wave ---
const SignalWaveBRoll: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const pts = 80;

  const makePath = (freq: number, amp: number, speed: number, phase: number) =>
    Array.from({ length: pts }).map((_, i) => {
      const x = (i / pts) * width;
      const y = height / 2 +
        Math.sin((i / pts) * freq + frame * speed) * amp +
        Math.sin((i / pts) * (freq * 0.5) + frame * speed * 0.7 + phase) * (amp * 0.5);
      return `${i === 0 ? "M" : "L"} ${x} ${y}`;
    }).join(" ");

  return (
    <AbsoluteFill style={{ backgroundColor: "#050510" }}>
      <svg width={width} height={height}>
        <path d={makePath(6, 80, 0.08, 0)} fill="none" stroke="#D4A53744" strokeWidth={20} />
        <path d={makePath(6, 80, 0.08, 0)} fill="none" stroke="#D4A537" strokeWidth={2} />
        <path d={makePath(4, 60, 0.06, 2)} fill="none" stroke="#6366f144" strokeWidth={12} />
        <path d={makePath(4, 60, 0.06, 2)} fill="none" stroke="#6366f1" strokeWidth={2} />
      </svg>
    </AbsoluteFill>
  );
};

// --- B-ROLL: Dashboard ---
const DashboardBRoll: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
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
      <div style={{
        position: "absolute", top: "25%",
        fontSize: 28, fontWeight: 300, color: "#64748b",
        fontFamily: FONT, letterSpacing: "0.1em", textTransform: "uppercase",
        opacity: spring({ frame, fps, config: { damping: 15, stiffness: 80 } }),
      }}>
        Performance Vergleich
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 40, width: "80%", marginTop: 40 }}>
        {bars.map((bar, i) => {
          const p = spring({
            frame: Math.max(0, frame - i * 8), fps,
            config: { damping: 12, stiffness: 60 },
          });
          return (
            <div key={i}>
              <div style={{ fontSize: 22, fontWeight: 400, color: "#94a3b8", marginBottom: 10, fontFamily: FONT, opacity: p }}>
                {bar.label}
              </div>
              <div style={{ height: 36, borderRadius: 8, backgroundColor: "#1e293b", overflow: "hidden" }}>
                <div style={{
                  height: "100%", width: `${bar.value * p}%`,
                  backgroundColor: bar.color, borderRadius: 8,
                  display: "flex", alignItems: "center", justifyContent: "flex-end", paddingRight: 12,
                }}>
                  <span style={{ fontSize: 18, fontWeight: 700, color: "#fff", fontFamily: FONT }}>
                    {Math.round(bar.value * p)}%
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

// --- B-ROLL: CRM Flow ---
const CRMFlowBRoll: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const steps = [
    { icon: "📊", label: "CRM Daten" },
    { icon: "⚡", label: "Signal" },
    { icon: "🎯", label: "Algorithmus" },
    { icon: "📈", label: "Performance" },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: "#050510", justifyContent: "center", alignItems: "center" }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 30 }}>
        {steps.map((step, i) => {
          const p = spring({
            frame: Math.max(0, frame - i * 6), fps,
            config: { damping: 15, stiffness: 150 },
          });
          return (
            <React.Fragment key={i}>
              <div style={{
                display: "flex", alignItems: "center", gap: 16,
                opacity: p, transform: `translateX(${interpolate(p, [0, 1], [-30, 0])}px)`,
              }}>
                <div style={{
                  width: 56, height: 56, borderRadius: 14,
                  backgroundColor: "#1a1a2e", border: "1px solid #D4A53744",
                  display: "flex", justifyContent: "center", alignItems: "center", fontSize: 28,
                }}>
                  {step.icon}
                </div>
                <span style={{ fontSize: 26, fontWeight: 500, color: "#e2e8f0", fontFamily: FONT }}>
                  {step.label}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div style={{ width: 2, height: 20, backgroundColor: "#D4A53744", opacity: p }} />
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
  const progress = spring({ frame, fps, config: { damping: 12, stiffness: 100 } });
  const pulse = Math.sin(frame * 0.15) * 0.3 + 0.7;

  return (
    <div style={{
      position: "absolute", bottom: "12%",
      left: 0, right: 0,
      display: "flex", justifyContent: "center",
      zIndex: 20, opacity: progress,
      transform: `scale(${interpolate(progress, [0, 1], [0.5, 1])})`,
    }}>
      <div style={{
        backgroundColor: "#D4A537", color: "#000",
        fontSize: 32, fontWeight: 800, fontFamily: FONT,
        padding: "18px 48px", borderRadius: 50,
        boxShadow: `0 0 ${20 + pulse * 20}px rgba(212,165,55,${pulse * 0.6})`,
      }}>
        {text}
      </div>
    </div>
  );
};
