"""Unit tests for scripts/check_stale_human_gates.py's staleness logic.

Uses a temp directory swapped in for PROJECTS_DIR/CONFIG_PATH so these
tests never touch real projects/ data - the real-data run (0 findings,
confirmed manually against projects/PRJ-*/state/) is a separate
validation step, not something these tests reproduce."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import check_stale_human_gates as chg


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class TestCheckStaleHumanGates(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.projects_dir = Path(self._tmpdir.name) / "projects"
        self.projects_dir.mkdir()
        self.config_path = Path(self._tmpdir.name) / "studio.config.json"
        self.config_path.write_text(json.dumps({"human": {"approval_sla_hours": 24, "on_timeout": "hold"}}))

        self._patches = [
            patch.object(chg, "PROJECTS_DIR", self.projects_dir),
            patch.object(chg, "CONFIG_PATH", self.config_path),
        ]
        for p in self._patches:
            p.start()
            self.addCleanup(p.stop)

    def _write_approvals(self, project_id, records):
        state_dir = self.projects_dir / project_id / "state"
        state_dir.mkdir(parents=True)
        lines = [json.dumps(r) for r in records]
        (state_dir / "approvals.jsonl").write_text("\n".join(lines) + "\n")

    def test_no_projects_no_findings(self):
        self.assertEqual(chg.check_stale_human_gates(), [])

    def test_fresh_pending_approval_not_flagged(self):
        self._write_approvals("PRJ-test", [{
            "approval_id": "APR-0001", "decision": "pending",
            "scope": {"type": "scene", "target_id": "SC-001"},
            "requested_by": "director-agent", "reason": "calibration",
            "requested_at": _iso(datetime.now(timezone.utc) - timedelta(hours=2)),
        }])
        self.assertEqual(chg.check_stale_human_gates(), [])

    def test_stale_pending_approval_flagged(self):
        self._write_approvals("PRJ-test", [{
            "approval_id": "APR-0002", "decision": "pending",
            "scope": {"type": "master", "target_id": "PRJ-test"},
            "requested_by": "director-agent", "reason": "master_export",
            "requested_at": _iso(datetime.now(timezone.utc) - timedelta(hours=30)),
        }])
        findings = chg.check_stale_human_gates()
        self.assertEqual(len(findings), 1)
        self.assertIn("APR-0002", findings[0])
        self.assertIn("hold", findings[0])

    def test_decided_approval_never_flagged_even_if_old(self):
        self._write_approvals("PRJ-test", [{
            "approval_id": "APR-0003", "decision": "approved",
            "scope": {"type": "scene", "target_id": "SC-002"},
            "requested_by": "director-agent", "reason": "calibration",
            "requested_at": _iso(datetime.now(timezone.utc) - timedelta(days=30)),
        }])
        self.assertEqual(chg.check_stale_human_gates(), [])

    def test_revoked_pending_approval_not_flagged(self):
        self._write_approvals("PRJ-test", [{
            "approval_id": "APR-0004", "decision": "pending", "revoked": True,
            "scope": {"type": "scene", "target_id": "SC-003"},
            "requested_by": "director-agent", "reason": "calibration",
            "requested_at": _iso(datetime.now(timezone.utc) - timedelta(hours=100)),
        }])
        self.assertEqual(chg.check_stale_human_gates(), [])

    def test_pending_without_requested_at_flagged_as_data_gap(self):
        self._write_approvals("PRJ-test", [{
            "approval_id": "APR-0005", "decision": "pending",
            "scope": {"type": "scene", "target_id": "SC-004"},
            "requested_by": "director-agent", "reason": "calibration",
        }])
        findings = chg.check_stale_human_gates()
        self.assertEqual(len(findings), 1)
        self.assertIn("no requested_at", findings[0])

    def test_malformed_json_line_flagged_not_raised(self):
        state_dir = self.projects_dir / "PRJ-test" / "state"
        state_dir.mkdir(parents=True)
        (state_dir / "approvals.jsonl").write_text("{not valid json\n")
        findings = chg.check_stale_human_gates()
        self.assertEqual(len(findings), 1)
        self.assertIn("malformed JSON", findings[0])

    def test_invalid_requested_at_format_flagged(self):
        self._write_approvals("PRJ-test", [{
            "approval_id": "APR-0006", "decision": "pending",
            "scope": {"type": "scene", "target_id": "SC-005"},
            "requested_by": "director-agent", "reason": "calibration",
            "requested_at": "not-a-timestamp",
        }])
        findings = chg.check_stale_human_gates()
        self.assertEqual(len(findings), 1)
        self.assertIn("not a valid ISO 8601", findings[0])

    def test_respects_custom_sla_from_config(self):
        self.config_path.write_text(json.dumps({"human": {"approval_sla_hours": 1, "on_timeout": "abort"}}))
        self._write_approvals("PRJ-test", [{
            "approval_id": "APR-0007", "decision": "pending",
            "scope": {"type": "scene", "target_id": "SC-006"},
            "requested_by": "director-agent", "reason": "calibration",
            "requested_at": _iso(datetime.now(timezone.utc) - timedelta(hours=2)),
        }])
        findings = chg.check_stale_human_gates()
        self.assertEqual(len(findings), 1)
        self.assertIn("abort", findings[0])

    def test_multiple_projects_scanned(self):
        self._write_approvals("PRJ-a", [{
            "approval_id": "APR-0008", "decision": "pending",
            "scope": {"type": "scene", "target_id": "SC-007"},
            "requested_by": "director-agent", "reason": "calibration",
            "requested_at": _iso(datetime.now(timezone.utc) - timedelta(hours=48)),
        }])
        self._write_approvals("PRJ-b", [{
            "approval_id": "APR-0009", "decision": "pending",
            "scope": {"type": "scene", "target_id": "SC-008"},
            "requested_by": "director-agent", "reason": "calibration",
            "requested_at": _iso(datetime.now(timezone.utc) - timedelta(hours=48)),
        }])
        findings = chg.check_stale_human_gates()
        self.assertEqual(len(findings), 2)


if __name__ == "__main__":
    unittest.main()
