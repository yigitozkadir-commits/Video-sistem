"""Unit tests for scripts/lib/slideshow_risk.py's style-relative checks.

parse_scene_blocks() is order-agnostic on purpose (see the module's
_SCENE_ID_RE docstring) - two real files in this repo disagree on whether
durationFrames or visuals comes first (scenesData.ts vs lullabies.ts), so
tests cover both orderings explicitly rather than assuming one."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from lib.slideshow_risk import (
    motion_ceiling_findings,
    parse_scene_blocks,
    repeated_adjacent_asset_findings,
    slot_duration_findings,
)


def scenesdata_style(scene_id, files, duration_frames):
    files_str = ",\n".join(f'{{ type: "still", file: "{f}" }}' for f in files)
    return f"""{{
    id: "{scene_id}",
    title: "T",
    audioFile: null,
    visuals: [
      {files_str}
    ],
    startFrame: 0,
    durationFrames: {duration_frames},
  }}"""


def lullabies_style(scene_id, files, duration_frames):
    files_str = ",\n".join(f'{{ type: "still", file: "{f}" }}' for f in files)
    return f"""{{
        id: "{scene_id}",
        title: "T",
        audioFile: null,
        startFrame: 0,
        durationFrames: {duration_frames},
        visuals: [
          {files_str}
        ],
      }}"""


class TestParseSceneBlocks(unittest.TestCase):
    def test_scenesdata_field_order_visuals_before_duration(self):
        text = "export const SCENES = [\n" + scenesdata_style("SC-001", ["a.jpg", "b.jpg"], 90) + "\n];"
        blocks = parse_scene_blocks(text)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0], {"scene_id": "SC-001", "duration_frames": 90, "files": ["a.jpg", "b.jpg"]})

    def test_lullabies_field_order_duration_before_visuals(self):
        text = "export const LULLABIES = [{ id: \"ninni-x\", scenes: [\n" + \
            lullabies_style("KAZAK", ["a.jpg", "b.jpg"], 2700) + "\n] }];"
        blocks = parse_scene_blocks(text)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["scene_id"], "KAZAK")
        self.assertEqual(blocks[0]["duration_frames"], 2700)
        self.assertEqual(blocks[0]["files"], ["a.jpg", "b.jpg"])

    def test_lowercase_lullaby_id_never_matched_as_scene(self):
        # The enclosing Lullaby object's own id ("ninni-kazak") is
        # lowercase and must never be treated as a scene id.
        text = "{ id: \"ninni-kazak\", label: \"x\", scenes: [\n" + \
            lullabies_style("KAZAK", ["a.jpg"], 2700) + "\n] }"
        blocks = parse_scene_blocks(text)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["scene_id"], "KAZAK")

    def test_multiple_scenes_each_parsed_independently(self):
        text = (
            scenesdata_style("SC-001", ["a.jpg"], 90) + ",\n" +
            scenesdata_style("SC-002", ["b.jpg", "c.jpg"], 180)
        )
        blocks = parse_scene_blocks(text)
        self.assertEqual([b["scene_id"] for b in blocks], ["SC-001", "SC-002"])
        self.assertEqual(blocks[1]["files"], ["b.jpg", "c.jpg"])

    def test_scene_with_no_visuals_skipped(self):
        text = """{
      id: "SC-001",
      title: "T",
      audioFile: null,
      visuals: [],
      startFrame: 0,
      durationFrames: 90,
    }"""
        self.assertEqual(parse_scene_blocks(text), [])

    def test_unquoted_ts_keys_parsed_not_json_keys(self):
        # Regression: file: "x" (unquoted TS key), not "file": "x" (JSON) -
        # a quoted-key regex silently matches 0 files against real data.
        text = scenesdata_style("SC-001", ["subdir/file name.jpg"], 90)
        blocks = parse_scene_blocks(text)
        self.assertEqual(blocks[0]["files"], ["subdir/file name.jpg"])


class TestSlotDurationFindings(unittest.TestCase):
    def test_no_pace_config_no_findings(self):
        scenes = [{"scene_id": "SC-001", "duration_frames": 9000, "files": ["a.jpg"]}]
        self.assertEqual(slot_duration_findings(scenes, 30, None), [])
        self.assertEqual(slot_duration_findings(scenes, 30, {}), [])

    def test_slot_within_range_not_flagged(self):
        # 20 files over 2700 frames @ 30fps = 4.5s/slot, exactly the
        # template's own avg_shot_s - the real PRJ-ninniler-atlasi shape.
        files = [f"img{i}.jpg" for i in range(20)]
        scenes = [{"scene_id": "KAZAK", "duration_frames": 2700, "files": files}]
        pace = {"avg_shot_s": 4.5, "range": [3, 7]}
        self.assertEqual(slot_duration_findings(scenes, 30, pace), [])

    def test_slot_far_over_range_upper_bound_flagged(self):
        # 1 file over 900 frames @ 30fps = 30s/slot, vs range upper 7s -
        # far past the 1.5x tolerance (10.5s).
        scenes = [{"scene_id": "SC-001", "duration_frames": 900, "files": ["a.jpg"]}]
        pace = {"avg_shot_s": 4.5, "range": [3, 7]}
        findings = slot_duration_findings(scenes, 30, pace)
        self.assertEqual(len(findings), 1)
        self.assertIn("SC-001", findings[0])

    def test_slot_moderately_over_within_tolerance_not_flagged(self):
        # 8s/slot vs range upper 7s - over the range but under the 1.5x
        # (10.5s) tolerance, same "last-slot absorbs rounding" philosophy
        # as pre_render_checklist.py's LOOP_RATIO_THRESHOLD.
        scenes = [{"scene_id": "SC-001", "duration_frames": 240, "files": ["a.jpg"]}]
        pace = {"avg_shot_s": 4.5, "range": [3, 7]}
        self.assertEqual(slot_duration_findings(scenes, 30, pace), [])

    def test_empty_files_skipped_no_division_by_zero(self):
        scenes = [{"scene_id": "SC-001", "duration_frames": 90, "files": []}]
        pace = {"avg_shot_s": 4.5, "range": [3, 7]}
        self.assertEqual(slot_duration_findings(scenes, 30, pace), [])


class TestRepeatedAdjacentAssetFindings(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.ts_path = Path(self._tmpdir.name) / "scenesData.ts"
        self.ts_path.write_text("// placeholder")

    def test_no_repeats_no_findings(self):
        scenes = [{"scene_id": "SC-001", "duration_frames": 90, "files": ["a.jpg", "b.jpg", "c.jpg"]}]
        self.assertEqual(repeated_adjacent_asset_findings(scenes, self.ts_path), [])

    def test_same_filename_back_to_back_flagged(self):
        scenes = [{"scene_id": "SC-001", "duration_frames": 90, "files": ["a.jpg", "a.jpg", "b.jpg"]}]
        findings = repeated_adjacent_asset_findings(scenes, self.ts_path)
        self.assertEqual(len(findings), 1)
        self.assertIn("a.jpg", findings[0])

    def test_repeat_across_scene_boundary_flagged(self):
        scenes = [
            {"scene_id": "SC-001", "duration_frames": 90, "files": ["a.jpg", "b.jpg"]},
            {"scene_id": "SC-002", "duration_frames": 90, "files": ["b.jpg", "c.jpg"]},
        ]
        findings = repeated_adjacent_asset_findings(scenes, self.ts_path)
        self.assertEqual(len(findings), 1)
        self.assertIn("SC-002", findings[0])

    def test_non_adjacent_repeat_not_flagged(self):
        scenes = [{"scene_id": "SC-001", "duration_frames": 90, "files": ["a.jpg", "b.jpg", "a.jpg"]}]
        self.assertEqual(repeated_adjacent_asset_findings(scenes, self.ts_path), [])

    def test_different_filenames_same_bytes_flagged_via_sha256(self):
        base = Path(self._tmpdir.name)
        (base / "one.jpg").write_bytes(b"identical-content")
        (base / "two.jpg").write_bytes(b"identical-content")
        scenes = [{"scene_id": "SC-001", "duration_frames": 90, "files": ["one.jpg", "two.jpg"]}]
        findings = repeated_adjacent_asset_findings(scenes, self.ts_path)
        self.assertEqual(len(findings), 1)
        self.assertIn("byte-identical", findings[0])

    def test_missing_files_do_not_crash_or_false_positive(self):
        scenes = [{"scene_id": "SC-001", "duration_frames": 90, "files": ["missing1.jpg", "missing2.jpg"]}]
        self.assertEqual(repeated_adjacent_asset_findings(scenes, self.ts_path), [])


class TestMotionCeilingFindings(unittest.TestCase):
    RESTRAINED_TSX = 'const KEN_BURNS_SCALE = 1.03; // restrained'

    def test_ceiling_at_calibrated_baseline_not_flagged(self):
        self.assertEqual(motion_ceiling_findings(self.RESTRAINED_TSX, 1), [])

    def test_ceiling_none_not_flagged(self):
        self.assertEqual(motion_ceiling_findings(self.RESTRAINED_TSX, None), [])

    def test_higher_ceiling_with_restrained_constant_flagged(self):
        # The real PRJ-ninniler-atlasi case: style motion_ceiling=2 but the
        # composition still uses the ceiling-1-calibrated 1.03 constant.
        findings = motion_ceiling_findings(self.RESTRAINED_TSX, 2)
        self.assertEqual(len(findings), 1)
        self.assertIn("motion_ceiling=2", findings[0])

    def test_higher_ceiling_with_matching_higher_scale_not_flagged(self):
        tsx = 'const KEN_BURNS_SCALE = 1.12; // tuned for motion_ceiling 3'
        self.assertEqual(motion_ceiling_findings(tsx, 3), [])

    def test_no_ken_burns_constant_in_file_no_crash(self):
        self.assertEqual(motion_ceiling_findings("// no constant here", 3), [])


if __name__ == "__main__":
    unittest.main()
