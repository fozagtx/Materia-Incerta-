// Pitch Anything (Klaff): set the frame, tell the story, reveal the intrigue.
import React from "react";
import { AbsoluteFill, Img } from "remotion";

import { IMG } from "../assets";
import { Chip, Counter, KenBurns, Reveal, Scene } from "../components/ui";
import { C, F } from "../theme";

/** The question: a real manuscript and one plant name. */
export const Question: React.FC = () => (
  <Scene>
    <AbsoluteFill style={{ flexDirection: "row" }}>
      <div style={{ flex: 1.15, padding: "230px 0 0 120px" }}>
        <Reveal delay={6}>
          <div style={{ fontFamily: F.sans, fontSize: 34, color: C.muted }}>Byzantium, 13th century.</div>
        </Reveal>
        <Reveal delay={22}>
          <div style={{ fontFamily: F.serif, fontSize: 62, color: C.ink, marginTop: 26, lineHeight: 1.15 }}>
            A physician&rsquo;s handbook prescribes
          </div>
        </Reveal>
        <Reveal delay={48} y={40}>
          <div style={{ fontFamily: F.serif, fontSize: 190, color: C.ink, lineHeight: 1.05, marginTop: 10 }}>ἄλυσσον</div>
        </Reveal>
        <Reveal delay={62}>
          <div style={{ fontFamily: F.serif, fontStyle: "italic", fontSize: 50, color: C.muted }}>alyssos</div>
        </Reveal>
        <Reveal delay={112} y={20}>
          <div style={{ fontFamily: F.sans, fontWeight: 700, fontSize: 76, color: C.accent, marginTop: 70 }}>
            Which plant is that?
          </div>
        </Reveal>
      </div>
      <div style={{ flex: 0.85, position: "relative" }}>
        <KenBurns src={IMG.folio} from={1.04} to={1.14} origin="50% 35%" style={{ position: "absolute", inset: 0 }} />
      </div>
    </AbsoluteFill>
  </Scene>
);

const Stat: React.FC<{ n: number; label: string; delay: number }> = ({ n, label, delay }) => (
  <Reveal delay={delay} style={{ flex: 1 }}>
    <div style={{ borderTop: `3px solid ${C.ink}`, paddingTop: 22 }}>
      <div style={{ fontFamily: F.serif, fontSize: 150, lineHeight: 1, color: C.ink, fontVariantNumeric: "tabular-nums" }}>
        <Counter to={n} delay={delay} duration={34} />
      </div>
      <div style={{ fontFamily: F.sans, fontSize: 32, color: C.muted, marginTop: 14 }}>{label}</div>
    </div>
  </Reveal>
);

/** The stakes: the cost of a wrong answer, and a published test done by hand. */
export const Stakes: React.FC = () => (
  <Scene>
    <AbsoluteFill style={{ padding: "150px 120px 0 120px" }}>
      <Reveal delay={4}>
        <div style={{ fontFamily: F.serif, fontSize: 74, color: C.ink, lineHeight: 1.12, maxWidth: 1500 }}>
          Modern readings of these names rest on dictionaries that disagree.
        </div>
      </Reveal>
      <Reveal delay={50}>
        <div style={{ fontFamily: F.sans, fontWeight: 600, fontSize: 42, color: C.accent, marginTop: 34 }}>
          Pick the wrong plant, and the lab tests the wrong species.
        </div>
      </Reveal>
      <Reveal delay={104}>
        <div style={{ fontFamily: F.sans, fontSize: 32, color: C.muted, marginTop: 92 }}>
          In 2024, Lardos et al. published a systematic test, done entirely by hand:
        </div>
      </Reveal>
      <div style={{ display: "flex", gap: 80, marginTop: 34 }}>
        <Stat n={50} label="historical drug names" delay={120} />
        <Stat n={141} label="candidate species" delay={136} />
        <Stat n={1213} label="feature comparisons by experts" delay={152} />
      </div>
      <Reveal delay={226}>
        <div style={{ fontFamily: F.serif, fontStyle: "italic", fontSize: 50, color: C.ink, marginTop: 64 }}>
          One label per candidate, and no way to tell how fragile it is.
        </div>
      </Reveal>
    </AbsoluteFill>
  </Scene>
);

const PlantCard: React.FC<{
  name: string;
  img: string;
  position?: string;
  fit: "Strong" | "Weak";
  uses: string;
  delay: number;
}> = ({ name, img, position = "50% 50%", fit, uses, delay }) => (
  <Reveal delay={delay} style={{ flex: 1 }}>
    <div style={{ background: C.card, border: `2px solid ${C.rule}`, borderRadius: 18, overflow: "hidden" }}>
      <div style={{ height: 390 }}>
        <Img src={img} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: position }} />
      </div>
      <div style={{ padding: "28px 36px 34px" }}>
        <div style={{ fontFamily: F.serif, fontStyle: "italic", fontSize: 56, color: C.ink }}>{name}</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 22 }}>
          <span style={{ fontFamily: F.sans, fontSize: 29, color: C.muted }}>Fits Dioscorides&rsquo; description</span>
          <Chip color={fit === "Strong" ? C.strong : C.weak}>{fit}</Chip>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 18 }}>
          <span style={{ fontFamily: F.sans, fontSize: 29, color: C.muted }}>Known medicinal use</span>
          <span style={{ fontFamily: F.sans, fontSize: 29, fontWeight: 600, color: C.ink }}>{uses}</span>
        </div>
      </div>
    </div>
  </Reveal>
);

/** The twist: choosing by medicinal use picks the plant that fits the text worse. */
export const Twist: React.FC = () => (
  <Scene>
    <AbsoluteFill style={{ padding: "110px 120px 0 120px" }}>
      <Reveal delay={4}>
        <div style={{ fontFamily: F.serif, fontSize: 58, color: C.ink }}>
          Two candidates for <span style={{ fontStyle: "italic" }}>alyssos</span>, as the experts scored them:
        </div>
      </Reveal>
      <div style={{ display: "flex", gap: 56, marginTop: 34 }}>
        <PlantCard name="Fibigia clypeata" img={IMG.fibigia} fit="Strong" uses="none found" delay={18} />
        <PlantCard
          name="Scutellaria galericulata"
          img={IMG.scutellaria}
          position="50% 24%"
          fit="Weak"
          uses="yes"
          delay={44}
        />
      </div>
      <Reveal delay={140}>
        <div style={{ fontFamily: F.serif, fontSize: 56, color: C.ink, marginTop: 46, lineHeight: 1.15 }}>
          Choose the plant with a known use, and you choose the one that{" "}
          <span style={{ color: C.accent }}>fits Dioscorides less well</span>.
        </div>
      </Reveal>
    </AbsoluteFill>
  </Scene>
);
