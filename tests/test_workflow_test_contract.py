from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGING_WORKFLOWS = (
    REPO_ROOT / ".github" / "workflows" / "package.yml",
    REPO_ROOT / ".github" / "workflows" / "release.yml",
)


class WorkflowTestContractTests(unittest.TestCase):
    def test_packaging_workflows_use_isolated_test_runner(self) -> None:
        for workflow in PACKAGING_WORKFLOWS:
            with self.subTest(workflow=workflow.name):
                contents = workflow.read_text(encoding="utf-8")
                self.assertIn("run: python -m tests.run_isolated", contents)
                self.assertNotIn("python -m unittest discover -s tests", contents)


if __name__ == "__main__":
    unittest.main()
