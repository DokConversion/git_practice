/**
 * Professionelle Farbpaletten fuer Video-Produktionen.
 */

export const PALETTES = {
  modern: {
    primary: "#6366f1",
    secondary: "#8b5cf6",
    accent: "#f59e0b",
    background: "#0f172a",
    surface: "#1e293b",
    text: "#f8fafc",
    textMuted: "#94a3b8",
  },
  minimal: {
    primary: "#18181b",
    secondary: "#3f3f46",
    accent: "#ef4444",
    background: "#ffffff",
    surface: "#f4f4f5",
    text: "#18181b",
    textMuted: "#71717a",
  },
  neon: {
    primary: "#00ff88",
    secondary: "#00ccff",
    accent: "#ff00ff",
    background: "#0a0a0a",
    surface: "#1a1a2e",
    text: "#ffffff",
    textMuted: "#888888",
  },
  warm: {
    primary: "#f97316",
    secondary: "#ef4444",
    accent: "#eab308",
    background: "#1c1917",
    surface: "#292524",
    text: "#fafaf9",
    textMuted: "#a8a29e",
  },
  corporate: {
    primary: "#2563eb",
    secondary: "#0891b2",
    accent: "#16a34a",
    background: "#ffffff",
    surface: "#f1f5f9",
    text: "#0f172a",
    textMuted: "#64748b",
  },
} as const;

export type PaletteName = keyof typeof PALETTES;

export function hexToRgba(hex: string, alpha: number = 1): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export function gradientFromPalette(
  palette: PaletteName,
  angle: number = 135
): string {
  const p = PALETTES[palette];
  return `linear-gradient(${angle}deg, ${p.primary}, ${p.secondary})`;
}
