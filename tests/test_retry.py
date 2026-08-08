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
from lib.retry import NonRetryable, with_retry


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


if __name__ == "__main__":
    unittest.main()
