import React from "react";
import { AbsoluteFill } from "remotion";
import { z } from "zod";
import { kenBurnsSchema } from "../schemas";
import { KenBurns } from "../components/effects/KenBurns";

export const KenBurnsComposition: React.FC<
  z.infer<typeof kenBurnsSchema>
> = ({ zoomStart, zoomEnd, panDirection }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#0f172a" }}>
      <KenBurns
        zoomStart={zoomStart}
        zoomEnd={zoomEnd}
        panDirection={panDirection}
      >
        <AbsoluteFill
          style={{
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <div
            style={{
              fontSize: 48,
              color: "white",
              fontFamily: "Inter, system-ui, sans-serif",
              fontWeight: 600,
              textAlign: "center",
              padding: 40,
            }}
          >
            Ken Burns Effekt
            <br />
            <span style={{ fontSize: 24, opacity: 0.7 }}>
              Ersetze dies mit einem Bild oder Video
            </span>
          </div>
        </AbsoluteFill>
      </KenBurns>
    </AbsoluteFill>
  );
};
