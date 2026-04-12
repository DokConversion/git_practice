import React from "react";
import {
  AbsoluteFill,
  Sequence,
  Video,
  Audio,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  OffthreadVideo,
} from "remotion";
import { z } from "zod";
import { WordByWordReveal, TextSlide } from "../components/text/WordByWordReveal";
import { LiveCaption } from "../components/overlays/LiveCaption";

/**
 * Value Reel Composition im bastianbarami-Stil.
 *
 * Struktur:
 *  1. Text-on-Black Hook (Woerter erscheinen einzeln)
 *  2. Talking Head mit Live-Captions
 *  3. Text-on-Black Zwischenstatement
 *  4. Talking Head mit Live-Captions
 *  5. Repeat...
 *
 * Format: 1080x1920 (9:16 Instagram Reel)
 * Pacing: Schnell, ~20 Schnitte/Minute
 */

// --- Schema ---

export const valueReelSchema = z.object({
  /** Scenes: Array von Szenen die das Reel aufbauen */
  scenes: z.array(
    z.discriminatedUnion("type", [
      // Text-on-Black Szene
      z.object({
        type: z.literal("text"),
        durationInFrames: z.number(),
        words: z.array(
          z.object({
            text: z.string(),
            startFrame: z.number(),
            highlight: z.boolean().optional(),
          })
        ),
        lineBreakAfter: z.array(z.number()).optional(),
      }),
      // Talking Head Szene (mit optionalen Captions)
      z.object({
        type: z.literal("talking-head"),
        durationInFrames: z.number(),
        videoSrc: z.string().optional(),
        captions: z
          .array(
            z.object({
              text: z.string(),
              startFrame: z.number(),
              endFrame: z.number(),
              highlight: z.boolean().optional(),
            })
          )
          .optional(),
      }),
      // Text-Slide (ganzer Satz auf einmal)
      z.object({
        type: z.literal("text-slide"),
        durationInFrames: z.number(),
        text: z.string(),
        highlightWords: z.array(z.string()).optional(),
      }),
    ])
  ),
});

type ValueReelProps = z.infer<typeof valueReelSchema>;

export const ValueReelComposition: React.FC<ValueReelProps> = ({
  scenes,
}) => {
  // Berechne Start-Frames fuer jede Szene
  let currentFrame = 0;
  const sceneTimings = scenes.map((scene) => {
    const start = currentFrame;
    currentFrame += scene.durationInFrames;
    return { ...scene, from: start };
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      {sceneTimings.map((scene, i) => (
        <Sequence
          key={i}
          from={scene.from}
          durationInFrames={scene.durationInFrames}
        >
          {scene.type === "text" && (
            <WordByWordReveal
              words={scene.words}
              lineBreakAfter={scene.lineBreakAfter}
              fontSize={64}
              fontFamily="'Georgia', 'Times New Roman', serif"
              highlightColor="#D4A537"
            />
          )}

          {scene.type === "talking-head" && (
            <TalkingHeadScene
              videoSrc={scene.videoSrc}
              captions={scene.captions}
            />
          )}

          {scene.type === "text-slide" && (
            <TextSlide
              text={scene.text}
              highlightWords={scene.highlightWords}
              fontSize={56}
              highlightColor="#D4A537"
            />
          )}
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

// --- Talking Head Scene ---

const TalkingHeadScene: React.FC<{
  videoSrc?: string;
  captions?: {
    text: string;
    startFrame: number;
    endFrame: number;
    highlight?: boolean;
  }[];
}> = ({ videoSrc, captions }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill>
      {/* Video oder Platzhalter */}
      {videoSrc ? (
        <OffthreadVideo
          src={staticFile(videoSrc)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      ) : (
        <AbsoluteFill
          style={{
            background:
              "linear-gradient(180deg, #1a1a1a 0%, #0d0d0d 100%)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <div
            style={{
              width: 120,
              height: 120,
              borderRadius: 60,
              backgroundColor: "#2a2a2a",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <div
              style={{
                fontSize: 48,
                color: "#555",
              }}
            >
              ?
            </div>
          </div>
        </AbsoluteFill>
      )}

      {/* Cinematischer Look: Vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.4) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* Live Captions */}
      {captions && captions.length > 0 && (
        <LiveCaption
          captions={captions}
          fontSize={48}
          positionY={55}
          color="#ffffff"
          highlightColor="#D4A537"
        />
      )}
    </AbsoluteFill>
  );
};
