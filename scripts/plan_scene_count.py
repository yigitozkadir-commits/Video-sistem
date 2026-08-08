#!/usr/bin/env python3
"""
Implements bible/Module_22_Scene_Planning_Algorithm.md: given a source PDF
(or .txt/.docx already extracted to text), computes a starting scene-count /
duration / video-still-mix plan without asking the human first.

This is a starting skeleton, not a final decision - M17's own per-shot
decision tree (video-or-still, camera, music, silence) still runs on top of
it and still writes its own decisions/DEC-*.json. This script only answers
the two questions that used to require asking the user every time: how many
scenes, and roughly how many of them are video vs still.

Usage:
    python3 scripts/plan_scene_count.py <source.pdf|source.txt> \
        [--content-type research_documentary|illustrated_story|encyclopedic_atlas|narrative_history|other] \
        [--target-duration-s N] [--out state/scene_plan.json]

Content-type classification, avg_scene_length_s ranges, the delivered-wpm
constant and the video-ratio target are all calibration data from
Module 22 §3/§5/§6/§7 - update both in lockstep when a new project finishes
and the calibration table grows.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Module 22 §4 - measured delivered wpm (includes M17 §9 pauses/silences),
# NOT a template's planning wpm, which always overshoots duration downward.
DELIVERED_WPM = 115.0

# Module 22 §5
AVG_SCENE_LENGTH_S = {
    "research_documentary": 45,
    "narrative_history": 37,
    "illustrated_story": 10,
    "encyclopedic_atlas": 42,
    "other": 40,
}

# Module 22 §3
NARRATION_WORD_FACTOR = {
    "research_documentary": 1.0,   # midpoint of [0.8, 1.3]; caller can override via reasoning
    "narrative_history": 1.25,     # midpoint of [1.0, 1.5]
    "illustrated_story": 1.0,      # duration-first, not word-first - see note below
    "encyclopedic_atlas": None,    # handled separately: chunked into episodes
    "other": 1.0,
}

# Module 22 §6
VIDEO_RATIO_TARGET = {
    "research_documentary": 0.70,
    "narrative_history": 0.70,
    "illustrated_story": 0.20,     # picture-book pacing is still-native, not video-native
    "encyclopedic_atlas": 0.05,    # reference/atlas format stays still-heavy by design
    "other": 0.55,
}

MIN_SCENE_S, MAX_SCENE_S = 8, 90  # M17 §5 floor/ceiling

# Module 22 §3 - PRJ-gok-umay-atlasi calibration: 25330 source words split into
# 6 episodes (~4222 source words/episode -> episode_count), but each episode's
# NARRATION is a curated summary, not a proportional transcription: real
# measured output was 1743s across 6 episodes (ffprobe) = ~557 narration
# words/episode at DELIVERED_WPM. Source-word share and narration length are
# decoupled for this content_type - don't confuse the two.
EPISODE_SOURCE_WORDS = 4000       # drives episode_count only
EPISODE_NARRATION_WORDS = 560     # drives each episode's duration

# Module 22 §6b - user-given anchors (2026-08-07), NOT yet render-verified
# (see Module 22 §7b). (duration_minutes, ai_video_count).
AI_VIDEO_ANCHORS = [(12.5, 5.0), (30.0, 12.5), (60.0, 20.0)]

# Module 22 §6c - user-given density anchor (2026-08-07), NOT yet render-verified.
# 100 images / 15 minutes.
IMAGE_DENSITY_PER_MIN = 100 / 15

# Module 22 §6d - embedded-image PDF branch threshold: below this, treat the
# PDF as text-only and generate all visuals via Flow instead.
EMBEDDED_IMAGE_MIN_PX = 100  # filter out smask/decoration slivers
EMBEDDED_IMAGE_THRESHOLD = 20  # meaningful embedded images needed to trigger the branch

VIDEO_FIRST_CONTENT_TYPES = {"research_documentary", "narrative_history"}


def ai_video_count_target(duration_min: float) -> tuple[float, str]:
    """Module 22 §6b piecewise-linear interpolation. Returns (count, note)."""
    anchors = AI_VIDEO_ANCHORS
    if duration_min <= anchors[0][0]:
        count = anchors[0][1] * (duration_min / anchors[0][0])
        return max(1.0, count), ""
    for (m0, c0), (m1, c1) in zip(anchors, anchors[1:]):
        if m0 <= duration_min <= m1:
            frac = (duration_min - m0) / (m1 - m0)
            return c0 + frac * (c1 - c0), ""
    # beyond the last anchor: extrapolate at the last segment's slope
    (m0, c0), (m1, c1) = anchors[-2], anchors[-1]
    slope = (c1 - c0) / (m1 - m0)
    count = c1 + slope * (duration_min - m1)
    return max(1.0, count), "UYARI: 60dk ustu ekstrapolasyon, kalibrasyon disi (Module 22 SS7b)."


def image_count_target(duration_min: float) -> int:
    """Module 22 §6c: round(duration_min * IMAGE_DENSITY_PER_MIN)."""
    return round(duration_min * IMAGE_DENSITY_PER_MIN)


def count_embedded_images(pdf_path: Path) -> int:
    """Module 22 §6d: pdfimages -list, filtered for smask/decoration slivers."""
    out = subprocess.run(
        ["pdfimages", "-list", str(pdf_path)], capture_output=True, text=True
    ).stdout
    lines = out.splitlines()[2:]  # skip the two header lines
    count = 0
    for line in lines:
        parts = line.split()
        if len(parts) < 5:
            continue
        img_type = parts[2]
        if img_type == "smask":
            continue
        try:
            width, height = int(parts[3]), int(parts[4])
        except (ValueError, IndexError):
            continue
        if width >= EMBEDDED_IMAGE_MIN_PX and height >= EMBEDDED_IMAGE_MIN_PX:
            count += 1
    return count


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return subprocess.run(
            ["pdftotext", str(path), "-"], capture_output=True, text=True
        ).stdout
    if path.suffix.lower() == ".docx":
        # mammoth/docx2txt aren't guaranteed installed; textutil/pandoc aren't either.
        # This repo already has python-docx available where docx sources are used.
        import docx  # noqa: E402
        return "\n".join(p.text for p in docx.Document(str(path)).paragraphs)
    return path.read_text(encoding="utf-8", errors="ignore")


def classify_content_type(text: str) -> str:
    words = text.split()
    word_count = len(words)
    has_bibliography = bool(re.search(r"kaynak[çc]a|bibliyografya|references", text, re.IGNORECASE))
    has_numbered_headings = len(re.findall(r"^\s*\d{1,2}[.\)]\s+[A-ZÇĞİÖŞÜ]", text, re.MULTILINE)) >= 3
    avg_sentence_len = word_count / max(1, len(re.findall(r"[.!?]+", text)))

    if word_count > 10000:
        return "encyclopedic_atlas"
    if word_count < 600 and avg_sentence_len < 12:
        return "illustrated_story"
    if has_bibliography or has_numbered_headings:
        return "research_documentary"
    return "other"


def plan(text: str, content_type: str, target_duration_s: float | None,
         embedded_image_count: int = 0) -> dict:
    source_word_count = len(text.split())

    if content_type == "encyclopedic_atlas":
        episode_count = max(1, round(source_word_count / EPISODE_SOURCE_WORDS))
        narration_word_target = EPISODE_NARRATION_WORDS
        reasoning = (
            f"encyclopedic_atlas: {source_word_count} kelime / {EPISODE_SOURCE_WORDS} "
            f"kelime-bölüm hedefi = {episode_count} bölüm. Her bölümün narration'ı "
            f"kaynağın orantılı transkripsiyonu DEĞİL, küratörlü özettir - bölüm "
            f"başına sabit ~{narration_word_target} kelime hedeflenir (PRJ-gok-umay-atlasi "
            f"gerçek ölçüm: 1743s / 6 bölüm = ~290s/bölüm, ffprobe ile doğrulandı). "
            f"Aşağıdaki target_duration_s TEK BİR bölüm içindir, {episode_count} bölümün "
            f"tamamı için değil."
        )
    else:
        factor = NARRATION_WORD_FACTOR[content_type]
        narration_word_target = round(source_word_count * factor)
        reasoning = (
            f"{content_type}: kaynak {source_word_count} kelime x factor {factor} "
            f"= {narration_word_target} hedef narration kelimesi."
        )

    if target_duration_s is None:
        target_duration_s = round(narration_word_target / (DELIVERED_WPM / 60))

    avg_scene_length_s = AVG_SCENE_LENGTH_S[content_type]
    scene_count = max(1, round(target_duration_s / avg_scene_length_s))

    implied_scene_len = target_duration_s / scene_count
    if implied_scene_len < MIN_SCENE_S or implied_scene_len > MAX_SCENE_S:
        reasoning += (
            f" UYARI: ortalama sahne uzunluğu ({implied_scene_len:.1f}s) M17 §5 "
            f"sınırlarının ({MIN_SCENE_S}-{MAX_SCENE_S}s) dışında - manuel gözden geçir."
        )

    video_ratio = VIDEO_RATIO_TARGET[content_type]
    video_scene_target = round(scene_count * video_ratio)
    still_scene_target = scene_count - video_scene_target

    duration_min = target_duration_s / 60
    ai_video_count, ai_video_note = ai_video_count_target(duration_min)
    image_count = image_count_target(duration_min)

    if content_type in VIDEO_FIRST_CONTENT_TYPES:
        # Module 22 §6b/§6c - absolute duration-based targets take over as the
        # primary model for these content types; the ratio model above (§6)
        # stays in the output as a cross-check, not the driving number.
        video_scene_target = round(ai_video_count)
        reasoning += (
            f" M22 SS6b: {duration_min:.1f}dk icin ai_video_count_target="
            f"{ai_video_count:.1f} (yuzde modeli yerine birincil hedef). "
            f"SS6c: image_count_target={image_count} ({IMAGE_DENSITY_PER_MIN:.3f} gorsel/dk)."
        )
        if ai_video_note:
            reasoning += " " + ai_video_note

    result = {
        "content_type": content_type,
        "source_word_count": source_word_count,
        "narration_word_target": narration_word_target,
        "target_duration_s": target_duration_s,
        "avg_scene_length_s": avg_scene_length_s,
        "scene_count": scene_count,
        "video_ratio_target": video_ratio,
        "video_scene_target": video_scene_target,
        "still_scene_target": still_scene_target,
        "ai_video_count_target": round(ai_video_count),
        "image_count_target": image_count,
        "source_has_embedded_images": embedded_image_count >= EMBEDDED_IMAGE_THRESHOLD,
        "embedded_image_count": embedded_image_count,
        "reasoning": reasoning,
        "calibration_module": "bible/Module_22_Scene_Planning_Algorithm.md",
    }
    if embedded_image_count >= EMBEDDED_IMAGE_THRESHOLD:
        result["note_embedded_images"] = (
            f"{embedded_image_count} embedded gorsel bulundu (M22 SS6d esigi "
            f"{EMBEDDED_IMAGE_THRESHOLD}). scripts/extract_pdf_images.py ile "
            f"cikarilip image_count_target'a sayilmali; eksik kalirsa Flow'dan "
            f"tamamlanir."
        )
    if content_type == "encyclopedic_atlas":
        result["episode_count"] = max(1, round(source_word_count / EPISODE_SOURCE_WORDS))
        result["note"] = "scene_count/target_duration_s are PER EPISODE, not for all episode_count episodes combined."
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source_path")
    ap.add_argument("--content-type", choices=list(AVG_SCENE_LENGTH_S), default=None)
    ap.add_argument("--target-duration-s", type=float, default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    src = Path(args.source_path)
    if not src.exists():
        print(f"ERROR: {src} not found", file=sys.stderr)
        sys.exit(1)

    text = extract_text(src)
    content_type = args.content_type or classify_content_type(text)
    embedded_image_count = count_embedded_images(src) if src.suffix.lower() == ".pdf" else 0
    result = plan(text, content_type, args.target_duration_s, embedded_image_count)

    out_json = json.dumps(result, indent=2, ensure_ascii=False)
    print(out_json)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(out_json + "\n")
        print(f"\nWrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
