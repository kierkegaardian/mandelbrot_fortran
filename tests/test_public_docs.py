from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import unquote, urlsplit

from app.content_depth.audit import build_depth_audit


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"


class _LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        link_attribute = "src" if tag in {"img", "script"} else "href"
        for name, value in attrs:
            if name == link_attribute and value:
                self.links.append(value)


class PublicDocsTests(unittest.TestCase):
    def test_all_local_html_links_stay_in_the_pages_artifact(self) -> None:
        docs_root = DOCS_ROOT.resolve()
        failures: list[str] = []

        for source in sorted(DOCS_ROOT.glob("*.html")):
            parser = _LinkCollector()
            parser.feed(source.read_text(encoding="utf-8"))
            parser.close()

            for link in parser.links:
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target = (source.parent / unquote(parsed.path)).resolve()
                if not target.is_relative_to(docs_root):
                    failures.append(f"{source.name}: link escapes docs artifact: {link}")
                elif not target.exists():
                    failures.append(f"{source.name}: missing local target: {link}")

        self.assertEqual([], failures, "\n".join(failures))

    def test_public_copy_keeps_family_sync_inside_the_beta_boundary(self) -> None:
        index = (DOCS_ROOT / "index.html").read_text(encoding="utf-8")
        privacy = (DOCS_ROOT / "privacy.html").read_text(encoding="utf-8")
        support = (DOCS_ROOT / "support.html").read_text(encoding="utf-8")
        coverage = (DOCS_ROOT / "coverage.html").read_text(encoding="utf-8")
        checklist = (DOCS_ROOT / "V1_RELEASE_CHECKLIST.md").read_text(encoding="utf-8")

        self.assertIn("Family Sync (Beta)", index)
        self.assertIn("Local-only is the default", index)
        self.assertIn("no hosted sync service ships with public v1", index)
        self.assertIn("Family Sync is an experimental, operator-configured beta", privacy)
        self.assertIn("public builds include no sync server", privacy)
        self.assertIn("Local-only is the default", support)
        self.assertIn("No hosted cloud/LAN sync service ships with v1", support)
        self.assertIn("local-first review", coverage)
        self.assertIn("Family Sync is labeled beta, defaults off", checklist)
        self.assertIn("Pages uses GitHub Actions as its publishing source", checklist)

    def test_pages_workflow_validates_and_deploys_the_docs_directory(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "pages.yml").read_text(
            encoding="utf-8"
        )

        for expected in (
            "pages: write",
            "id-token: write",
            "actions/configure-pages@v5",
            "python -m unittest tests.test_public_docs",
            "actions/upload-pages-artifact@v4",
            "path: docs",
            "actions/deploy-pages@v4",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, workflow)

    def test_curriculum_depth_copy_matches_the_substantive_audit(self) -> None:
        report = build_depth_audit(seeds_per_archetype=25)
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        todo = (REPO_ROOT / "TODO.md").read_text(encoding="utf-8")
        coverage = (DOCS_ROOT / "coverage.html").read_text(encoding="utf-8")
        counts = f"`{report.ready_count} ready / {report.thin_count} thin / {report.missing_count} missing`"

        self.assertEqual(len(report.rows), 158)
        self.assertIn(counts, readme)
        self.assertIn(counts, todo)
        self.assertIn("eleven depth-ready subskills", coverage)
        self.assertIn("one advanced finance pilot", coverage)


if __name__ == "__main__":
    unittest.main()
