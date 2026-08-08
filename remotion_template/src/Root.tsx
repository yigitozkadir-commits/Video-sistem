import React from "react";
import { Composition } from "remotion";
import { StudioComposition } from "./compositions/StudioComposition";
import { TOTAL_FRAMES, FPS } from "./scenesData";

// Rename the composition id + component per project once copied
// (remotion_<project_id>/src/Root.tsx) - keep the id in sync with
// package.json's "render" script and any CI matrix entry that targets it.
export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="studio-video"
      component={StudioComposition}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={1920}
      height={1080}
      defaultCodec="h264"
    />
  );
};
