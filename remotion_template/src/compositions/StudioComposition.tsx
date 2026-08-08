import React from "react";
import { AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, useCurrentFrame } from "remotion";
import { SCENES, SceneVisual } from "../scenesData";

// Studio-standard composition pattern, distilled from remotion_avrasya /
// remotion_ryskulov after two rounds of real production bugs. Per-scene
// crossfaded still/video slides + Ken-Burns on stills + measured narration
// audio with fade in/out + a title-card overlay. Reliability-badge and
// citation-card overlays are intentionally NOT included here - they're a
// per-style-profile concern, add them per project if the style profile
// calls for them (see style/archival_restrained_documentary.json's
// ai_generated_disclosure / citation_card fields).

const FADE_FRAMES = 15; // 0.5s at 30fps
const KEN_BURNS_SCALE = 1.03; // restrained - matches motion_ceiling: 1 in most style profiles

const VisualSlide: React.FC<{
  visual: SceneVisual;
  slotDurationFrames: number;
  isFirstSlide: boolean;
  isLastSlide: boolean;
}> = ({ visual, slotDurationFrames, isFirstSlide, isLastSlide }) => {
  const frame = useCurrentFrame();

  // Guard against very short slots: interpolate() requires a strictly
  // increasing inputRange, which unconditional FADE_FRAMES-based crossfades
  // violate once slotDurationFrames drops below ~2x the fade length (e.g. a
  // near-silent scene, or a scene with many visual slots crammed into a
  // short narration). Found and fixed for real in two separate projects
  // this system produced - always keep this guard when adapting the
  // pattern, don't unconditionally interpolate over slotDurationFrames.
  const maxFade = Math.max(0, Math.floor(slotDurationFrames / 2) - 1);
  const crossfadeIn = Math.min(isFirstSlide ? FADE_FRAMES : Math.floor(slotDurationFrames / 3), maxFade);
  const crossfadeOut = Math.min(isLastSlide ? FADE_FRAMES : Math.floor(slotDurationFrames / 3), maxFade);

  const opacity =
    maxFade < 1
      ? 1
      : interpolate(
          frame,
          [0, crossfadeIn, slotDurationFrames - crossfadeOut, slotDurationFrames],
          [0, 1, 1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );

  const scale =
    visual.type === "still"
      ? interpolate(frame, [0, slotDurationFrames], [1, KEN_BURNS_SCALE], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 1;

  if (visual.type === "video") {
    return (
      <AbsoluteFill style={{ opacity }}>
        <OffthreadVideo
          src={visual.file}
          loop
          muted
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ opacity }}>
      <AbsoluteFill>
        <Img
          src={visual.file}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: "blur(30px) brightness(0.45) grayscale(0.2)",
            transform: "scale(1.15)",
          }}
        />
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <Img
          src={visual.file}
          style={{
            height: "94%",
            width: "auto",
            maxWidth: "94%",
            objectFit: "contain",
            boxShadow: "0 30px 80px rgba(0,0,0,0.7)",
            transform: `scale(${scale})`,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const SceneLayer: React.FC<{
  title: string;
  audioFile: string | null;
  visuals: SceneVisual[];
  durationFrames: number;
}> = ({ title, audioFile, visuals, durationFrames }) => {
  const frame = useCurrentFrame();

  const fade = Math.max(1, Math.min(FADE_FRAMES, Math.floor(durationFrames / 2) - 1));
  const titleFadeIn = Math.max(1, Math.min(20, Math.floor(durationFrames / 2) - fade - 1));

  const audioOpacity = interpolate(
    frame,
    [0, fade, durationFrames - fade, durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const titleOpacity = interpolate(
    frame,
    [fade, fade + titleFadeIn, durationFrames - fade, durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // audioFile is null for silent scenes (e.g. a title card) - by design,
  // not an error. Never fall back to a different audio source here.
  const audioEl = audioFile ? <Audio src={audioFile} volume={audioOpacity} /> : null;

  if (visuals.length === 0) {
    return (
      <>
        {audioEl}
        <AbsoluteFill style={{ backgroundColor: "#1a1816", justifyContent: "center", alignItems: "center" }}>
          <div style={{ color: "#8a8272", fontFamily: "Georgia, serif", fontSize: 32 }}>
            [{title} - no visual yet]
          </div>
        </AbsoluteFill>
      </>
    );
  }

  const slotDuration = Math.floor(durationFrames / visuals.length);

  return (
    <>
      {audioEl}
      <AbsoluteFill style={{ backgroundColor: "#0a0908" }}>
      {visuals.map((visual, i) => {
        const slotStartFrame = i * slotDuration;
        const isLastVisual = i === visuals.length - 1;
        const thisSlotDuration = isLastVisual ? durationFrames - slotStartFrame : slotDuration;
        return (
          <Sequence key={i} from={slotStartFrame} durationInFrames={thisSlotDuration} layout="none">
            <VisualSlide
              visual={visual}
              slotDurationFrames={thisSlotDuration}
              isFirstSlide={i === 0}
              isLastSlide={isLastVisual}
            />
          </Sequence>
        );
      })}

      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          alignItems: "flex-start",
          padding: "0 0 64px 80px",
          opacity: titleOpacity,
        }}
      >
        <div
          style={{
            fontFamily: "Georgia, 'Times New Roman', serif",
            fontSize: 40,
            fontWeight: 700,
            color: "#c9c2b0",
            letterSpacing: 1.2,
            textShadow: "0 4px 24px rgba(0,0,0,0.9)",
            maxWidth: "70%",
          }}
        >
          {title}
        </div>
      </AbsoluteFill>
      </AbsoluteFill>
    </>
  );
};

export const StudioComposition: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {SCENES.map((scene) => (
        <Sequence key={scene.id} from={scene.startFrame} durationInFrames={scene.durationFrames}>
          <SceneLayer
            title={`${scene.id} - ${scene.title}`}
            audioFile={scene.audioFile}
            visuals={scene.visuals}
            durationFrames={scene.durationFrames}
          />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
