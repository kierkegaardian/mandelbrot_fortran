from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ..paths import repo_root
from .models import (
    ArchetypeSpec,
    ContentStatus,
    DepthSpec,
    MisconceptionSpec,
    ProofSpec,
    ProofStep,
    ReasoningKind,
    WorkedExample,
    WorkedExampleStep,
)


IN_SCOPE_SKILLS: tuple[str, ...] = (
    "counting", "place_value", "add_subtract", "multiply", "divide", "ratios", "fractions",
    "long_addition", "long_subtraction", "long_multiplication", "long_division", "money", "measurement",
    "financial_literacy", "geometry_shapes", "data_displays", "data_analysis", "integers",
    "order_of_operations", "pre_algebra", "algebra_linear", "algebra_1", "geometry_area",
    "stats_percent", "stats_mean", "stats_probability",
)

PROOF_SUBSKILLS: frozenset[str] = frozenset(
    {
        "Angles in lines and triangles",
        "Triangle congruence criteria",
        "Transformations and congruence",
        "Similarity and scale factor",
        "Analytic geometry and coordinate proofs",
    }
)


class DepthManifestError(ValueError):
    pass


def _manifest_dir() -> Path:
    return repo_root() / "data" / "content_depth"


@lru_cache(maxsize=1)
def load_depth_specs() -> dict[tuple[str, str], DepthSpec]:
    specs: dict[tuple[str, str], DepthSpec] = {}
    directory = _manifest_dir()
    if not directory.exists():
        return specs
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or int(payload.get("version", 0)) != 1:
            raise DepthManifestError(f"Unsupported depth manifest: {path}")
        skill = str(payload.get("skill", "")).strip()
        if skill not in IN_SCOPE_SKILLS:
            raise DepthManifestError(f"Out-of-scope depth skill in {path}: {skill}")
        rows = payload.get("subskills")
        if not isinstance(rows, list):
            raise DepthManifestError(f"Depth manifest subskills must be a list: {path}")
        for raw in rows:
            spec = _parse_spec(skill, raw, path)
            key = (spec.skill, spec.subskill)
            if key in specs:
                raise DepthManifestError(f"Duplicate depth spec: {key}")
            specs[key] = spec
    _validate_unique_archetypes(specs)
    return specs


def depth_spec_for(skill: str, subskill: str | None) -> DepthSpec | None:
    if not subskill:
        return None
    return load_depth_specs().get((skill, subskill))


def depth_ready_for(skill: str, subskill: str | None) -> bool:
    spec = depth_spec_for(skill, subskill)
    return spec is not None and spec.content_status is ContentStatus.READY


def in_scope_pairs() -> tuple[tuple[str, str], ...]:
    from ..skill_graph import subskills_for

    return tuple((skill, subskill) for skill in IN_SCOPE_SKILLS for subskill in subskills_for(skill))


def clear_depth_spec_cache() -> None:
    load_depth_specs.cache_clear()


def _parse_spec(skill: str, raw: object, path: Path) -> DepthSpec:
    if not isinstance(raw, dict):
        raise DepthManifestError(f"Invalid subskill row in {path}")
    subskill = str(raw.get("subskill", "")).strip()
    archetypes = tuple(_parse_archetype(item, path) for item in _as_list(raw.get("archetypes"), path))
    example_raw = raw.get("worked_example")
    if not isinstance(example_raw, dict):
        raise DepthManifestError(f"Missing worked example for {skill}/{subskill}")
    steps = tuple(_parse_example_step(item, path) for item in _as_list(example_raw.get("steps"), path))
    worked = WorkedExample(str(example_raw.get("title", subskill)), steps)
    misconceptions = tuple(_parse_misconception(item, path) for item in _as_list(raw.get("misconceptions"), path))
    proof = _parse_proof(raw.get("proof"), path)
    try:
        content_status = ContentStatus(str(raw.get("content_status", ContentStatus.SCAFFOLD.value)))
    except ValueError as exc:
        raise DepthManifestError(f"Invalid content status for {skill}/{subskill}") from exc
    spec = DepthSpec(skill, subskill, content_status, archetypes, worked, misconceptions, proof)
    _validate_spec(spec, path)
    return spec


def _parse_archetype(raw: object, path: Path) -> ArchetypeSpec:
    if not isinstance(raw, dict):
        raise DepthManifestError(f"Invalid archetype in {path}")
    try:
        kind = ReasoningKind(str(raw["reasoning_kind"]))
    except (KeyError, ValueError) as exc:
        raise DepthManifestError(f"Invalid reasoning kind in {path}") from exc
    return ArchetypeSpec(str(raw.get("id", "")).strip(), kind, str(raw.get("prompt_prefix", "")))


