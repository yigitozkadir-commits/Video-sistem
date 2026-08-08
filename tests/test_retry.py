"""Unit tests for scripts/lib/retry.py's backoff/jitter math and
NonRetryable short-circuit behavior (review finding B-04).

time.sleep and random.uniform are patched throughout so these tests run in
milliseconds instead of actually waiting out backoff delays - the delay
*arguments* passed to time.sleep are what's under test, not real time.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from lib.retry import NonRetryable, WallClockExceeded, with_retry


class TestWithRetry(unittest.TestCase):
    def test_succeeds_on_first_try_no_sleep(self):
        with patch("lib.retry.time.sleep") as mock_sleep:
            result = with_retry(lambda: 42)
        self.assertEqual(result, 42)
        mock_sleep.assert_not_called()

    def test_retries_transient_failure_then_succeeds(self):
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise ConnectionError("transient")
            return "ok"

        with patch("lib.retry._retry_config", return_value={"transient_max": 5, "backoff_base_s": 0.01}):
            with patch("lib.retry.time.sleep") as mock_sleep:
                result = with_retry(flaky, category="transient")

        self.assertEqual(result, "ok")
        self.assertEqual(calls["n"], 3)
        self.assertEqual(mock_sleep.call_count, 2)

    def test_exhausts_max_attempts_and_raises(self):
        def always_fails():
            raise ConnectionError("still down")

        with patch("lib.retry._retry_config", return_value={"transient_max": 3, "backoff_base_s": 0.01}):
            with patch("lib.retry.time.sleep") as mock_sleep:
                with self.assertRaises(ConnectionError):
                    with_retry(always_fails, category="transient")
        # sleeps between attempts 1->2 and 2->3, none after the final attempt
        self.assertEqual(mock_sleep.call_count, 2)

    def test_nonretryable_short_circuits_immediately(self):
        calls = {"n": 0}

        def bad_auth():
            calls["n"] += 1
            raise NonRetryable("401 invalid key")

        with patch("lib.retry._retry_config", return_value={"transient_max": 5, "backoff_base_s": 0.01}):
            with patch("lib.retry.time.sleep") as mock_sleep:
                with self.assertRaises(NonRetryable):
                    with_retry(bad_auth, category="transient")

        self.assertEqual(calls["n"], 1, "NonRetryable must not be retried")
        mock_sleep.assert_not_called()

    def test_compliance_category_never_retries_by_default(self):
        # CLAUDE.md law #6 / this module's own docstring: compliance_max
        # is 0 by design - a compliance failure should not auto-retry.
        calls = {"n": 0}

        def fails():
            calls["n"] += 1
            raise ValueError("content policy violation")

        with patch("lib.retry._retry_config", return_value={"compliance_max": 0}):
            with patch("lib.retry.time.sleep") as mock_sleep:
                with self.assertRaises(ValueError):
                    with_retry(fails, category="compliance")

        self.assertEqual(calls["n"], 1)
        mock_sleep.assert_not_called()

    def test_backoff_grows_exponentially_and_is_capped(self):
        # random.uniform patched to 0 so delay == min(cap, base * 2**(attempt-1)) exactly.
        def always_fails():
            raise ConnectionError("down")

        cfg = {"transient_max": 6, "backoff_base_s": 1, "backoff_cap_s": 10, "jitter": 0.2}
        with patch("lib.retry._retry_config", return_value=cfg):
            with patch("lib.retry.random.uniform", return_value=0.0):
                with patch("lib.retry.time.sleep") as mock_sleep:
                    with self.assertRaises(ConnectionError):
                        with_retry(always_fails, category="transient")

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        # attempts 1..5 sleep (attempt 6 is the last try, no sleep after it):
        # base*2^0, base*2^1, base*2^2, base*2^3, then capped at 10
        self.assertEqual(delays, [1, 2, 4, 8, 10])

    def test_jitter_is_applied_within_bounds(self):
        def always_fails():
            raise ConnectionError("down")

        cfg = {"transient_max": 2, "backoff_base_s": 10, "backoff_cap_s": 1000, "jitter": 0.5}
        with patch("lib.retry._retry_config", return_value=cfg):
            with patch("lib.retry.time.sleep") as mock_sleep:
                with self.assertRaises(ConnectionError):
                    with_retry(always_fails, category="transient")

        delay = mock_sleep.call_args_list[0].args[0]
        # base=10, jitter=0.5 -> delay in [10*0.5, 10*1.5] = [5, 15]
        self.assertGreaterEqual(delay, 5)
        self.assertLessEqual(delay, 15)

    def test_on_retry_callback_receives_attempt_and_exception(self):
        seen = []

        def flaky():
            if len(seen) < 2:
                raise ConnectionError(f"fail-{len(seen)}")
            return "ok"

        def on_retry(attempt, exc):
            seen.append((attempt, str(exc)))

        with patch("lib.retry._retry_config", return_value={"transient_max": 5, "backoff_base_s": 0.01}):
            with patch("lib.retry.time.sleep"):
                with_retry(flaky, category="transient", on_retry=on_retry)

        self.assertEqual(seen, [(1, "fail-0"), (2, "fail-1")])

    def test_no_queue_means_no_wall_clock_check(self):
        # queue=None (the default) must preserve the old attempts-only
        # behavior exactly - no _timeout_config lookup, no WallClockExceeded.
        def always_fails():
            raise ConnectionError("down")

        with patch("lib.retry._retry_config", return_value={"transient_max": 2, "backoff_base_s": 0.01}):
            with patch("lib.retry._timeout_config") as mock_timeout_cfg:
                with patch("lib.retry.time.sleep"):
                    with self.assertRaises(ConnectionError):
                        with_retry(always_fails, category="transient")
        mock_timeout_cfg.assert_not_called()

    def test_unknown_queue_means_no_wall_clock_check(self):
        # queue given but absent from the timeouts config -> no ceiling applied.
        def always_fails():
            raise ConnectionError("down")

        with patch("lib.retry._retry_config", return_value={"transient_max": 2, "backoff_base_s": 0.01}):
            with patch("lib.retry._timeout_config", return_value={}):
                with patch("lib.retry.time.sleep"):
                    with self.assertRaises(ConnectionError):
                        with_retry(always_fails, category="transient", queue="q.unknown")

    def test_wall_clock_exceeded_raises_before_max_attempts(self):
        # A generous attempts budget (transient_max=100) but a tiny
        # wall-clock ceiling: time.monotonic() is mocked to jump far past
        # the ceiling on the second read, so the loop must stop on
        # WallClockExceeded long before attempts are exhausted.
        def always_fails():
            raise ConnectionError("down")

        monotonic_values = iter([0.0, 1000.0, 1000.0, 1000.0, 1000.0])

        with patch("lib.retry._retry_config", return_value={"transient_max": 100, "backoff_base_s": 0.01}):
            with patch("lib.retry._timeout_config", return_value={"q.prompt": 5}):  # 5 min = 300s
                with patch("lib.retry.time.monotonic", side_effect=lambda: next(monotonic_values)):
                    with patch("lib.retry.time.sleep"):
                        with self.assertRaises(WallClockExceeded):
                            with_retry(always_fails, category="transient", queue="q.prompt")

    def test_wall_clock_not_exceeded_within_ceiling(self):
        # Elapsed time stays under the ceiling for every check - behaves
        # exactly like the no-queue case (raises the underlying exception
        # once attempts are exhausted, not WallClockExceeded).
        def always_fails():
            raise ConnectionError("down")

        with patch("lib.retry._retry_config", return_value={"transient_max": 3, "backoff_base_s": 0.01}):
            with patch("lib.retry._timeout_config", return_value={"q.prompt": 5}):
                with patch("lib.retry.time.monotonic", return_value=0.0):
                    with patch("lib.retry.time.sleep"):
                        with self.assertRaises(ConnectionError):
                            with_retry(always_fails, category="transient", queue="q.prompt")

    def test_wall_clock_exceeded_logs_with_timeout_code(self):
        logged = {}

        def fake_log_error(**kwargs):
            logged.update(kwargs)

        def always_fails():
            raise ConnectionError("down")

        monotonic_values = iter([0.0, 1000.0, 1000.0, 1000.0])

        with patch("lib.retry._retry_config", return_value={"transient_max": 100, "backoff_base_s": 0.01}):
            with patch("lib.retry._timeout_config", return_value={"q.prompt": 5}):
                with patch("lib.retry.time.monotonic", side_effect=lambda: next(monotonic_values)):
                    with patch("lib.retry.time.sleep"):
                        with patch("lib.errors.log_error", side_effect=fake_log_error):
                            with self.assertRaises(WallClockExceeded):
                                with_retry(
                                    always_fails, category="transient", queue="q.prompt",
                                    error_context={"project_state_dir": "/tmp/x", "code": "E-GEN-001"},
                                )

        self.assertEqual(logged["code"], "E-SYS-221")
        self.assertFalse(logged["retryable"])

    def test_wall_clock_exceeded_honors_custom_timeout_code(self):
        logged = {}

        def fake_log_error(**kwargs):
            logged.update(kwargs)

        def always_fails():
            raise ConnectionError("down")

        monotonic_values = iter([0.0, 1000.0, 1000.0, 1000.0])

        with patch("lib.retry._retry_config", return_value={"transient_max": 100, "backoff_base_s": 0.01}):
            with patch("lib.retry._timeout_config", return_value={"q.prompt": 5}):
                with patch("lib.retry.time.monotonic", side_effect=lambda: next(monotonic_values)):
                    with patch("lib.retry.time.sleep"):
                        with patch("lib.errors.log_error", side_effect=fake_log_error):
                            with self.assertRaises(WallClockExceeded):
                                with_retry(
                                    always_fails, category="transient", queue="q.prompt",
                                    error_context={"project_state_dir": "/tmp/x", "timeout_code": "E-SYS-299"},
                                )

        self.assertEqual(logged["code"], "E-SYS-299")


class TestTimeoutConfig(unittest.TestCase):
    def test_strips_comment_key(self):
        from lib.retry import _timeout_config
        fake_json = '{"timeouts": {"_comment": "explanatory text", "q.render": 90}}'
        with patch("lib.retry._CONFIG_PATH") as mock_path:
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = fake_json
            cfg = _timeout_config()
        self.assertNotIn("_comment", cfg)
        self.assertEqual(cfg["q.render"], 90)


if __name__ == "__main__":
    unittest.main()
