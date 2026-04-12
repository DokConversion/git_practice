import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { mainSchema } from "../schemas.js";
import { TextReveal } from "../components/text/TextReveal.js";
import { LowerThird } from "../components/overlays/LowerThird.js";
import { ParticleBackground } from "../components/effects/ParticleBackground.js";
import { GradientBackground } from "../components/effects/GradientBackground.js";

/**
 * Hauptkomposition: Demonstriert alle Faehigkeiten in einem zusammenhaengenden Video.
 */

export const MainComposition: React.FC<z.infer<typeof mainSchema>> = ({
  title,
  subtitle,
  primaryColor,
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f172a" }}>
      {/* === SZENE 1: Intro mit Partikeln (0-5s) === */}
      <Sequence from={0} durationInFrames={5 * fps}>
        <AbsoluteFill>
          <GradientBackground
            colors={["#0f172a", "#1e1b4b", "#312e81"]}
            speed={0.3}
            type="radial"
          />
          <ParticleBackground
            count={60}
            color={primaryColor}
            connected={true}
            connectionDistance={120}
          />
          <AbsoluteFill
            style={{
              justifyContent: "center",
              alignItems: "center",
              flexDirection: "column",
              gap: 20,
            }}
          >
            <TextReveal
              text={title}
              fontSize={100}
              variant="blur"
              color="#ffffff"
            />
            <Sequence from={15}>
              <TextReveal
                text={subtitle}
                fontSize={36}
                variant="slide-up"
                color="#94a3b8"
                fontWeight={400}
              />
            </Sequence>
          </AbsoluteFill>
        </AbsoluteFill>
      </Sequence>

      {/* === SZENE 2: Feature Showcase (5-12s) === */}
      <Sequence from={5 * fps} durationInFrames={7 * fps}>
        <AbsoluteFill>
          <GradientBackground
            colors={["#1e1b4b", "#312e81", "#4338ca"]}
            speed={0.2}
            type="linear"
          />
          <AbsoluteFill
            style={{
              justifyContent: "center",
              alignItems: "center",
              flexDirection: "column",
              gap: 40,
            }}
          >
            <TextReveal
              text="Professionelle Videos"
              fontSize={72}
              variant="letter-by-letter"
              color="#ffffff"
            />
            <Sequence from={30}>
              <TextReveal
                text="mit React & TypeScript"
                fontSize={48}
                variant="typewriter"
                color={accentColor}
                fontWeight={500}
              />
            </Sequence>
          </AbsoluteFill>
          <Sequence from={20}>
            <LowerThird
              title="Powered by Remotion"
              subtitle="React-basierte Video-Engine"
              accentColor={primaryColor}
              variant="modern"
            />
          </Sequence>
        </AbsoluteFill>
      </Sequence>

      {/* === SZENE 3: Glitch-Text Demo (12-18s) === */}
      <Sequence from={12 * fps} durationInFrames={6 * fps}>
        <AbsoluteFill style={{ backgroundColor: "#0a0a0a" }}>
          <AbsoluteFill
            style={{
              justifyContent: "center",
              alignItems: "center",
              flexDirection: "column",
              gap: 30,
            }}
          >
            <TextReveal
              text="NEXT LEVEL"
              fontSize={120}
              variant="glitch"
              color="#00ff88"
              fontWeight={900}
            />
            <Sequence from={20}>
              <TextReveal
                text="Video Production"
                fontSize={48}
                variant="blur"
                color="#ffffff"
              />
            </Sequence>
          </AbsoluteFill>
          <Sequence from={15}>
            <LowerThird
              title="RGB Glitch Effect"
              subtitle="Inspiriert von remocn.dev"
              accentColor="#00ff88"
              variant="broadcast"
            />
          </Sequence>
        </AbsoluteFill>
      </Sequence>

      {/* === SZENE 4: Broadcast Lower Third (18-24s) === */}
      <Sequence from={18 * fps} durationInFrames={6 * fps}>
        <AbsoluteFill>
          <GradientBackground
            colors={["#0f172a", "#1e293b", "#334155"]}
            speed={0.1}
            type="conic"
          />
          <ParticleBackground count={30} color={accentColor} speed={0.5} />
          <AbsoluteFill
            style={{
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <TextReveal
              text="Dein Video. Dein Code."
              fontSize={80}
              variant="slide-up"
              color="#ffffff"
            />
          </AbsoluteFill>
          <Sequence from={10}>
            <LowerThird
              title="Broadcast Quality"
              subtitle="Professionelle Overlays & Effekte"
              accentColor={accentColor}
              variant="minimal"
            />
          </Sequence>
        </AbsoluteFill>
      </Sequence>

      {/* === SZENE 5: Outro (24-30s) === */}
      <Sequence from={24 * fps} durationInFrames={6 * fps}>
        <AbsoluteFill>
          <GradientBackground
            colors={[primaryColor, "#7c3aed", accentColor]}
            speed={0.5}
            type="radial"
          />
          <AbsoluteFill
            style={{
              justifyContent: "center",
              alignItems: "center",
              flexDirection: "column",
              gap: 24,
            }}
          >
            <TextReveal
              text={title}
              fontSize={90}
              variant="blur"
              color="#ffffff"
            />
            <Sequence from={15}>
              <div
                style={{
                  fontSize: 28,
                  color: "rgba(255,255,255,0.7)",
                  fontFamily: "Inter, system-ui, sans-serif",
                  fontWeight: 400,
                }}
              >
                Erstellt mit Remotion + React
              </div>
            </Sequence>
          </AbsoluteFill>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