def _parse_example_step(raw: object, path: Path) -> WorkedExampleStep:
    if not isinstance(raw, dict):
        raise DepthManifestError(f"Invalid worked-example step in {path}")
    answer = raw.get("expected_answer")
    return WorkedExampleStep(
        str(raw.get("stage", "")), str(raw.get("prompt", "")), str(raw.get("explanation", "")),
        None if answer is None else str(answer),
    )


def _parse_misconception(raw: object, path: Path) -> MisconceptionSpec:
    if not isinstance(raw, dict):
        raise DepthManifestError(f"Invalid misconception in {path}")
    return MisconceptionSpec(
        str(raw.get("code", "")), str(raw.get("feedback", "")), str(raw.get("hint", "")),
        str(raw.get("recovery_archetype_id", "")),
    )


def _parse_proof(raw: object, path: Path) -> ProofSpec | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise DepthManifestError(f"Invalid proof in {path}")
    required = tuple(_parse_proof_step(item, path) for item in _as_list(raw.get("required_steps"), path))
    distractors = tuple(_parse_proof_step(item, path) for item in _as_list(raw.get("distractor_steps"), path))
    return ProofSpec(str(raw.get("prompt", "")), required, distractors)


def _parse_proof_step(raw: object, path: Path) -> ProofStep:
    if not isinstance(raw, dict):
        raise DepthManifestError(f"Invalid proof step in {path}")
    depends = raw.get("depends_on", [])
    if not isinstance(depends, list):
        raise DepthManifestError(f"Invalid proof dependencies in {path}")
    return ProofStep(
        str(raw.get("id", "")), str(raw.get("statement", "")), str(raw.get("reason", "")),
        tuple(str(item) for item in depends),
    )


def _as_list(raw: object, path: Path) -> list[object]:
    if not isinstance(raw, list):
        raise DepthManifestError(f"Expected list in {path}")
    return raw


def _validate_unique_archetypes(specs: dict[tuple[str, str], DepthSpec]) -> None:
    seen: set[str] = set()
    for spec in specs.values():
        for archetype in spec.archetypes:
            if not archetype.archetype_id or archetype.archetype_id in seen:
                raise DepthManifestError(f"Duplicate or empty archetype id: {archetype.archetype_id}")
            seen.add(archetype.archetype_id)


def _validate_spec(spec: DepthSpec, path: Path) -> None:
    if not spec.subskill:
        raise DepthManifestError(f"Empty subskill in {path}")
    ids = {item.archetype_id for item in spec.archetypes}
    if len(ids) != len(spec.archetypes) or "" in ids:
        raise DepthManifestError(f"Duplicate or empty archetype id for {spec.skill}/{spec.subskill}")
    if any(item.reasoning_kind is ReasoningKind.LEGACY for item in spec.archetypes):
        raise DepthManifestError(f"Depth archetypes cannot be legacy for {spec.skill}/{spec.subskill}")
    stages = tuple(step.stage for step in spec.worked_example.steps)
    if stages != ("model", "guided", "transfer"):
        raise DepthManifestError(f"Invalid worked-example progression for {spec.skill}/{spec.subskill}")
    for step in spec.worked_example.steps:
        if not step.prompt or not step.explanation:
            raise DepthManifestError(f"Incomplete worked-example step for {spec.skill}/{spec.subskill}")
    misconception_codes: set[str] = set()
    for item in spec.misconceptions:
        if not item.code or item.code in misconception_codes or not item.feedback or not item.hint:
            raise DepthManifestError(f"Invalid misconception for {spec.skill}/{spec.subskill}")
        if item.recovery_archetype_id not in ids:
            raise DepthManifestError(
                f"Unresolvable recovery archetype for {spec.skill}/{spec.subskill}: {item.recovery_archetype_id}"
            )
        misconception_codes.add(item.code)
    if spec.proof is None:
        return
    required_ids = {item.step_id for item in spec.proof.required_steps}
    bank_ids = {item.step_id for item in spec.proof.step_bank}
    if len(bank_ids) != len(spec.proof.step_bank) or "" in bank_ids:
        raise DepthManifestError(f"Duplicate or empty proof step for {spec.skill}/{spec.subskill}")
    for step in spec.proof.step_bank:
        if not step.statement or not step.reason:
            raise DepthManifestError(f"Incomplete proof pair for {spec.skill}/{spec.subskill}")
    for step in spec.proof.required_steps:
        if any(dep not in required_ids for dep in step.depends_on):
            raise DepthManifestError(f"Invalid proof dependency for {spec.skill}/{spec.subskill}")
    resolved: set[str] = set()
    pending = list(spec.proof.required_steps)
    while pending:
        ready = [step for step in pending if set(step.depends_on) <= resolved]
        if not ready:
            raise DepthManifestError(f"Cyclic proof dependencies for {spec.skill}/{spec.subskill}")
        for step in ready:
            resolved.add(step.step_id)
            pending.remove(step)
