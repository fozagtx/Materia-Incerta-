// Flat colours only. No gradients anywhere in this video.
export const C = {
  paper: "#F3EFE6",
  paperDeep: "#E9E3D6",
  card: "#FBF9F4",
  ink: "#16140F",
  muted: "#6E685C",
  rule: "#D6CEBD",
  accent: "#9B2C1F", // oxblood
  teal: "#1E5B57",
  strong: "#2F7A4D",
  moderate: "#A86F0C",
  weak: "#7A7468",
  danger: "#B3261E",
  term: "#121212",
  termBar: "#1E1E1E",
  termText: "#E8E6E1",
  termMuted: "#8C8A85",
  termGreen: "#86C98A",
  termAmber: "#E3B15B",
} as const;

export const F = {
  serif: "'EB Garamond', Georgia, serif",
  sans: "'Inter', system-ui, sans-serif",
  mono: "'JetBrains Mono', ui-monospace, monospace",
} as const;

export const FPS = 30;
export const W = 1920;
export const H = 1080;

// Scene lengths in frames (30 fps). Total = 2700 = 90 s.
// Order follows Klaff's Pitch Anything: frame, story, intrigue, idea, proof, prize, hookpoint.
export const SCENES = [
  { id: "question", frames: 240 },
  { id: "stakes", frames: 330 },
  { id: "twist", frames: 300 },
  { id: "idea", frames: 240 },
  { id: "how", frames: 420 },
  { id: "live", frames: 330 },
  { id: "result", frames: 330 },
  { id: "prize", frames: 240 },
  { id: "next", frames: 270 },
] as const;

export const TOTAL = SCENES.reduce((n, s) => n + s.frames, 0);
