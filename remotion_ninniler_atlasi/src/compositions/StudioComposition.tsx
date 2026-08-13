import React, { useMemo } from "react";
import { AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { createTikTokStyleCaptions, type Caption } from "@remotion/captions";
import { SCENES, SceneData, SceneVisual } from "../scenesData";

// Studio-standard composition pattern, distilled from remotion_avrasya /
// remotion_ryskulov after two rounds of real production bugs. Per-scene
// crossfaded still/video slides + Ken-Burns on stills + measured narration
// audio with fade in/out + a title-card overlay. Reliability-badge and
// citation-card overlays are intentionally NOT included here - they're a
// per-style-profile concern, add them per project if the style profile
// calls for them (see style/archival_restrained_documentary.json's
// ai_generated_disclosure / citation_card fields).
//
// Captions (review finding B-05) are opt-in per scene via SceneData's
// optional `captions` field (scripts/generate_captions.py's output,
// already @remotion/captions-shaped) - a scene without it renders
// identically to before this was added. Default style is a restrained,
// centered subtitle bar (readable phrase-length chunks, not word-by-word
// flash) to match this studio's documentary tone; a project that wants
// TikTok-style word-highlight for a TPL-vertical-short deliverable can
// swap CaptionsOverlay's rendering without touching the data pipeline -
// createTikTokStyleCaptions() already produces per-word timing within
// each page (see activePage.tokens), this component just doesn't
// highlight them individually by default.

const FADE_FRAMES = 15; // 0.5s at 30fps
const KEN_BURNS_SCALE = 1.03; // restrained - matches motion_ceiling: 1 in most style profiles
const CAPTION_PAGE_MS = 1500; // group words into ~1.5s reading chunks, not per-word flashes

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

const CaptionsOverlay: React.FC<{ captions: Caption[] }> = ({ captions }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentMs = (frame / fps) * 1000;

  // captions are relative to this scene's own audio start (0 = scene
  // start) - useCurrentFrame() here is already Sequence-relative (this
  // component only ever renders inside a scene's own <Sequence>), so no
  // extra offset math is needed.
  const { pages } = useMemo(
    () => createTikTokStyleCaptions({ captions, combineTokensWithinMilliseconds: CAPTION_PAGE_MS }),
    [captions]
  );

  const activePage = pages.find(
    (page) => currentMs >= page.startMs && currentMs < page.startMs + page.durationMs
  );

  if (!activePage) {
    return null;
  }

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        padding: "0 8% 120px 8%",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          fontFamily: "Georgia, 'Times New Roman', serif",
          fontSize: 34,
          fontWeight: 600,
          color: "#f2efe6",
          textAlign: "center",
          lineHeight: 1.35,
          textShadow: "0 2px 12px rgba(0,0,0,0.9), 0 0 4px rgba(0,0,0,0.9)",
          background: "rgba(10, 9, 8, 0.55)",
          padding: "10px 22px",
          borderRadius: 6,
        }}
      >
        {activePage.text}
      </div>
    </AbsoluteFill>
  );
};

const SceneLayer: React.FC<{
  title: string;
  audioFile: string | null;
  visuals: SceneVisual[];
  durationFrames: number;
  captions?: Caption[];
}> = ({ title, audioFile, visuals, durationFrames, captions }) => {
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
  // Opt-in (B-05): only rendered when this scene actually has caption
  // data - see the file-header comment and SceneData.captions' docstring.
  const captionsEl = captions && captions.length > 0 ? <CaptionsOverlay captions={captions} /> : null;

  if (visuals.length === 0) {
    return (
      <>
        {audioEl}
        <AbsoluteFill style={{ backgroundColor: "#1a1816", justifyContent: "center", alignItems: "center" }}>
          <div style={{ color: "#8a8272", fontFamily: "Georgia, serif", fontSize: 32 }}>
            [{title} - no visual yet]
          </div>
        </AbsoluteFill>
        {captionsEl}
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
      {captionsEl}
      </AbsoluteFill>
    </>
  );
};

export const StudioComposition: React.FC<{ scenes?: SceneData[] }> = ({ scenes = SCENES }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {scenes.map((scene) => (
        <Sequence key={scene.id} from={scene.startFrame} durationInFrames={scene.durationFrames}>
          <SceneLayer
            title={`${scene.id} - ${scene.title}`}
            audioFile={scene.audioFile}
            visuals={scene.visuals}
            durationFrames={scene.durationFrames}
            captions={scene.captions}
          />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
