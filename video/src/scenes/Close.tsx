// Pitch Anything (Klaff): offer the prize, nail the hookpoint, ask for the decision.
import React from "react";
import { AbsoluteFill } from "remotion";

import { CREDITS } from "../assets";
import { Reveal, Scene } from "../components/ui";
import { C, F } from "../theme";

const Gift: React.FC<{ text: string; delay: number }> = ({ text, delay }) => (
  <Reveal delay={delay} x={-30} y={0}>
    <div style={{ borderTop: `2px solid ${C.rule}`, padding: "28px 0" }}>
      <div style={{ fontFamily: F.serif, fontSize: 58, color: C.ink }}>{text}</div>
    </div>
  </Reveal>
);

/** The prize: what a researcher gets for every name. */
export const Prize: React.FC = () => (
  <Scene>
    <AbsoluteFill style={{ padding: "150px 120px 0 120px" }}>
      <Reveal delay={2}>
        <div style={{ fontFamily: F.sans, fontWeight: 600, fontSize: 38, color: C.muted }}>For every one of the 50 names:</div>
      </Reveal>
      <div style={{ marginTop: 26 }}>
        <Gift text="A ranked list of candidate plants, with the evidence" delay={14} />
        <Gift text="How stable that ranking is, not just one label" delay={32} />
        <Gift text="Which compounds hold whichever plant is meant" delay={50} />
        <Gift text="Every number rebuilt with one command" delay={68} />
      </div>
    </AbsoluteFill>
  </Scene>
);

/** Hookpoint and close. */
export const Next: React.FC = () => (
  <Scene fadeOut={1}>
    <AbsoluteFill style={{ padding: "200px 120px 0 120px" }}>
      <Reveal delay={2}>
        <div style={{ fontFamily: F.sans, fontSize: 36, color: C.muted }}>
          Next: all 50 names, scored against the 1,213 expert comparisons, failures included.
        </div>
      </Reveal>
      <Reveal delay={16} y={36}>
        <div style={{ fontFamily: F.serif, fontSize: 150, color: C.ink, marginTop: 40, lineHeight: 1 }}>Materia Incerta</div>
      </Reveal>
      <Reveal delay={30}>
        <div style={{ fontFamily: F.serif, fontStyle: "italic", fontSize: 54, color: C.accent, marginTop: 26 }}>
          Lab time for the compounds that survive identification doubt.
        </div>
      </Reveal>
      <Reveal delay={44}>
        <div style={{ fontFamily: F.mono, fontSize: 28, color: C.ink, marginTop: 60 }}>
          github.com/fozagtx/Materia-Incerta- · EthnoHack 2026
        </div>
      </Reveal>
    </AbsoluteFill>
    <div style={{ position: "absolute", left: 120, right: 120, bottom: 50 }}>
      <Reveal delay={56} y={10}>
        <div style={{ fontFamily: F.sans, fontSize: 18, color: C.muted, lineHeight: 1.55 }}>{CREDITS.join(" · ")}</div>
      </Reveal>
    </div>
  </Scene>
);
