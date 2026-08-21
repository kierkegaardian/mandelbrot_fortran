from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import ingest_open_textbook_wordproblems as textbook_ingest
from scripts.ingest_open_textbook_wordproblems import (
    SourceCatalogItem,
    extract_answer_key_map,
    extract_word_problem_candidates,
    ingest_source,
    load_catalog,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


class OpenTextbookIngestTests(unittest.TestCase):
    def test_catalog_books_rag_identities_match_corrected_sources(self) -> None:
        catalog = load_catalog(REPO_ROOT / "scripts" / "source_catalog.json")
        by_id = {item.source_id: item for item in catalog}

        roy = by_id["ray_new_practical_arithmetic_1897"]
        self.assertEqual("A New Practical Arithmetic", roy.title)
        self.assertEqual("J. L. H. Roy (1892)", roy.source)
        self.assertEqual("roy_new_practical_arithmetic_1892", roy.books_rag_resource_id)
        self.assertEqual(
            "2e6cdddfdc0d1ecf295fe0e1a91bd112f0430817fbcfa9f92677d4c65e21cc1b",
            roy.books_rag_sha256,
        )

        active_calculus = by_id["active_calculus_single_variable_2e_2025"]
        self.assertEqual(
            "boelkins_active_calculus_single_2e_2025",
            active_calculus.books_rag_resource_id,
        )
        self.assertEqual(
            "686b0f905e84c611da69b37d28ee2d7ba222ff6fc965cac2b7624d8e1f73a110",
            active_calculus.books_rag_sha256,
        )

    def test_catalog_requires_hash_for_books_rag_identity(self) -> None:
        payload = [
            {
                "id": "sample",
                "title": "Sample",
                "pdf_filename": "sample.pdf",
                "books_rag_resource_id": "sample_resource",
                "books_rag_sha256": "not-a-hash",
            }
        ]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "catalog.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid Books RAG SHA-256"):
                load_catalog(path)

    def test_catalog_rejects_partial_books_rag_identity(self) -> None:
        payload = [
            {
                "id": "sample",
                "title": "Sample",
                "pdf_filename": "sample.pdf",
                "books_rag_resource_id": "sample_resource",
            }
        ]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "catalog.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be provided together"):
                load_catalog(path)

    def test_ingest_rejects_pdf_with_wrong_books_rag_hash(self) -> None:
        source = SourceCatalogItem(
            source_id="sample",
            title="Sample",
            source="Test",
            license="CC0",
            url="",
            pdf_filename="sample.pdf",
            answer_key_likely=False,
            books_rag_resource_id="sample_resource",
            books_rag_sha256="0" * 64,
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            reference_dir = root / "reference_pdfs"
            reference_dir.mkdir()
            (reference_dir / "sample.pdf").write_bytes(b"different content")
            with (
                patch.object(textbook_ingest, "data_dir", return_value=root),
                self.assertRaisesRegex(ValueError, "Books RAG identity mismatch"),
            ):
                ingest_source(
                    source,
                    max_candidates=1,
                    refresh_text=False,
                    dry_run=True,
                    min_words=8,
                )

    def test_curriculum_index_uses_corrected_textbook_sources(self) -> None:
        rows = json.loads(
            (REPO_ROOT / "data" / "curriculum_index.json").read_text(encoding="utf-8")
        )
        roy_rows = [row for row in rows if row["pdf"] == "new_practical_arithmetic.pdf"]
        self.assertTrue(roy_rows)
        self.assertTrue(
            all(str(row["source"]).startswith("J. L. H. Roy (1892)") for row in roy_rows)
        )

        active_rows = [
            row for row in rows if row["pdf"] == "active_calculus_single_variable_2e.pdf"
        ]
        self.assertEqual(
            {"calculus_1", "calculus_2", "calculus_slope"},
            {row["skill"] for row in active_rows},
        )
        self.assertTrue(
            all(row["source"] == "Active Calculus Single Variable, Second Edition" for row in active_rows)
        )

    def test_extract_answer_key_map(self) -> None:
        text = """
        Chapter Exercises

        Answer Key
        1. C
        2) 14
        3 - 7/2
        """
        out = extract_answer_key_map(text)
        self.assertEqual(out.get(1), "C")
        self.assertEqual(out.get(2), "14")
        self.assertEqual(out.get(3), "7/2")

    def test_extract_word_problem_candidates_filters_short_blocks(self) -> None:
        text = """
        1. 3 + 4 = ?

        2. A train travels 120 miles in 3 hours. What is the average speed in miles per hour?

        3. Compute 5 * 9.
        """
        out = extract_word_problem_candidates(text, min_words=8)
        self.assertEqual(len(out), 1)
        qnum, body = out[0]
        self.assertEqual(qnum, 2)
        self.assertIn("average speed", body.lower())


if __name__ == "__main__":
    unittest.main()
