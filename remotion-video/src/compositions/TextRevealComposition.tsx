import React from "react";
import { AbsoluteFill } from "remotion";
import { z } from "zod";
import { textRevealSchema } from "../schemas.js";
import { TextReveal } from "../components/text/TextReveal.js";
import { GradientBackground } from "../components/effects/GradientBackground.js";

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
