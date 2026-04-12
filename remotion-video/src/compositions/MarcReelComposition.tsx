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
 * Marc's Signal Marketing Reel - V4 (Sync Fix)
 *
 * EXAKTE Whisper-Timestamps:
 * [00:00.000 --> 00:06.800] Segment 1: "Der Hauptgrund... Signal Marketing in 2026"
 * [00:07.180 --> 00:16.220] Segment 2: "Die meisten versuchen... statt auf Signale"
 * [00:16.680 --> 00:23.660] Segment 3: "Wenn du den Unterschied... bessere Ergebnisse"
 * [00:23.660 --> 00:36.600] Segment 4: "Lasst mich erklaeren... CRM... Algorithmus"
 * [00:37.040 --> 00:42.040] Segment 5: "Live-Webinar, meld dich an"
 */

export const MarcReelComposition: React.FC<
  z.infer<typeof marcReelSchema>
> = ({ videoFile }) => {
  // Helper: Sekunden -> Frames
  const f = (seconds: number) => Math.round(seconds * 30);

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000", fontFamily: FONT }}>

      {/* VIDEO - laeuft DURCHGEHEND */}
      <OffthreadVideo
        src={staticFile(videoFile)}
        muted
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
      {/* Vignette */}
      <AbsoluteFill style={{
        background: "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.5) 100%)",
        pointerEvents: "none",
      }} />
      <AbsoluteFill style={{
        background: "linear-gradient(to top, rgba(0,0,0,0.75) 0%, transparent 35%)",
        pointerEvents: "none",
      }} />

      {/* AUDIO - laeuft DURCHGEHEND */}
      <Audio src={staticFile(videoFile)} volume={1} />

      {/* ============================================ */}
      {/* SEGMENT 1: 0:00 - 0:06.8                    */}
      {/* "Der Hauptgrund warum deine Funnels nicht    */}
      {/*  performen liegt daran dass du nicht         */}
      {/*  verstanden hast dass Signal Marketing      */}
      {/*  in 2026 zaehlt"                            */}
      {/* ============================================ */}

      {/* Text-Overlay: 0:00 - 0:02.5 */}
      <Sequence from={f(0)} durationInFrames={f(2.5)}>
        <FadeOverlay>
          <AnimatedGradientBg colors={["#0a0a0a", "#1a0a2e", "#0a0a0a"]} />
          <CenterContent>
            <AnimatedWords words={[
              { text: "Der Hauptgrund", delay: 0 },
              { text: "warum deine Funnels", delay: 6 },
              { text: "nicht performen", delay: 14, highlight: true },
            ]} />
          </CenterContent>
        </FadeOverlay>
      </Sequence>

      {/* Captions: 0:02.5 - 0:06.8 */}
      <Sequence from={f(2.5)} durationInFrames={f(4.3)}>
        <CaptionOverlay words={[
          { text: "liegt daran", start: 0, end: f(0.9) },
          { text: "dass du nicht", start: f(0.9), end: f(1.8) },
          { text: "verstanden hast", start: f(1.8), end: f(2.7) },
          { text: "Signal Marketing", start: f(2.7), end: f(3.6), highlight: true },
          { text: "in 2026 zaehlt", start: f(3.6), end: f(4.3), highlight: true },
        ]} />
      </Sequence>

      {/* ============================================ */}
      {/* PAUSE + B-ROLL: 0:06.8 - 0:08.5             */}
      {/* (kurze Pause zwischen Segment 1 und 2)       */}
      {/* ============================================ */}
      <Sequence from={f(6.8)} durationInFrames={f(1.7)}>
        <FadeOverlay>
          <SignalWaveBRoll />
          <CenterContent>
            <AnimatedWords words={[
              { text: "Signal Marketing", delay: 0, highlight: true },
              { text: "> Events", delay: 8 },
            ]} size={64} />
          </CenterContent>
        </FadeOverlay>
      </Sequence>

      {/* ============================================ */}
      {/* SEGMENT 2: 0:07.18 - 0:16.22                */}
      {/* "Die meisten versuchen... ihre Kampagnen     */}
      {/*  auf Events zu optimieren statt auf Signale" */}
      {/* ============================================ */}

      {/* Captions: 0:08.5 - 0:16.2 */}
      <Sequence from={f(8.5)} durationInFrames={f(7.7)}>
        <CaptionOverlay words={[
          { text: "die meisten versuchen", start: 0, end: f(1.5) },
          { text: "noch immer", start: f(1.5), end: f(2.5) },
          { text: "ihre Kampagnen", start: f(3), end: f(4.3) },
          { text: "auf Events", start: f(4.3), end: f(5.5) },
          { text: "zu optimieren", start: f(5.5), end: f(6.5) },
          { text: "statt auf Signale", start: f(6.5), end: f(7.7), highlight: true },
        ]} />
      </Sequence>

      {/* ============================================ */}
      {/* B-ROLL: 0:16.2 - 0:17.8                     */}
      {/* (Uebergang zu Segment 3)                     */}
      {/* ============================================ */}
      <Sequence from={f(16.2)} durationInFrames={f(1.6)}>
        <FadeOverlay>
          <DashboardBRoll />
        </FadeOverlay>
      </Sequence>

      {/* ============================================ */}
      {/* SEGMENT 3: 0:16.68 - 0:23.66                */}
      {/* "Wenn du den Unterschied verstehst...        */}
      {/*  bessere Ergebnisse im Performance Marketing"*/}
      {/* ============================================ */}

      {/* Captions: 0:17.8 - 0:23.7 */}
      <Sequence from={f(17.8)} durationInFrames={f(5.9)}>
        <CaptionOverlay words={[
          { text: "wenn du verstanden hast", start: 0, end: f(1.5) },
          { text: "was der Unterschied ist", start: f(1.5), end: f(3), highlight: true },
          { text: "dann wirst du", start: f(3), end: f(4) },
          { text: "deutlich bessere", start: f(4), end: f(5), highlight: true },
          { text: "Ergebnisse sehen", start: f(5), end: f(5.9), highlight: true },
        ]} />
      </Sequence>

      {/* ============================================ */}
      {/* TEXT OVERLAY: 0:23.7 - 0:25.5                */}
      {/* "Lasst mich kurz erklaeren"                  */}
      {/* ============================================ */}
      <Sequence from={f(23.7)} durationInFrames={f(1.8)}>
        <FadeOverlay>
          <AnimatedGradientBg colors={["#0a0a0a", "#0a1628", "#0a0a0a"]} />
          <CenterContent>
            <AnimatedWords words={[
              { text: "Lasst mich", delay: 0 },
              { text: "kurz erklaeren", delay: 8 },
            ]} size={56} />
          </CenterContent>
        </FadeOverlay>
      </Sequence>

      {/* ============================================ */}
      {/* SEGMENT 4: 0:25.5 - 0:36.6                  */}
      {/* "Signale sind Events die tiefer kommen       */}
      {/*  aus einem CRM... Algorithmus..."            */}
      {/* ============================================ */}

      {/* Captions: 0:25.5 - 0:32 */}
      <Sequence from={f(25.5)} durationInFrames={f(6.5)}>
        <CaptionOverlay words={[
          { text: "Signale sind Events", start: 0, end: f(1.5), highlight: true },
          { text: "die deutlich tiefer", start: f(1.5), end: f(3) },
          { text: "kommen", start: f(3), end: f(3.8), highlight: true },
          { text: "aus einem CRM", start: f(3.8), end: f(5.3), highlight: true },
          { text: "der Algorithmus", start: f(5.3), end: f(6.5) },
        ]} />
      </Sequence>

      {/* B-ROLL: 0:32 - 0:34 */}
      <Sequence from={f(32)} durationInFrames={f(2)}>
        <FadeOverlay>
          <CRMFlowBRoll />
        </FadeOverlay>
      </Sequence>

      {/* Captions: 0:34 - 0:37 */}
      <Sequence from={f(34)} durationInFrames={f(3)}>
        <CaptionOverlay words={[
          { text: "kann damit deutlich", start: 0, end: f(1.2) },
          { text: "mehr arbeiten", start: f(1.2), end: f(2.2), highlight: true },
          { text: "als mit klassischen Events", start: f(2.2), end: f(3) },
        ]} />
      </Sequence>

      {/* ============================================ */}
      {/* SEGMENT 5: 0:37.04 - 0:42.04                */}
      {/* "Live-Webinar... meld dich an"               */}
      {/* ============================================ */}
      <Sequence from={f(37)} durationInFrames={f(5)}>
        <CaptionOverlay words={[
          { text: "Wie das geht", start: 0, end: f(1.2) },
          { text: "zeige ich dir", start: f(1.2), end: f(2.2) },
          { text: "im Live-Webinar", start: f(2.2), end: f(3.5), highlight: true },
          { text: "Meld dich jetzt an!", start: f(3.5), end: f(5), highlight: true },
        ]} />
        <Sequence from={f(2.5)}>
          <CTAButton text="Jetzt anmelden" />
        </Sequence>
      </Sequence>

    </AbsoluteFill>
  );
};

