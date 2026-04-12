import React from "react";
import { AbsoluteFill } from "remotion";
import { z } from "zod";
import { textRevealSchema } from "../schemas";
import { TextReveal } from "../components/text/TextReveal";
import { GradientBackground } from "../components/effects/GradientBackground";

export const TextRevealComposition: React.FC<
  z.infer<typeof textRevealSchema>
> = ({ text, fontSize, color, backgroundColor }) => {
  return (
    <AbsoluteFill style={{ backgroundColor }}>
      <GradientBackground
        colors={[backgroundColor, "#1e1b4b", backgroundColor]}
        speed={0.2}
      />
      <AbsoluteFill
        style={{ justifyContent: "center", alignItems: "center" }}
      >
        <TextReveal
          text={text}
          fontSize={fontSize}
          color={color}
          variant="blur"
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
