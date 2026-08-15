from __future__ import annotations

from collections.abc import Callable
import gc
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings

from app import db
from scripts import generate_syllogism_word_manifest as syllogism_manifest
from scripts import ingest_open_textbook_wordproblems as textbook_ingest


class ScriptDbConnectionLifetimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._data_dir = Path(self._tmp.name)
        self.enterContext(
            db.override_db_config(db.DbConfig(path=str(self._data_dir / "test_app.db")))
        )
        db.init_db()
        gc.collect()

    def test_open_textbook_ingest_closes_both_connections(self) -> None:
        reference_dir = self._data_dir / "reference_pdfs"
        reference_dir.mkdir()
        (reference_dir / "sample.pdf").write_bytes(b"%PDF-placeholder")
        ingest_dir = self._data_dir / "ingest" / "open_textbooks" / "sample"
        ingest_dir.mkdir(parents=True)
        (ingest_dir / "pdftotext.txt").write_text(
            "1. A train travels 120 miles in 3 hours. "
            "What is the average speed in miles per hour?\n",
            encoding="utf-8",
        )
        source = textbook_ingest.SourceCatalogItem(
            source_id="sample",
            title="Sample",
            source="test",
            license="CC0",
            url="",
            pdf_filename="sample.pdf",
            answer_key_likely=False,
            books_rag_resource_id="",
            books_rag_sha256="",
        )

        with patch.object(textbook_ingest, "data_dir", return_value=self._data_dir):
            resource_warnings = self._capture_resource_warnings(
                lambda: textbook_ingest.ingest_source(
                    source,
                    max_candidates=1,
                    refresh_text=False,
                    dry_run=False,
                    min_words=8,
                )
            )

        self.assertEqual([], resource_warnings)

    def test_syllogism_manifest_helpers_close_both_connections(self) -> None:
        book = db.create_book("Sample", "test", "sample.pdf", "2026-08-08T00:00:00+00:00")
        candidate_id = db.add_exercise_candidate(
            book.id,
            "sample:1",
            "All sample statements are test statements.",
            "new",
            "2026-08-08T00:00:00+00:00",
        )

        def exercise_helpers() -> None:
            rows = syllogism_manifest._fetch_candidates([], "new", 10)
            self.assertEqual(candidate_id, rows[0]["candidate_id"])
            syllogism_manifest._mark_templated([candidate_id])

        resource_warnings = self._capture_resource_warnings(exercise_helpers)

        self.assertEqual([], resource_warnings)

    def _capture_resource_warnings(
        self,
        operation: Callable[[], object],
    ) -> list[warnings.WarningMessage]:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ResourceWarning)
            operation()
            gc.collect()
        return [item for item in caught if issubclass(item.category, ResourceWarning)]


if __name__ == "__main__":
    unittest.main()
