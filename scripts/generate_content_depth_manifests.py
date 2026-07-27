from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.content_depth.registry import IN_SCOPE_SKILLS, PROOF_SUBSKILLS  # noqa: E402
from app.content_depth.pilot_specs import pilot_manifest_fields  # noqa: E402
from app import db  # noqa: E402
from app.explanations import explanation_for  # noqa: E402
from app.quiz_engine import generate_question  # noqa: E402
from app.skill_graph import subskills_for  # noqa: E402


OUTPUT_DIR = ROOT / "data" / "content_depth"

CONTEXT_BY_SKILL: dict[str, str] = {
    "counting": "During an inventory count, choose a one-to-one counting model and solve.",
    "place_value": "A school is organizing attendance records; choose a place-value model and solve.",
    "add_subtract": "A classroom is tracking supplies; construct an addition or subtraction model and solve.",
    "multiply": "A coordinator is arranging equal groups; choose an array or group model and solve.",
    "divide": "A team is sharing materials equally; construct a division model and solve.",
    "ratios": "A recipe or scale plan must keep quantities proportional; choose a ratio model and solve.",
    "fractions": "A recipe is divided into equal portions; choose a fraction model and solve.",
    "money": "A family is checking a purchase; select a money model and solve.",
    "financial_literacy": "A household is comparing financial choices; construct the relevant model and decide.",
    "measurement": "A maker project needs an exact measurement; choose the unit model and solve.",
    "geometry_shapes": "A designer must classify or build a shape; choose an attribute model and solve.",
    "data_displays": "A class survey must be represented and interpreted; choose the display model and solve.",
    "data_analysis": "A community survey supports a decision; choose a defensible data model and solve.",
    "integers": "A temperature or elevation change must be modeled; choose a signed-number model and solve.",
    "order_of_operations": "A calculation procedure must be followed reliably; choose the operation order and solve.",
    "pre_algebra": "A changing real quantity needs an algebraic model; construct the relationship and solve.",
    "algebra_linear": "A steady-rate situation needs a linear model; construct the equation and solve.",
    "algebra_1": "A real relationship must be represented algebraically; choose the model and solve.",
    "geometry_area": "A construction plan needs geometric justification; choose the geometric model and solve.",
    "stats_percent": "A report compares a part with a whole; choose a percent model and solve.",
    "stats_mean": "A report needs a fair summary; choose a center model and solve.",
    "stats_probability": "A planning decision depends on chance; construct a probability model and solve.",
}

VERTICAL_CONTEXT: dict[tuple[str, str], str] = {
    ("add_subtract", "Single-digit addition"): "A classroom combines two trays of pencils. Draw or choose the joining-groups model, then solve.",
    ("fractions", "Equivalent fractions"): "A recipe is rescaled. Build equal-area or multiplicative fraction models, then solve.",
    ("data_displays", "Picture and bar graphs"): "A class survey needs a display. Choose the scale and bar/picture model before answering.",
    ("financial_literacy", "Income, gifts, wants, and needs"): "A child is identifying a money source, a contextual need or want, or a useful job skill. Select the matching model and decide.",
    ("financial_literacy", "Budget percentages, net worth, interest, and incentives"): "A family compares a budget and debt offer. Build the percent or net-worth model before deciding.",
    ("pre_algebra", "Two-step equations and inequalities"): "A service charges a fixed fee plus a rate. Construct a two-step equation or inequality, then solve.",
    ("algebra_linear", "Slope from points"): "A ramp designer compares rise with run. Construct the rate-of-change model, then solve.",
    ("algebra_1", "Systems by elimination"): "Two ticket plans produce the same totals. Construct a system and eliminate one variable to solve.",
    ("geometry_area", "Triangle congruence criteria"): "A bridge frame uses matching triangular braces. Select sufficient corresponding facts and justify congruence.",
    ("data_analysis", "Sample inferences from displays"): "A community survey informs a town decision. Check the sample and display before making an inference.",
}


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    expected: set[Path] = set()
    # A fresh in-memory DB deliberately disables local template selection so
    # generated manifests are reproducible on every developer machine.
    with db.override_db_config(db.DbConfig(path=":memory:")):
        for skill in IN_SCOPE_SKILLS:
            path = OUTPUT_DIR / f"{skill}.json"
            payload = {
                "version": 1,
                "skill": skill,
                "subskills": [_subskill_payload(skill, subskill) for subskill in subskills_for(skill)],
            }
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            expected.add(path)
    for stale in OUTPUT_DIR.glob("*.json"):
        if stale not in expected:
            stale.unlink()
    print(f"skills={len(IN_SCOPE_SKILLS)} subskills={sum(len(subskills_for(skill)) for skill in IN_SCOPE_SKILLS)}")
    return 0


