from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import tempfile
from typing import Iterator

from app import db
from scripts.import_template_manifest import import_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]
EARLY_MATH_MANIFESTS = (
    REPO_ROOT / "scripts" / "template_manifests" / "early_math_number_place_value_v1.json",
    REPO_ROOT / "scripts" / "template_manifests" / "early_math_operations_long_v1.json",
    REPO_ROOT / "scripts" / "template_manifests" / "early_math_fractions_ratios_v1.json",
    REPO_ROOT / "scripts" / "template_manifests" / "early_math_money_measurement_time_v1.json",
    REPO_ROOT / "scripts" / "template_manifests" / "early_math_shapes_data_v1.json",
    REPO_ROOT / "scripts" / "template_manifests" / "early_math_integers_order_v1.json",
    REPO_ROOT / "scripts" / "template_manifests" / "early_math_pre_algebra_structure_v1.json",
)


@contextmanager
def imported_early_math_data_dir() -> Iterator[Path]:
    previous = os.environ.get("MANDELQUEST_DATA_DIR")
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["MANDELQUEST_DATA_DIR"] = tmp
        db.init_db()
        for manifest in EARLY_MATH_MANIFESTS:
            import_manifest(manifest)
        yield Path(tmp)
    if previous is None:
        os.environ.pop("MANDELQUEST_DATA_DIR", None)
    else:
        os.environ["MANDELQUEST_DATA_DIR"] = previous
