from __future__ import annotations

from pathlib import Path

from .paths import assets_dir

OPENMOJI_ASSETS = {
    "OpenMoji: Rocket": "1F680.png",
    "OpenMoji: Pizza": "1F355.png",
    "OpenMoji: Rainbow": "1F308.png",
    "OpenMoji: Balloon": "1F388.png",
    "OpenMoji: Soccer Ball": "26BD.png",
    "OpenMoji: Cupcake": "1F9C1.png",
    "OpenMoji: Cat": "1F431.png",
    "OpenMoji: Dog": "1F436.png",
}


def openmoji_paths() -> dict[str, Path]:
    base = assets_dir() / "openmoji"
    return {name: base / filename for name, filename in OPENMOJI_ASSETS.items()}
