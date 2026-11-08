// Pitch Anything (Klaff): introduce the idea, then prove it with a real run.
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

import { FIBIGIA_FRUIT, FIBIGIA_MODERN_EXCERPT, LIVE, LiveResult, MatchClass, TERMINAL_LINES } from "../assets";
import { Reveal, Scene, Typewriter } from "../components/ui";
import { C, F } from "../theme";

const Pillar: React.FC<{ title: string; body: string; delay: number }> = ({ title, body, delay }) => (
  <Reveal delay={delay} style={{ flex: 1 }}>
    <div style={{ borderTop: `3px solid ${C.ink}`, paddingTop: 22 }}>
      <div style={{ fontFamily: F.sans, fontWeight: 700, fontSize: 40, color: C.ink }}>{title}</div>
      <div style={{ fontFamily: F.sans, fontSize: 28, color: C.muted, marginTop: 10, lineHeight: 1.35 }}>{body}</div>
    </div>
  </Reveal>
);

/** The idea, in Klaff's form: for whom, what it is, unlike what. */
export const Idea: React.FC = () => (
  <Scene>
    <AbsoluteFill style={{ padding: "170px 120px 0 120px" }}>
      <Reveal delay={4}>
        <div style={{ fontFamily: F.sans, fontSize: 34, color: C.muted }}>
          For researchers deciding which historical plants deserve lab work:
        </div>
      </Reveal>
      <Reveal delay={20}>
        <div style={{ fontFamily: F.serif, fontSize: 82, color: C.ink, lineHeight: 1.1, marginTop: 24, maxWidth: 1640 }}>
          <span style={{ color: C.accent }}>Materia Incerta</span> shows how sure an identification is, and which
          compounds survive the doubt.
        </div>
      </Reveal>
      <div style={{ display: "flex", gap: 64, marginTop: 90 }}>
        <Pillar title="Ranking" body="Each candidate scored detail by detail, the way the experts did it" delay={92} />
        <Pillar title="Stability" body="How often that ranking holds when the evidence is resampled" delay={108} />
        <Pillar title="Compounds" body="Which ones hold whichever plant is meant" delay={124} />
      </div>
    </AbsoluteFill>
  </Scene>
);

const Panel: React.FC<{ title: string; children: React.ReactNode; style?: React.CSSProperties; dark?: boolean }> = ({
  title,
  children,
  style,
  dark,
}) => (
  <div
    style={{
      background: dark ? C.term : C.card,
      border: dark ? "none" : `2px solid ${C.rule}`,
      borderRadius: 16,
      padding: "22px 30px",
      ...style,
    }}
  >
    <div style={{ fontFamily: F.sans, fontWeight: 600, fontSize: 21, color: dark ? C.termGreen : C.muted }}>{title}</div>
    <div style={{ marginTop: 12 }}>{children}</div>
  </div>
);