// ===========================
// KOMPONENTEN
// ===========================

const FadeOverlay: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const fadeIn = interpolate(frame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: Math.min(fadeIn, fadeOut), zIndex: 5 }}>
      {children}
    </AbsoluteFill>
  );
};

const CenterContent: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "0 60px", zIndex: 10 }}>
    {children}
  </AbsoluteFill>
);

const AnimatedWords: React.FC<{
  words: { text: string; delay: number; highlight?: boolean }[];
  size?: number;
}> = ({ words, size = 58 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
      {words.map((word, i) => {
        const p = spring({ frame: Math.max(0, frame - word.delay), fps, config: { damping: 18, stiffness: 180, mass: 0.5 } });
        return (
          <div key={i} style={{
            fontSize: size, fontWeight: word.highlight ? 700 : 300,
            color: word.highlight ? "#D4A537" : "#ffffff",
            opacity: p, transform: `translateY(${interpolate(p, [0, 1], [25, 0])}px)`,
            fontFamily: FONT, textAlign: "center",
          }}>
            {word.text}
          </div>
        );
      })}
    </div>
  );
};

const CaptionOverlay: React.FC<{
  words: { text: string; start: number; end: number; highlight?: boolean }[];
}> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const current = words.find((w) => frame >= w.start && frame < w.end);
  if (!current) return null;
  const p = spring({ frame: frame - current.start, fps, config: { damping: 22, stiffness: 280, mass: 0.4 } });
  return (
    <div style={{ position: "absolute", top: "58%", left: 0, right: 0, display: "flex", justifyContent: "center", zIndex: 10 }}>
      <div style={{ opacity: p, transform: `scale(${interpolate(p, [0, 1], [0.88, 1])})` }}>
        <span style={{
          fontSize: 46, fontWeight: current.highlight ? 700 : 600,
          color: current.highlight ? "#D4A537" : "#ffffff",
          fontFamily: FONT, textShadow: "0 2px 12px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.6)",
        }}>
          {current.text}
        </span>
      </div>
    </div>
  );
};

