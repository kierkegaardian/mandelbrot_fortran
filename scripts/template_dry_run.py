from __future__ import annotations

import argparse
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import random

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import db  # noqa: E402
from app.template_engine import instantiate_template, mc_choices  # noqa: E402
from app import template_engine as te  # noqa: E402


DEFAULT_FORTRAN_SKILLS = {
    "add_subtract",
    "integers",
    "order_of_operations",
    "algebra_linear",
    "pre_algebra",
    "algebra_1",
}


def _expr_with_values(expr: str, values: dict[str, float]) -> str:
    out = str(expr)
    for name in sorted(values.keys(), key=len, reverse=True):
        raw = float(values[name])
        # Keep integer literals readable where possible.
        if abs(raw - round(raw)) < 1e-9:
            literal = str(int(round(raw)))
        else:
            literal = f"{raw:.12f}".rstrip("0").rstrip(".")
        out = re.sub(rf"\b{re.escape(name)}\b", literal, out)
    return out


def _fortran_eval(expr: str, compiler: str) -> float:
    # Reject Python-only ops we don't map in this verifier path.
    if "//" in expr or "%" in expr:
        raise ValueError("unsupported operator for Fortran verifier (// or %)")
    if re.search(r"[^0-9eE\.\+\-\*\/\(\)\s]", expr):
        raise ValueError("expression has unsupported tokens for Fortran verifier")

    source = f"""program verify_expr
  implicit none
  real(8) :: v
  v = {expr}
  write(*,'(F30.15)') v
end program verify_expr
"""
    with tempfile.TemporaryDirectory(prefix="fortran_verify_") as td:
        td_path = Path(td)
        src = td_path / "verify_expr.f90"
        exe = td_path / "verify_expr.out"
        src.write_text(source, encoding="utf-8")
        comp = subprocess.run(
            [compiler, str(src), "-O0", "-o", str(exe)],
            capture_output=True,
            text=True,
        )
        if comp.returncode != 0:
            raise RuntimeError(f"Fortran compile failed: {comp.stderr.strip()}")
        run = subprocess.run([str(exe)], capture_output=True, text=True)
        if run.returncode != 0:
            raise RuntimeError(f"Fortran run failed: {run.stderr.strip()}")
        return float(run.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run all question templates for errors.")
    parser.add_argument("--samples", type=int, default=50, help="Number of instantiations per template")
    parser.add_argument("--skill", default="", help="Optional skill filter")
    parser.add_argument("--include-inactive", action="store_true", help="Include inactive templates")
    parser.add_argument("--mc", action="store_true", help="Also dry-run MC distractor generation")
    parser.add_argument("--require-external-id", action="store_true", help="Fail if any template has no external_id")
    parser.add_argument(
        "--external-id-prefix",
        default="",
        help="Optional prefix filter for external IDs (e.g., math.add_subtract.)",
    )
    parser.add_argument(
        "--fortran-verify",
        action="store_true",
        help="Cross-check arithmetic/algebra template numeric answers with Fortran evaluator",
    )
    parser.add_argument(
        "--fortran-compiler",
        default="gfortran",
        help="Fortran compiler command (default: gfortran)",
    )
    parser.add_argument(
        "--fortran-skills",
        default=",".join(sorted(DEFAULT_FORTRAN_SKILLS)),
        help="Comma-separated skills to verify with Fortran",
    )
    parser.add_argument(
        "--fortran-tol",
        type=float,
        default=1e-8,
        help="Absolute tolerance for Python vs Fortran numeric match",
    )
    args = parser.parse_args()

    db.init_db()
    templates = db.list_all_question_templates(active_only=not args.include_inactive)
    if args.skill:
        templates = [t for t in templates if t.skill == args.skill]
    if args.external_id_prefix:
        prefix = str(args.external_id_prefix)
        templates = [t for t in templates if t.external_id and str(t.external_id).startswith(prefix)]

    rng = random.Random(0)
    total = 0
    failures: list[str] = []
    missing_external_id = 0
    fortran_checked = 0
    fortran_skipped = 0
    fortran_skills = {s.strip() for s in str(args.fortran_skills).split(",") if s.strip()}
    if args.fortran_verify and shutil.which(args.fortran_compiler) is None:
        raise SystemExit(f"Fortran compiler not found: {args.fortran_compiler}")
    for template in templates:
        if not template.external_id:
            missing_external_id += 1
        vars_spec = db.list_template_vars(template.id)
        for i in range(int(args.samples)):
            total += 1
            try:
                inst = instantiate_template(template, vars_spec, rng=rng)
                if args.mc and inst.numeric_answer is not None:
                    choices = mc_choices(inst.numeric_answer, spread=template.choice_spread, rng=rng)
                    if len(set(choices)) != 4:
                        raise ValueError("choices not unique")
                if args.fortran_verify and template.skill in fortran_skills:
                    values = te._sample_with_constraints(template.constraint_expr, vars_spec, rng=rng)
                    py_val = float(te._safe_eval_numeric(template.answer_expr, values))
                    f_expr = _expr_with_values(template.answer_expr, values)
                    try:
                        ft_val = _fortran_eval(f_expr, args.fortran_compiler)
                        fortran_checked += 1
                        if not math.isfinite(ft_val) or abs(py_val - ft_val) > float(args.fortran_tol):
                            raise ValueError(
                                f"Fortran mismatch py={py_val} ft={ft_val} expr={template.answer_expr!r} mapped={f_expr!r}"
                            )
                    except ValueError:
                        fortran_skipped += 1
            except Exception as exc:
                failures.append(
                    f"template_id={template.id} skill={template.skill} subskill={template.subskill} "
                    f"external_id={template.external_id!r} label={template.label!r} "
                    f"sample={i+1} error={type(exc).__name__}: {exc}"
                )
                break

    print(
        f"templates={len(templates)} samples_per={int(args.samples)} total_runs={total} "
        f"failures={len(failures)} missing_external_id={missing_external_id} "
        f"fortran_checked={fortran_checked} fortran_skipped={fortran_skipped}"
    )
    if args.require_external_id and missing_external_id > 0:
        failures.append(f"Missing external IDs for {missing_external_id} template(s).")
    if failures:
        print("\n".join(failures[:50]))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
