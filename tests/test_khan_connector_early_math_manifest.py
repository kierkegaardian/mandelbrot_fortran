from __future__ import annotations

import unittest

from app.early_math_catalog import EARLY_MATH_SKILLS
from scripts.generate_khan_connector_early_math_manifest import build_catalog, build_manifest


class KhanConnectorEarlyMathManifestTests(unittest.TestCase):
    def test_manifest_has_unique_external_ids_and_early_math_skills(self) -> None:
        items = build_manifest()
        external_ids = [str(item["external_id"]) for item in items]
        self.assertEqual(len(external_ids), len(set(external_ids)))
        self.assertGreater(len(items), 0)
        for item in items:
            with self.subTest(external_id=item["external_id"]):
                self.assertIn(str(item["skill"]), EARLY_MATH_SKILLS)

    def test_catalog_groups_cover_all_manifest_items(self) -> None:
        items = build_manifest()
        catalog = build_catalog()
        self.assertGreater(len(catalog["groups"]), 0)
        grouped_ids = {
            external_id
            for group in catalog["groups"]
            for external_id in group["external_ids"]
        }
        self.assertEqual(grouped_ids, {str(item["external_id"]) for item in items})

    def test_manifest_covers_core_arithmetic_snapshot_skills(self) -> None:
        items = build_manifest()
        self.assertGreaterEqual(len(items), 65)
        skills = {str(item["skill"]) for item in items}
        self.assertTrue(
            {
                "add_subtract",
                "fractions",
                "measurement",
                "money",
                "multiply",
                "order_of_operations",
                "place_value",
                "pre_algebra",
                "ratios",
                "long_addition",
                "long_subtraction",
                "long_multiplication",
            }.issubset(skills)
        )


if __name__ == "__main__":
    unittest.main()
