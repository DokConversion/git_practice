import { z } from "zod";

export const mainSchema = z.object({
  title: z.string(),
  subtitle: z.string(),
  primaryColor: z.string(),
  accentColor: z.string(),
});

export const textRevealSchema = z.object({
  text: z.string(),
  fontSize: z.number(),
  color: z.string(),
  backgroundColor: z.string(),
});

export const kenBurnsSchema = z.object({
  zoomStart: z.number(),
  zoomEnd: z.number(),
  panDirection: z.enum(["left", "right", "up", "down", "center"]),
});

export const splitScreenSchema = z.object({
  splitRatio: z.number(),
  direction: z.enum(["horizontal", "vertical"]),
});

export const audioVisualizerSchema = z.object({
  barCount: z.number(),
  barColor: z.string(),
  backgroundColor: z.string(),
});
