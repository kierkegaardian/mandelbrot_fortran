from __future__ import annotations

import argparse
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Source:
    url: str
    filename: str
    kind: str  # historical or historical_keys


SOURCES: list[Source] = [
    # Additional SAT/GRE PDFs from a public GitHub repo.
    Source(
        url="https://raw.githubusercontent.com/Hazrat-Ali9/SAT-GRE-GMAT-TOFEL-PTE-ACT-DET/main/practice_test_8_cd.pdf",
        filename="github_hazrat_sat_practice_test_8_cd.pdf",
        kind="historical",
    ),
    # Supplemental ETS GRE references (public PDF endpoints).
    Source(
        url="https://www.ets.org/pdfs/gre/gre-math-conventions.pdf",
        filename="ets_gre_math_conventions.pdf",
        kind="historical",
    ),
]


def _is_pdf(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(4) == b"%PDF"
    except OSError:
        return False


def _download(url: str, out_path: Path) -> bool:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["curl", "-L", "--fail", "--silent", "--show-error", "--max-time", "45", "-o", str(out_path), url]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        if out_path.exists():
            out_path.unlink(missing_ok=True)
        return False
    if not _is_pdf(out_path):
        out_path.unlink(missing_ok=True)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull additional public SAT/GRE PDFs with PDF signature checks.")
    parser.add_argument("--root", default="data/reference_pdfs", help="Root reference_pdfs directory")
    parser.add_argument("--refresh", action="store_true", help="Re-download even when file already exists")
    args = parser.parse_args()

    root = Path(args.root)
    added = 0
    kept = 0
    failed = 0

    for src in SOURCES:
        out_dir = root / src.kind
        out_path = out_dir / src.filename
        if out_path.exists() and not args.refresh:
            kept += 1
            continue

        tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        if _download(src.url, tmp_path):
            shutil.move(str(tmp_path), str(out_path))
            added += 1
        else:
            tmp_path.unlink(missing_ok=True)
            failed += 1

    print(f"added={added} kept={kept} failed={failed} root={root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