const AnimatedGradientBg: React.FC<{ colors: string[] }> = ({ colors }) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{ background: `linear-gradient(${frame * 0.5}deg, ${colors.join(", ")})` }} />;
};

const SignalWaveBRoll: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const makePath = (freq: number, amp: number, speed: number, phase: number) =>
    Array.from({ length: 80 }).map((_, i) => {
      const x = (i / 80) * width;
      const y = height / 2 + Math.sin((i / 80) * freq + frame * speed) * amp + Math.sin((i / 80) * freq * 0.5 + frame * speed * 0.7 + phase) * amp * 0.5;
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

const DashboardBRoll: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bars = [
    { label: "Click Events", value: 35, color: "#ef4444" },
    { label: "Form Submits", value: 52, color: "#f59e0b" },
    { label: "CRM Signale", value: 89, color: "#22c55e" },
  ];
  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0f1a", justifyContent: "center", alignItems: "center", padding: 60 }}>
      <div style={{ position: "absolute", top: "25%", fontSize: 28, fontWeight: 300, color: "#64748b", fontFamily: FONT, letterSpacing: "0.1em", textTransform: "uppercase",
        opacity: spring({ frame, fps, config: { damping: 15, stiffness: 80 } }) }}>
        Performance Vergleich
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 40, width: "80%", marginTop: 40 }}>
        {bars.map((bar, i) => {
          const p = spring({ frame: Math.max(0, frame - i * 6), fps, config: { damping: 12, stiffness: 60 } });
          return (
            <div key={i}>
              <div style={{ fontSize: 22, fontWeight: 400, color: "#94a3b8", marginBottom: 10, fontFamily: FONT, opacity: p }}>{bar.label}</div>
              <div style={{ height: 36, borderRadius: 8, backgroundColor: "#1e293b", overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${bar.value * p}%`, backgroundColor: bar.color, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "flex-end", paddingRight: 12 }}>
                  <span style={{ fontSize: 18, fontWeight: 700, color: "#fff", fontFamily: FONT }}>{Math.round(bar.value * p)}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

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
          const p = spring({ frame: Math.max(0, frame - i * 5), fps, config: { damping: 15, stiffness: 150 } });
          return (
            <React.Fragment key={i}>
              <div style={{ display: "flex", alignItems: "center", gap: 16, opacity: p, transform: `translateX(${interpolate(p, [0, 1], [-30, 0])}px)` }}>
                <div style={{ width: 56, height: 56, borderRadius: 14, backgroundColor: "#1a1a2e", border: "1px solid #D4A53744", display: "flex", justifyContent: "center", alignItems: "center", fontSize: 28 }}>{step.icon}</div>
                <span style={{ fontSize: 26, fontWeight: 500, color: "#e2e8f0", fontFamily: FONT }}>{step.label}</span>
              </div>
              {i < steps.length - 1 && <div style={{ width: 2, height: 20, backgroundColor: "#D4A53744", opacity: p }} />}
            </React.Fragment>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const CTAButton: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame, fps, config: { damping: 12, stiffness: 100 } });
  const pulse = Math.sin(frame * 0.15) * 0.3 + 0.7;
  return (
    <div style={{ position: "absolute", bottom: "12%", left: 0, right: 0, display: "flex", justifyContent: "center", zIndex: 20, opacity: p, transform: `scale(${interpolate(p, [0, 1], [0.5, 1])})` }}>
      <div style={{ backgroundColor: "#D4A537", color: "#000", fontSize: 32, fontWeight: 800, fontFamily: FONT, padding: "18px 48px", borderRadius: 50, boxShadow: `0 0 ${20 + pulse * 20}px rgba(212,165,55,${pulse * 0.6})` }}>
        {text}
      </div>
    </div>
  );
};
