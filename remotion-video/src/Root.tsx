import React from "react";
import { Composition } from "remotion";
import {
  mainSchema,
  textRevealSchema,
  kenBurnsSchema,
  splitScreenSchema,
  audioVisualizerSchema,
} from "./schemas.js";
import { MainComposition } from "./compositions/MainComposition.js";
import { TextRevealComposition } from "./compositions/TextRevealComposition.js";
import { KenBurnsComposition } from "./compositions/KenBurnsComposition.js";
import { SplitScreenComposition } from "./compositions/SplitScreenComposition.js";
import { AudioVisualizerComposition } from "./compositions/AudioVisualizerComposition.js";

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
    </>
  );
};