/** Dioscorides' sentence with the plant name swapped out. */
const MaskedGreek: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  const highlight = interpolate(frame, [at - 26, at - 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const swap = interpolate(frame, [at, at + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const rest = LIVE.ancient_sentence.replace(/^ἄλυσσον/, "");
  const line: React.CSSProperties = {
    fontFamily: F.serif,
    fontSize: 38,
    color: C.ink,
    lineHeight: 1.4,
    position: "absolute",
    left: 0,
    top: 0,
    right: 0,
  };
  return (
    <div style={{ position: "relative", height: 112 }}>
      <div style={{ ...line, opacity: 1 - swap }}>
        <span
          style={{
            background: `rgba(155, 44, 31, ${0.16 * highlight})`,
            textDecoration: highlight > 0.5 ? "line-through" : "none",
            textDecorationColor: C.accent,
            textDecorationThickness: 3,
          }}
        >
          ἄλυσσον
        </span>
        {rest}
      </div>
      <div style={{ ...line, opacity: swap }}>
        <span
          style={{
            fontFamily: F.sans,
            fontSize: 28,
            fontWeight: 600,
            color: C.card,
            background: C.accent,
            borderRadius: 6,
            padding: "2px 10px",
          }}
        >
          PLANT
        </span>
        {rest}
      </div>
    </div>
  );
};

/** How it works: hide the name, then ask the model for a verdict with quotes. */
export const HowItWorks: React.FC = () => {
  const answer = JSON.stringify(
    {
      match_class: FIBIGIA_FRUIT.match_class,
      ancient_quote: FIBIGIA_FRUIT.ancient_quote,
      modern_quote: FIBIGIA_FRUIT.modern_quote,
      reason: FIBIGIA_FRUIT.reason,
    },
    null,
    2,
  );
  return (
    <Scene>
      <AbsoluteFill style={{ padding: "100px 120px 0 120px" }}>
        <Reveal delay={4}>
          <div style={{ fontFamily: F.serif, fontSize: 54, color: C.ink }}>First, hide the plant&rsquo;s name.</div>
        </Reveal>
        <Reveal delay={18} style={{ marginTop: 22 }}>
          <Panel title="Dioscorides, De materia medica 3.91, in the original Greek">
            <MaskedGreek at={70} />
          </Panel>
        </Reveal>

        <Reveal delay={150} style={{ marginTop: 40 }}>
          <div style={{ fontFamily: F.serif, fontSize: 54, color: C.ink }}>
            Then compare each detail, and demand a quote from both texts.
          </div>
        </Reveal>
        <div style={{ display: "flex", gap: 32, marginTop: 22 }}>
          <Reveal delay={166} style={{ flex: 0.82 }}>
            <Panel title="Ancient detail: fruit" style={{ height: 160 }}>
              <div style={{ fontFamily: F.serif, fontSize: 36, color: C.ink }}>{FIBIGIA_FRUIT.ancient_greek}</div>
              <div style={{ fontFamily: F.sans, fontSize: 24, color: C.muted, marginTop: 6 }}>
                &ldquo;{FIBIGIA_FRUIT.ancient_gloss}&rdquo;
              </div>
            </Panel>
            <Panel title="Modern flora: Fibigia clypeata" style={{ height: 300, marginTop: 20 }}>
              <div style={{ fontFamily: F.sans, fontSize: 25, color: C.ink, lineHeight: 1.4 }}>{FIBIGIA_MODERN_EXCERPT}</div>
            </Panel>
          </Reveal>
          <Reveal delay={182} style={{ flex: 1.18 }}>
            <Panel dark title={`Live answer · ${LIVE.model.split("/")[1]} on Nebius`} style={{ height: 480, overflow: "hidden" }}>
              <pre
                style={{
                  fontFamily: F.mono,
                  fontSize: 20,
                  color: C.termText,
                  margin: 0,
                  whiteSpace: "pre-wrap",
                  lineHeight: 1.45,
                }}
              >
                <Typewriter text={answer} delay={198} cps={170} cursor />
              </pre>
            </Panel>
          </Reveal>
        </div>
      </AbsoluteFill>
    </Scene>
  );
};

/** The real run, exactly as the script printed it. */
export const LiveRun: React.FC = () => {
  const frame = useCurrentFrame();
  const cmd = "python pipeline/examples/alyssos_live.py";
  const cmdDone = 14 + Math.ceil((cmd.length / 80) * 30);
  const lastLineAt = cmdDone + 8 + (TERMINAL_LINES.length - 1) * 13;
  return (
    <Scene>
      <AbsoluteFill style={{ padding: "110px 120px 0 120px" }}>
        <Reveal delay={0}>
          <div style={{ fontFamily: F.serif, fontSize: 54, color: C.ink }}>Ten comparisons, sent live to the model.</div>
        </Reveal>
        <Reveal delay={6} style={{ marginTop: 28 }}>
          <div style={{ background: C.term, borderRadius: 16, overflow: "hidden", height: 640 }}>
            <div style={{ background: C.termBar, height: 46, display: "flex", alignItems: "center", gap: 10, padding: "0 20px" }}>
              {["#E5534B", "#E3B15B", "#57AB5A"].map((c) => (
                <div key={c} style={{ width: 14, height: 14, borderRadius: 7, background: c }} />
              ))}
              <div style={{ fontFamily: F.mono, fontSize: 18, color: C.termMuted, marginLeft: 14 }}>
                {LIVE.run_at_utc} UTC · {LIVE.model} · Nebius Token Factory
              </div>
            </div>
            <div style={{ padding: "22px 30px", fontFamily: F.mono, fontSize: 23, lineHeight: 1.65, whiteSpace: "pre" }}>
              <div style={{ color: C.termText }}>
                <span style={{ color: C.termAmber }}>$ </span>
                <Typewriter text={cmd} delay={14} cps={80} />
              </div>
              {TERMINAL_LINES.map((l, i) => {
                const at = cmdDone + 8 + i * 13;
                if (frame < at) return null;
                const last = i === TERMINAL_LINES.length - 1;
                const color = last
                  ? C.termGreen
                  : l.includes(" no_match ")
                    ? "#E59A93"
                    : l.includes(" partial ") || l.includes(" good ")
                      ? C.termGreen
                      : C.termMuted;
                return (
                  <div key={i} style={{ color }}>
                    {l}
                  </div>
                );
              })}
            </div>
          </div>
        </Reveal>
        <Reveal delay={lastLineAt + 10}>
          <div style={{ fontFamily: F.sans, fontSize: 30, color: C.muted, marginTop: 26 }}>
            Every answer checked against the schema. Every plant name hidden before sending.
          </div>
        </Reveal>
      </AbsoluteFill>
    </Scene>
  );
};

const CLASS_STYLE: Record<MatchClass, { label: string; color: string }> = {
  good: { label: "Match", color: C.strong },
  partial: { label: "Partial", color: C.moderate },
  no_match: { label: "Conflict", color: C.danger },
  absent: { label: "Not described", color: C.weak },
};

const Verdict: React.FC<{ r: LiveResult; delay: number }> = ({ r, delay }) => {
  const s = CLASS_STYLE[r.match_class];
  const rejected = r.reason.startsWith("[coerced");
  return (
    <Reveal delay={delay} y={12}>
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <span
          style={{
            fontFamily: F.sans,
            fontWeight: 600,
            fontSize: 25,
            color: s.color,
            border: `2px solid ${s.color}`,
            borderRadius: 999,
            padding: "4px 16px",
            background: C.card,
            whiteSpace: "nowrap",
          }}
        >
          {s.label}
        </span>
        <span style={{ fontFamily: F.sans, fontSize: 22, color: C.muted, lineHeight: 1.25 }}>
          {rejected ? "claimed partial, but its quote wasn't in the text" : r.modern_quote ? `“${r.modern_quote}”` : ""}
        </span>
      </div>
    </Reveal>
  );
};

/** What the model found, as a real evidence matrix. */
export const Result: React.FC = () => {
  const cats = ["habit", "leaves", "fruit", "seed", "habitat"];
  const get = (cand: string, cat: string) => LIVE.results.find((r) => r.candidate === cand && r.category === cat)!;
  const tally = (cand: string) => {
    const rs = LIVE.results.filter((r) => r.candidate === cand);
    const pos = rs.filter((r) => r.match_class === "good" || r.match_class === "partial").length;
    const neg = rs.filter((r) => r.match_class === "no_match").length;
    return { pos, neg };
  };
  const say = (t: { pos: number; neg: number }) =>
    `${t.pos} ${t.pos === 1 ? "fits" : "fit"} in part, ${t.neg} ${t.neg === 1 ? "conflict" : "conflicts"}`;
  const fib = tally("Fibigia clypeata");
  const scu = tally("Scutellaria galericulata");
  const cell: React.CSSProperties = { borderTop: `2px solid ${C.rule}`, padding: "16px 0" };
  return (
    <Scene>
      <AbsoluteFill style={{ padding: "96px 120px 0 120px" }}>
        <Reveal delay={0}>
          <div style={{ fontFamily: F.serif, fontSize: 54, color: C.ink }}>What the model found, detail by detail.</div>
        </Reveal>
        <div style={{ marginTop: 26, display: "grid", gridTemplateColumns: "470px 1fr 1fr", columnGap: 40 }}>
          <div />
          <Reveal delay={8}>
            <div style={{ fontFamily: F.serif, fontStyle: "italic", fontSize: 40, color: C.ink, paddingBottom: 12 }}>
              Fibigia clypeata
            </div>
          </Reveal>
          <Reveal delay={8}>
            <div style={{ fontFamily: F.serif, fontStyle: "italic", fontSize: 40, color: C.ink, paddingBottom: 12 }}>
              Scutellaria galericulata
            </div>
          </Reveal>
          {cats.map((cat, i) => {
            const f = get("Fibigia clypeata", cat);
            const s = get("Scutellaria galericulata", cat);
            const d = 18 + i * 22;
            return (
              <React.Fragment key={cat}>
                <Reveal delay={d} style={cell}>
                  <div style={{ fontFamily: F.serif, fontSize: 31, color: C.ink }}>{f.ancient_greek}</div>
                  <div style={{ fontFamily: F.sans, fontSize: 21, color: C.muted, marginTop: 2 }}>{f.ancient_gloss}</div>
                </Reveal>
                <div style={{ ...cell, paddingTop: 20 }}>
                  <Verdict r={f} delay={d + 8} />
                </div>
                <div style={{ ...cell, paddingTop: 20 }}>
                  <Verdict r={s} delay={d + 12} />
                </div>
              </React.Fragment>
            );
          })}
          <div style={{ borderTop: `3px solid ${C.ink}` }} />
          <Reveal delay={150} style={{ borderTop: `3px solid ${C.ink}`, paddingTop: 16 }}>
            <div style={{ fontFamily: F.sans, fontWeight: 700, fontSize: 32, color: C.strong }}>
              {say(fib)}
            </div>
          </Reveal>
          <Reveal delay={156} style={{ borderTop: `3px solid ${C.ink}`, paddingTop: 16 }}>
            <div style={{ fontFamily: F.sans, fontWeight: 700, fontSize: 32, color: C.danger }}>
              {say(scu)}
            </div>
          </Reveal>
        </div>
        <Reveal delay={186}>
          <div style={{ fontFamily: F.serif, fontSize: 46, color: C.ink, marginTop: 34 }}>
            Blind to the names, the model points the same way as the experts.
          </div>
        </Reveal>
      </AbsoluteFill>
    </Scene>
  );
};
