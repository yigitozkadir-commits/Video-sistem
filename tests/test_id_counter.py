"""Unit tests for scripts/lib/id_counter.py (review finding B-01)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from lib.id_counter import next_id


class TestNextId(unittest.TestCase):
    def test_starts_at_one_for_new_file(self):
        with tempfile.TemporaryDirectory() as td:
            counter = Path(td) / ".counter"
            self.assertEqual(next_id(counter), 1)

    def test_increments_monotonically(self):
        with tempfile.TemporaryDirectory() as td:
            counter = Path(td) / ".counter"
            values = [next_id(counter) for _ in range(5)]
            self.assertEqual(values, [1, 2, 3, 4, 5])

    def test_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            counter = Path(td) / "nested" / "state" / ".counter"
            self.assertEqual(next_id(counter), 1)
            self.assertTrue(counter.exists())

    def test_survives_concurrent_processes_with_no_duplicates(self):
        import multiprocessing

        def worker(counter_path: str, q, n_calls: int) -> None:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
            from lib.id_counter import next_id as _next_id
            for _ in range(n_calls):
                q.put(_next_id(Path(counter_path)))

        with tempfile.TemporaryDirectory() as td:
            counter = Path(td) / ".counter"
            q = multiprocessing.Queue()
            n_procs, n_calls = 6, 25
            procs = [
                multiprocessing.Process(target=worker, args=(str(counter), q, n_calls))
                for _ in range(n_procs)
            ]
            for p in procs:
                p.start()
            for p in procs:
                p.join()
            values = []
            while not q.empty():
                values.append(q.get())
            self.assertEqual(len(values), n_procs * n_calls)
            self.assertEqual(len(values), len(set(values)), "duplicate IDs allocated under concurrency")
            self.assertEqual(sorted(values), list(range(1, n_procs * n_calls + 1)))


if __name__ == "__main__":
    unittest.main()
