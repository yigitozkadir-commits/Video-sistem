import React from "react";
import { Composition } from "remotion";
import { StudioComposition } from "./compositions/StudioComposition";
import { LULLABIES, FPS } from "./lullabies";

// 10 lullabies, 10 separate Compositions (one per Ninniler Atlası nation),
// all sharing the one StudioComposition component via its `scenes` prop
// (review finding from this session's B-05 work made that prop possible).
// PLACEHOLDER TIMING - see lullabies.ts header: no music exists yet.
export const RemotionRoot: React.FC = () => {
  return (
    <>
      {LULLABIES.map((lullaby) => (
        <Composition
          key={lullaby.id}
          id={lullaby.id}
          component={StudioComposition}
          durationInFrames={lullaby.totalFrames}
          fps={FPS}
          width={1920}
          height={1080}
          defaultCodec="h264"
          defaultProps={{ scenes: lullaby.scenes }}
        />
      ))}
    </>
  );
};
