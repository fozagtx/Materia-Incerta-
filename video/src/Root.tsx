import React from "react";
import { Composition } from "remotion";

import { Pitch } from "./Pitch";
import { FPS, H, TOTAL, W } from "./theme";

export const Root: React.FC = () => (
  <Composition id="MateriaIncerta" component={Pitch} durationInFrames={TOTAL} fps={FPS} width={W} height={H} />
);