def _subskill_payload(skill: str, subskill: str) -> dict[str, object]:
    slug = _slug(subskill)
    base = f"depth.v1.{skill}.{slug}"
    context = VERTICAL_CONTEXT.get((skill, subskill), CONTEXT_BY_SKILL.get(skill, "Choose a useful mathematical model and solve."))
    archetypes: list[dict[str, str]] = [
        {"id": f"{base}.concept", "reasoning_kind": "conceptual", "prompt_prefix": f"Which mental model best supports {subskill}?"},
        {"id": f"{base}.procedure", "reasoning_kind": "procedural"},
        {"id": f"{base}.transfer", "reasoning_kind": "transfer"},
        {"id": f"{base}.application", "reasoning_kind": "application", "prompt_prefix": context},
    ]
    proof = None
    if subskill in PROOF_SUBSKILLS:
        archetypes.append({"id": f"{base}.proof", "reasoning_kind": "proof"})
        proof = _proof_payload(subskill)
    explanation = explanation_for(skill, subskill)
    pilot_fields = pilot_manifest_fields(skill, subskill, base)
    worked_example = (
        pilot_fields["worked_example"] if pilot_fields is not None
        else _worked_example(skill, subskill, explanation.try_this)
    )
    misconceptions = (
        pilot_fields["misconceptions"] if pilot_fields is not None
        else [
            {
                "code": f"{slug}.model_confusion",
                "feedback": explanation.common_mistake or f"The model for {subskill} was selected incorrectly.",
                "hint": explanation.mental_model or explanation.how_short,
                "recovery_archetype_id": f"{base}.concept",
            },
            {
                "code": f"{slug}.procedure_slip",
                "feedback": f"The setup is close, but a step in {subskill} changed the result.",
                "hint": explanation.try_this or explanation.how_short,
                "recovery_archetype_id": f"{base}.procedure",
            },
        ]
    )
    return {
        "subskill": subskill,
        "content_status": "ready" if pilot_fields is not None else "scaffold",
        "archetypes": archetypes,
        "worked_example": worked_example,
        "misconceptions": misconceptions,
        **({"proof": proof} if proof is not None else {}),
    }


def _worked_example(skill: str, subskill: str, try_this: str) -> dict[str, object]:
    questions = []
    for index in range(3):
        random.seed(_stable_seed(skill, subskill, index))
        questions.append(generate_question(skill, 2, "typed", subskill=subskill))
    return {
        "title": f"Worked example: {subskill}",
        "steps": [
            {
                "stage": "model",
                "prompt": questions[0].prompt,
                "explanation": f"{questions[0].explanation} Answer: {questions[0].correct_answer}",
                "expected_answer": questions[0].correct_answer,
            },
            {
                "stage": "guided",
                "prompt": questions[1].prompt,
                "explanation": try_this or questions[1].explanation,
                "expected_answer": questions[1].correct_answer,
            },
            {
                "stage": "transfer",
                "prompt": questions[2].prompt,
                "explanation": "Solve independently, then compare with the worked strategy.",
                "expected_answer": questions[2].correct_answer,
            },
        ],
    }


def _proof_payload(subskill: str) -> dict[str, object]:
    details = {
        "Angles in lines and triangles": (
            "Prove the missing triangle angle relationship from parallel-line angle facts.",
            (("given", "The marked lines are parallel.", "Given", ()),
             ("corresponding", "The corresponding angles are congruent.", "Corresponding angles theorem", ("given",)),
             ("vertical", "The vertical angles are congruent.", "Vertical angles theorem", ("corresponding",)),
             ("conclusion", "The target angles have equal measure.", "Transitive property", ("vertical",))),
        ),
        "Triangle congruence criteria": (
            "Prove the two triangular braces are congruent using the marked corresponding facts.",
            (("side_one", "The first pair of corresponding sides is congruent.", "Given", ()),
             ("angle", "The included angles are congruent.", "Given", ()),
             ("side_two", "The second pair of corresponding sides is congruent.", "Given", ()),
             ("conclusion", "The triangles are congruent.", "SAS congruence", ("side_one", "angle", "side_two"))),
        ),
        "Transformations and congruence": (
            "Prove a translated figure is congruent to its original.",
            (("map", "Every vertex moves by the same translation vector.", "Definition of translation", ()),
             ("length", "Corresponding side lengths are preserved.", "Translations preserve distance", ("map",)),
             ("angle", "Corresponding angle measures are preserved.", "Translations preserve angles", ("map",)),
             ("conclusion", "The image is congruent to the original figure.", "Rigid-motion definition", ("length", "angle"))),
        ),
        "Similarity and scale factor": (
            "Prove two triangles are similar from their corresponding measurements.",
            (("ratio_one", "One pair of corresponding sides has the stated scale factor.", "Given measurements", ()),
             ("ratio_two", "A second pair has the same scale factor.", "Compute corresponding ratios", ()),
             ("angle", "The included angles are congruent.", "Given", ()),
             ("conclusion", "The triangles are similar.", "SAS similarity", ("ratio_one", "ratio_two", "angle"))),
        ),
        "Analytic geometry and coordinate proofs": (
            "Use coordinates to prove the described quadrilateral has the claimed property.",
            (("coordinates", "List the relevant endpoint coordinates.", "Given", ()),
             ("slopes", "Compute the slopes of opposite sides.", "Slope formula", ("coordinates",)),
             ("parallel", "The opposite sides are parallel.", "Equal slopes imply parallel lines", ("slopes",)),
             ("conclusion", "The coordinate evidence proves the claimed property.", "Definition of the quadrilateral", ("parallel",))),
        ),
    }
    prompt, steps = details[subskill]
    required = [
        {"id": step_id, "statement": statement, "reason": reason, "depends_on": list(depends)}
        for step_id, statement, reason, depends in steps
    ]
    distractors = [
        {"id": "distractor_guess", "statement": "The diagram looks accurate, so the claim is true.", "reason": "Visual appearance", "depends_on": []},
        {"id": "distractor_converse", "statement": "Reverse an unrelated theorem to reach the claim.", "reason": "Invalid converse", "depends_on": []},
    ]
    return {"prompt": prompt, "required_steps": required, "distractor_steps": distractors}


def _stable_seed(skill: str, subskill: str, index: int) -> int:
    digest = hashlib.sha256(f"{skill}|{subskill}|{index}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


if __name__ == "__main__":
    raise SystemExit(main())
