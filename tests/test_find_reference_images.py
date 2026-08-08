"""Unit tests for scripts/find_reference_images.py's pure logic (license
gating, CC-URL parsing, provider fallback order). Network-touching provider
functions (_wikimedia_candidates/_nasa_candidates/_archive_org_candidates)
are mocked - these tests never make a real HTTP call."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import find_reference_images as fri


class TestLicenseIsReusable(unittest.TestCase):
    def test_accepts_cc0(self):
        self.assertTrue(fri.license_is_reusable("CC0"))

    def test_accepts_cc_by(self):
        self.assertTrue(fri.license_is_reusable("CC BY-SA 4.0"))

    def test_accepts_public_domain(self):
        self.assertTrue(fri.license_is_reusable("Public Domain"))

    def test_rejects_nc(self):
        self.assertFalse(fri.license_is_reusable("CC BY-NC 4.0"))

    def test_rejects_nd(self):
        self.assertFalse(fri.license_is_reusable("CC BY-ND 4.0"))

    def test_rejects_empty(self):
        self.assertFalse(fri.license_is_reusable(""))

    def test_rejects_none(self):
        self.assertFalse(fri.license_is_reusable(None))

    def test_rejects_unrelated_license(self):
        self.assertFalse(fri.license_is_reusable("All Rights Reserved"))

    def test_case_insensitive(self):
        self.assertTrue(fri.license_is_reusable("cc0"))
        self.assertFalse(fri.license_is_reusable("cc by-nc 2.0"))


class TestLicenseShortFromCcUrl(unittest.TestCase):
    def test_cc0_zero_path(self):
        self.assertEqual(fri._license_short_from_cc_url("https://creativecommons.org/publicdomain/zero/1.0/"), "cc0")

    def test_cc_by_sa(self):
        self.assertEqual(fri._license_short_from_cc_url("https://creativecommons.org/licenses/by-sa/4.0/"), "cc by-sa")

    def test_cc_by_nc_nd_still_parsed_but_later_rejected(self):
        # Parsing succeeds even for a non-reusable license - the rejection
        # happens in license_is_reusable(), not here. This mirrors the real
        # Archive.org failure mode this function was written to handle
        # (a by-nc-nd item was observed in real search results).
        short = fri._license_short_from_cc_url("https://creativecommons.org/licenses/by-nc-nd/4.0/")
        self.assertEqual(short, "cc by-nc-nd")
        self.assertFalse(fri.license_is_reusable(short))

    def test_unrecognized_url_returns_empty(self):
        self.assertEqual(fri._license_short_from_cc_url("https://example.com/not-a-license"), "")


class TestFindBestCandidate(unittest.TestCase):
    """PROVIDERS binds function objects at module-load time, so patching
    fri._wikimedia_candidates etc. by name after the fact wouldn't affect
    what find_best_candidate() actually iterates over - patch fri.PROVIDERS
    itself instead, which is what find_best_candidate() reads."""

    def test_tries_providers_in_order_first_reusable_wins(self):
        wikimedia_reject = {
            "source": "wikimedia_commons", "source_title": "t1", "source_url": "u1",
            "file_url": "f1", "mime": "image/jpeg", "width": 2000, "height": 1000,
            "license_short": "", "license_url": "", "attribution": "",
        }
        nasa_accept = {
            "source": "nasa", "source_title": "t2", "source_url": "u2",
            "file_url": "f2", "mime": "image/jpeg", "width": None, "height": None,
            "license_short": "public domain", "license_url": "", "attribution": "",
        }
        fake_providers = [
            ("wikimedia_commons", lambda q: [wikimedia_reject]),
            ("nasa", lambda q: [nasa_accept]),
            ("archive_org", lambda q: []),
        ]
        with patch.object(fri, "PROVIDERS", fake_providers):
            best = fri.find_best_candidate("test query")
        self.assertIsNotNone(best)
        self.assertEqual(best["source"], "nasa")

    def test_rejects_below_min_width_when_known(self):
        too_small = {
            "source": "wikimedia_commons", "source_title": "t", "source_url": "u",
            "file_url": "f", "mime": "image/jpeg", "width": 500, "height": 300,
            "license_short": "cc0", "license_url": "", "attribution": "",
        }
        fake_providers = [("wikimedia_commons", lambda q: [too_small])]
        with patch.object(fri, "PROVIDERS", fake_providers):
            best = fri.find_best_candidate("test query")
        self.assertIsNone(best)

    def test_none_width_not_rejected_missing_pixel_data_providers(self):
        # NASA/Archive.org don't supply width from this endpoint - must not
        # be penalized for data the provider never had.
        no_width = {
            "source": "nasa", "source_title": "t", "source_url": "u",
            "file_url": "f", "mime": "image/jpeg", "width": None, "height": None,
            "license_short": "public domain", "license_url": "", "attribution": "",
        }
        fake_providers = [("nasa", lambda q: [no_width])]
        with patch.object(fri, "PROVIDERS", fake_providers):
            best = fri.find_best_candidate("test query")
        self.assertIsNotNone(best)

    def test_no_candidates_anywhere_returns_none(self):
        fake_providers = [
            ("wikimedia_commons", lambda q: []),
            ("nasa", lambda q: []),
            ("archive_org", lambda q: []),
        ]
        with patch.object(fri, "PROVIDERS", fake_providers):
            best = fri.find_best_candidate("test query")
        self.assertIsNone(best)

    def test_unsupported_mime_rejected(self):
        pdf_result = {
            "source": "wikimedia_commons", "source_title": "t", "source_url": "u",
            "file_url": "f", "mime": "application/pdf", "width": 5000, "height": 5000,
            "license_short": "cc0", "license_url": "", "attribution": "",
        }
        fake_providers = [("wikimedia_commons", lambda q: [pdf_result])]
        with patch.object(fri, "PROVIDERS", fake_providers):
            best = fri.find_best_candidate("test query")
        self.assertIsNone(best)


if __name__ == "__main__":
    unittest.main()
