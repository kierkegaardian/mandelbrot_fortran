from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .paths import data_dir


@dataclass(frozen=True)
class CurriculumEntry:
    skill: str
    label: str
    topics: tuple[str, ...]
    pdf: str
    source: str


def _load_curriculum() -> list[CurriculumEntry]:
    path = data_dir() / "curriculum_index.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries: list[CurriculumEntry] = []
    for item in raw:
        entries.append(
            CurriculumEntry(
                skill=str(item.get("skill", "")),
                label=str(item.get("label", "")),
                topics=tuple(str(topic) for topic in item.get("topics", [])),
                pdf=str(item.get("pdf", "")),
                source=str(item.get("source", "")),
            )
        )
    return entries


CURRICULUM: list[CurriculumEntry] = _load_curriculum()
BY_SKILL = {entry.skill: entry for entry in CURRICULUM}


def get_curriculum_for_skill(skill: str) -> CurriculumEntry | None:
    return BY_SKILL.get(skill)


def curriculum_entries() -> list[CurriculumEntry]:
    return CURRICULUM


def curriculum_pdf_path(skill: str) -> Path | None:
    entry = BY_SKILL.get(skill)
    if entry is None:
        return None
    path = data_dir() / "reference_pdfs" / entry.pdf
    if not path.exists():
        return None
    return path
