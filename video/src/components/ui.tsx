import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

import { C, F } from "../theme";

const ease = Easing.bezier(0.22, 1, 0.36, 1);

/** Fade + rise in at `delay` frames. */
export const Reveal: React.FC<{
  delay?: number;
  duration?: number;
  y?: number;
  x?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ delay = 0, duration = 18, y = 28, x = 0, children, style }) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame - delay, [0, duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  });
  return (
    <div style={{ opacity: t, transform: `translate(${(1 - t) * x}px, ${(1 - t) * y}px)`, ...style }}>
      {children}
    </div>
  );
};

/** Scene wrapper: flat paper background and a short fade at both ends. */
export const Scene: React.FC<{
  children: React.ReactNode;
  background?: string;
  fadeIn?: number;
  fadeOut?: number;
}> = ({ children, background = C.paper, fadeIn = 8, fadeOut = 10 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const opacity = Math.min(
    interpolate(frame, [0, fadeIn], [0, 1], { extrapolateRight: "clamp" }),
    interpolate(frame, [durationInFrames - fadeOut, durationInFrames], [1, 0], { extrapolateLeft: "clamp" }),
  );
  return (
    <AbsoluteFill style={{ background, opacity }}>
      {children}
    </AbsoluteFill>
  );
};

/** Characters appear one by one starting at `delay`. */
export const Typewriter: React.FC<{
  text: string;
  delay?: number;
  cps?: number;
  style?: React.CSSProperties;
  cursor?: boolean;
}> = ({ text, delay = 0, cps = 40, style, cursor = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const shown = Math.max(0, Math.min(text.length, Math.floor(((frame - delay) / fps) * cps)));
  const done = shown >= text.length;
  return (
    <span style={style}>
      {text.slice(0, shown)}
      {cursor && !done && frame >= delay ? <span style={{ opacity: 0.6 }}>▍</span> : null}
    </span>
  );
};

/** Animated integer with thousands separators. */
export const Counter: React.FC<{ to: number; delay?: number; duration?: number }> = ({
  to,
  delay = 0,
  duration = 30,
}) => {
  const frame = useCurrentFrame();
  const v = interpolate(frame - delay, [0, duration], [0, to], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  return <>{Math.round(v).toLocaleString("en-US")}</>;
};

/** Slow push-in on a still image. */
export const KenBurns: React.FC<{
  src: string;
  from?: number;
  to?: number;
  origin?: string;
  style?: React.CSSProperties;
}> = ({ src, from = 1.0, to = 1.08, origin = "50% 50%", style }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const s = interpolate(frame, [0, durationInFrames], [from, to]);
  return (
    <div style={{ overflow: "hidden", ...style }}>
      <Img
        src={src}
        style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${s})`, transformOrigin: origin }}
      />
    </div>
  );
};

/** Small uppercase line used for kickers and credits. */
export const Kicker: React.FC<{ children: React.ReactNode; color?: string; style?: React.CSSProperties }> = ({
  children,
  color = C.muted,
  style,
}) => (
  <div
    style={{
      fontFamily: F.mono,
      fontSize: 22,
      letterSpacing: 2.5,
      textTransform: "uppercase",
      color,
      ...style,
    }}
  >
    {children}
  </div>
);

export const Credit: React.FC<{ children: React.ReactNode; style?: React.CSSProperties; light?: boolean }> = ({
  children,
  style,
  light,
}) => (
  <div style={{ fontFamily: F.sans, fontSize: 17, color: light ? "#F3EFE6" : C.muted, ...style }}>{children}</div>
);

/** Flat pill. */
export const Chip: React.FC<{ children: React.ReactNode; color: string; style?: React.CSSProperties }> = ({
  children,
  color,
  style,
}) => (
  <span
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 10,
      padding: "8px 18px",
      borderRadius: 999,
      border: `2px solid ${color}`,
      color,
      fontFamily: F.sans,
      fontWeight: 600,
      fontSize: 26,
      background: C.card,
      ...style,
    }}
  >
    {children}
  </span>
);

/** Horizontal share bar, solid fill. */
export const Bar: React.FC<{ value: number; delay?: number; color?: string; width?: number; label: string }> = ({
  value,
  delay = 0,
  color = C.teal,
  width = 420,
  label,
}) => {
  const frame = useCurrentFrame();
  const v = interpolate(frame - delay, [0, 24], [0, value], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  });
  return (
    <div style={{ width }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: F.sans, fontSize: 22, color: C.muted }}>
        <span>{label}</span>
        <span style={{ fontVariantNumeric: "tabular-nums", color: C.ink, fontWeight: 600 }}>{Math.round(v * 100)}%</span>
      </div>
      <div style={{ height: 12, background: C.paperDeep, borderRadius: 6, marginTop: 8 }}>
        <div style={{ height: 12, width: `${v * 100}%`, background: color, borderRadius: 6 }} />
      </div>
    </div>
  );
};
