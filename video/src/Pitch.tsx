import React, { useEffect, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, Series } from "remotion";

import { fontsReady } from "./fonts";
import { Next, Prize } from "./scenes/Close";
import { HowItWorks, Idea, LiveRun, Result } from "./scenes/Demo";
import { Question, Stakes, Twist } from "./scenes/Opening";
import { C, SCENES } from "./theme";

const COMPONENTS: Record<(typeof SCENES)[number]["id"], React.FC> = {
  question: Question,
  stakes: Stakes,
  twist: Twist,
  idea: Idea,
  how: HowItWorks,
  live: LiveRun,
  result: Result,
  prize: Prize,
  next: Next,
};

export const Pitch: React.FC = () => {
  const [handle] = useState(() => delayRender("Loading fonts"));
  useEffect(() => {
    fontsReady
      .then(() => continueRender(handle))
      .catch((e) => {
        console.error(e);
        continueRender(handle);
      });
  }, [handle]);
  return (
    <AbsoluteFill style={{ background: C.paper }}>
      <Series>
        {SCENES.map((s) => {
          const Comp = COMPONENTS[s.id];
          return (
            <Series.Sequence key={s.id} durationInFrames={s.frames}>
              <Comp />
            </Series.Sequence>
          );
        })}
      </Series>
    </AbsoluteFill>
  );
};
