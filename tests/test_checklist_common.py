"""Unit tests for scripts/lib/checklist_common.py's
long_compound_number_findings() - the long-spelled-out-number detector that
exists because of a real ElevenLabs mispronunciation incident (CLAUDE.md
section 10 / LONG_NUMBER_WORD_THRESHOLD's own comment). Review finding B-04
flagged this as the most regression-fragile piece since its threshold (8)
is calibrated from that one real incident, not derived analytically."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from lib.checklist_common import LONG_NUMBER_WORD_THRESHOLD, long_compound_number_findings


def scene(scene_id: str, text: str) -> dict:
    return {"scene_id": scene_id, "source_text": text}


class TestLongCompoundNumberFindings(unittest.TestCase):
    def test_no_number_words_no_findings(self):
        scenes = [scene("SC-001", "Bu bir tarihi araştırma metnidir, sayı içermez.")]
        self.assertEqual(long_compound_number_findings(scenes), [])

    def test_run_just_under_threshold_not_flagged(self):
        short_run = " ".join(["bin"] * (LONG_NUMBER_WORD_THRESHOLD - 1))
        scenes = [scene("SC-002", f"nüfus {short_run} kişiydi")]
        self.assertEqual(long_compound_number_findings(scenes), [])

    def test_run_at_threshold_is_flagged(self):
        run = " ".join(["bin"] * LONG_NUMBER_WORD_THRESHOLD)
        scenes = [scene("SC-003", f"nüfus {run} kişiydi")]
        findings = long_compound_number_findings(scenes)
        self.assertEqual(len(findings), 1)
        self.assertIn("SC-003", findings[0])
        self.assertIn(f"{LONG_NUMBER_WORD_THRESHOLD} words", findings[0])

    def test_real_world_style_population_figure(self):
        # Loosely modeled on the actual SC-001 population-figure incident
        # this threshold was calibrated against (CLAUDE.md section 10).
        text = (
            "bölgenin nüfusu iki milyon üç yüz kırk beş bin altı yüz yetmiş "
            "sekiz kişiye ulaştı"
        )
        findings = long_compound_number_findings([scene("SC-001", text)])
        self.assertEqual(len(findings), 1)
        self.assertIn("SC-001", findings[0])

    def test_ordinary_year_not_flagged(self):
        # 4-digit years spelled out (~5 words) transcribe cleanly per this
        # module's own calibration note - must stay under threshold so
        # ordinary years don't trigger constant false alarms.
        text = "olay bin dokuz yüz elli üç yılında gerçekleşti"
        self.assertEqual(long_compound_number_findings([scene("SC-004", text)]), [])

    def test_trailing_run_at_end_of_text_is_caught(self):
        # Exercises the post-loop flush (run_len check after the for-loop
        # ends), not just the mid-text else-branch.
        run = " ".join(["on"] * LONG_NUMBER_WORD_THRESHOLD)
        scenes = [scene("SC-005", f"toplam sayı {run}")]
        findings = long_compound_number_findings(scenes)
        self.assertEqual(len(findings), 1)

    def test_case_insensitive(self):
        run = " ".join(["Bin"] * LONG_NUMBER_WORD_THRESHOLD)
        findings = long_compound_number_findings([scene("SC-006", run)])
        self.assertEqual(len(findings), 1)

    def test_multiple_scenes_only_flags_the_offending_one(self):
        run = " ".join(["yüz"] * LONG_NUMBER_WORD_THRESHOLD)
        scenes = [
            scene("SC-007", "sıradan bir cümle, sayı yok"),
            scene("SC-008", f"rakam {run} burada"),
            scene("SC-009", "başka sıradan bir cümle"),
        ]
        findings = long_compound_number_findings(scenes)
        self.assertEqual(len(findings), 1)
        self.assertIn("SC-008", findings[0])

    def test_two_separate_runs_in_same_scene_both_flagged(self):
        run = " ".join(["milyon"] * LONG_NUMBER_WORD_THRESHOLD)
        text = f"{run} ara metin burada duruyor {run}"
        findings = long_compound_number_findings([scene("SC-010", text)])
        self.assertEqual(len(findings), 2)

    def test_missing_source_text_treated_as_empty(self):
        self.assertEqual(long_compound_number_findings([{"scene_id": "SC-011"}]), [])


if __name__ == "__main__":
    unittest.main()
