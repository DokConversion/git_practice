import React from "react";
import { Composition } from "remotion";
import {
  mainSchema,
  textRevealSchema,
  kenBurnsSchema,
  splitScreenSchema,
  audioVisualizerSchema,
} from "./schemas";
import { MainComposition } from "./compositions/MainComposition";
import { TextRevealComposition } from "./compositions/TextRevealComposition";
import { KenBurnsComposition } from "./compositions/KenBurnsComposition";
import { SplitScreenComposition } from "./compositions/SplitScreenComposition";
import { AudioVisualizerComposition } from "./compositions/AudioVisualizerComposition";
import {
  ValueReelComposition,
  valueReelSchema,
} from "./compositions/ValueReelComposition";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="MainVideo"
        component={MainComposition}
        schema={mainSchema}
        durationInFrames={30 * 30}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Mein Video",
          subtitle: "Erstellt mit Remotion",
          primaryColor: "#6366f1",
          accentColor: "#f59e0b",
        }}
      />

      <Composition
        id="TextReveal"
        component={TextRevealComposition}
        schema={textRevealSchema}
        durationInFrames={5 * 30}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          text: "Willkommen",
          fontSize: 120,
          color: "#ffffff",
          backgroundColor: "#0f172a",
        }}
      />

      <Composition
        id="KenBurns"
        component={KenBurnsComposition}
        schema={kenBurnsSchema}
        durationInFrames={8 * 30}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          zoomStart: 1,
          zoomEnd: 1.3,
          panDirection: "left" as const,
        }}
      />

      <Composition
        id="SplitScreen"
        component={SplitScreenComposition}
        schema={splitScreenSchema}
        durationInFrames={6 * 30}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          splitRatio: 0.5,
          direction: "horizontal" as const,
        }}
      />

      <Composition
        id="AudioVisualizer"
        component={AudioVisualizerComposition}
        schema={audioVisualizerSchema}
        durationInFrames={10 * 30}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          barCount: 64,
          barColor: "#6366f1",
          backgroundColor: "#0f172a",
        }}
      />
      {/* === VALUE REEL (9:16 Instagram Reel - bastianbarami Stil) === */}
      <Composition
        id="ValueReel"
        component={ValueReelComposition}
        schema={valueReelSchema}
        durationInFrames={60 * 30}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          scenes: [
            // Szene 1: Text-on-Black Hook
            {
              type: "text" as const,
              durationInFrames: 3 * 30,
              words: [
                { text: "Stell", startFrame: 0 },
                { text: "dir", startFrame: 8 },
                { text: "vor,", startFrame: 16 },
                { text: "es", startFrame: 28 },
                { text: "ist", startFrame: 34 },
                { text: "2045,", startFrame: 42, highlight: true },
                { text: "20", startFrame: 55, highlight: true },
                { text: "Jahre", startFrame: 62, highlight: true },
              ],
              lineBreakAfter: [2, 4],
            },
            // Szene 2: Talking Head
            {
              type: "talking-head" as const,
              durationInFrames: 7 * 30,
              captions: [
                { text: "als", startFrame: 5, endFrame: 18 },
                { text: "jeder", startFrame: 18, endFrame: 32 },
                { text: "Mensch", startFrame: 32, endFrame: 50 },
                { text: "auf", startFrame: 50, endFrame: 62 },
                { text: "diesem", startFrame: 62, endFrame: 78 },
                { text: "Planeten.", startFrame: 78, endFrame: 100 },
                { text: "Jeder", startFrame: 110, endFrame: 125 },
                { text: "Beruf,", startFrame: 125, endFrame: 145, highlight: true },
                { text: "fuer", startFrame: 145, endFrame: 158 },
                { text: "den", startFrame: 158, endFrame: 170 },
                { text: "kann", startFrame: 175, endFrame: 200 },
              ],
            },
            // Szene 3: Text-on-Black Statement
            {
              type: "text-slide" as const,
              durationInFrames: 3 * 30,
              text: "Mein Kind wird die Faehigkeit haben",
              highlightWords: ["Faehigkeit"],
            },
            // Szene 4: Talking Head
            {
              type: "talking-head" as const,
              durationInFrames: 7 * 30,
              captions: [
                { text: "sich", startFrame: 5, endFrame: 25 },
                { text: "anzupassen", startFrame: 25, endFrame: 55, highlight: true },
                { text: "und", startFrame: 60, endFrame: 75 },
                { text: "zu", startFrame: 75, endFrame: 88 },
                { text: "lernen.", startFrame: 88, endFrame: 120 },
              ],
            },
            // Szene 5: Abschluss Text
            {
              type: "text" as const,
              durationInFrames: 4 * 30,
              words: [
                { text: "Das", startFrame: 0 },
                { text: "ist", startFrame: 10 },
                { text: "die", startFrame: 18 },
                { text: "wichtigste", startFrame: 26, highlight: true },
                { text: "Investition.", startFrame: 40, highlight: true },
              ],
              lineBreakAfter: [2],
            },
          ],
        }}
      />
    </>
  );
};
