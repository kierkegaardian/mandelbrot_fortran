I'll review the Wave 1C plan against the repo's existing depth-pilot and money patterns—findings first, evidence-backed, no file edits.Gathering evidence from existing pilots, money manifests, and readiness criteria.# Wave 1C Plan Review — `g1_money` / Dollar-coin values

**Verdict: BLOCK** (direction is sound; two verification traps and one incomplete registration surface must be fixed in the plan before implement).

---

## Findings (must-fix first)

### 1. Frozen audit counters will break existing tests
**Severity: must-fix · Test risk**

Plan targets `15 ready / 143 thin / 0 missing` but does not say to update prior pins. These still assert `14 / 144`:

| File | Assertion |
|------|-----------|
| `tests/test_content_depth_framework.py` | `ready_count == 14`, `thin_count == 144` |
| `tests/test_content_depth_place_value.py` | `(14, 144, 0)` |
| `tests/test_content_depth_add_subtract.py` | `(14, 144, 0)` |

New money tests alone leave full discovery red.

**Minimal plan change:** Explicitly bump those three pins (plus README/TODO/CONTINUITY/`docs/coverage.html`) to `15 / 143 / 0`.

---

### 2. Cumulative-check design cannot copy the add/subtract pattern
**Severity: must-fix · Cumulative-check risk**

Evidence from `build_texas_cumulative_quiz` + G1 goal order:

| Check | Window |
|-------|--------|
| **1** | `g1_place_value`, `g1_add_subtract` only — **no money** |
| **2** | earlier includes `g1_money`; **current** is `g1_personal_finance` (still scaffold) |
| **3+** | money earlier + shapes/data still mostly thin |

`tests/test_content_depth_add_subtract.py` uses check **1** and asserts *all* questions are non-`LEGACY` with `scaffold_steps is None`. That works only because both goals are fully ready.

If Wave 1C copies that to check 1 → **money never exercised**.
If it uses check 2 and keeps “all non-LEGACY” → **fails** on scaffold `Income, gifts, wants, and needs`.

**Minimal plan change:** Specify check **≥2** (or 2/3), assert `scaffold_steps is None` globally, and assert non-`LEGACY` / depth archetypes **only for** `(money, Dollar-coin values)` samples (or seed until at least one money item appears). Do not require every cumulative item to be ready.

---

### 3. Registration surface is under-specified
**Severity: must-fix · Generator / scope risk**

Ready path is not just `pilot_money.py` + regenerate. Prior pilots require all of:

1. `PILOT_TARGETS` + `MISCONCEPTIONS` + `WORKED_EXAMPLES` in `pilot_specs.py` (`pilot_manifest_fields` sets `content_status: ready`)
2. `_BUILDERS[( "money", "Dollar-coin values" )]` in `pilot_generators.py`
3. `has_pilot_generator` / `PILOT_TARGETS` alignment (audit note: *“ready status has no authored generator”*)

Audit readiness also requires: conceptual + procedural + transfer + application archetypes; worked stages exactly `model` / `guided` / `transfer` with **3 distinct prompts** and answer keys; ≥2 misconceptions; enriched intuition; Khan mapping; authored semantic checks (transfer error language; application `model` + `;` in answer; MC distractors).

**Minimal plan change:** List those four registration touchpoints explicitly. Single target only: `("money", "Dollar-coin values")`.

---

### 4. G1 honesty vs shared subskill / legacy templates
**Severity: must-fix pedagogy constraint (plan partially states it) · Pedagogy risk**

Evidence:

- `g1_money` → only `Dollar-coin values` (`texas_grade_goals.py`).
- Same subskill is also under `g2_money` with **Making change**.
- Scaffold `data/content_depth/money.json` examples are multi-dollar (`$26.37`, `$32.08`) — **not** G1.
- Legacy templates go to multi-dollar / large multi-coin sets (`generate_early_math_manifests.py`).
- Intuition `try_this` is still *“Make $1.37 with bills and coins in two different ways”* (`early_math_intuition.py`) — composition-style, conflicts with “no making-change / budget arithmetic” even if audit only checks non-empty fields.

Plan correctly freezes Making change / Budget-style totals / Place-value in currency as scaffold. Gaps:

- Cap **generated** totals and formats for the ready pilot (e.g. single-coin identity; small sets with total ≤ 100¢; `$1 = 100¢`; no change-from-payment; no multi-item budgets).
- Worked examples in `WORKED_EXAMPLES` must be G1-honest (replace multi-dollar scaffold prose).
- Optional but recommended: tighten intuition `try_this` to name/value or count-vs-value — not required for audit green, required for pedagogical consistency.

**Minimal plan change:** Add hard generator bounds + G1-only worked-example content requirements; keep intuition refresh optional unless you want zero G2 bleed in skill UX.

---

### 5. Diagnostic / form semantics (plan OK if followed)
**Severity: suggestion · Diagnostic risk**

Audit `_check_authored_question` will fail ready status if:

- transfer prompts lack `learner` / `diagnose` / `correct`
- application lacks `model` in prompt and `;` in `correct_answer`
- two misconception answers not distinct from key / each other
- MC omits those distractors; application MC lacks ≥2 distinct model prefixes

Plan’s four reasoning forms match the framework. Implementers must map wrong answers **1:1** to the two registered misconception codes (pilot generator uses `wrong_answers[index]`).

**Coin-count-vs-value** and **dollars-vs-cents** are the right two diagnostic themes for TEKS 1.4; ensure each form can emit both as answer keys, not only feedback text.

---

### 6. Scope / TEKS alignment (mostly good)
**Severity: nit · Scope**

- Goal scope single-subskill: correct for “g1_money depth-ready.”
- Penny/nickel/dime/quarter + dollar=100¢: good for 1.4 relationships.
- “Compare coin count with coin value” is appropriate depth; keep multi-coin **totals** modest so G1 does not silently become TEKS 2.5 collection counting.
- Do not promote Making change under G2 pressure in this wave — plan already gates that with tests.

---

### 7. Process / constraints (compatible)
**Severity: note**

- Dirty worktree, no commit/push: fine.
- New `pilot_money.py` for one target should stay ≪300 LOC (`pilot_place_value.py` ≈128 for two targets).
- Curriculum Depth remains parent-only / off by default: plan does not need to change that flag.
- Verifications listed (focused tests, 100-seed audit, template dry-run, full unittest, smoke, HTML parse, `git diff --check`) match prior Wave receipts.

---

## What the plan gets right

- Bounded slice: one ready row; three money peers stay scaffold.
- Forms match audit contract (conceptual / procedural / transfer / application).
- Explicit non-goals (making change, budget arithmetic).
- Gate move 14→15 / 144→143 with sibling-scaffold proofs.
- Prior pilot pattern (`pilot_*` + tests + manifest regen + docs) is the right skeleton.

---

## Minimal plan deltas to flip BLOCK → GO

1. **Register** `("money", "Dollar-coin values")` in `PILOT_TARGETS`, `MISCONCEPTIONS`, `WORKED_EXAMPLES`, and `_BUILDERS`; then regenerate `data/content_depth/money.json`.
2. **Update all** hardcoded `14/144` audit pins (framework, place_value, add_subtract tests + docs).
3. **Cumulative:** check that includes money; assert depth only for money samples; never require full-window non-LEGACY while personal_finance/shapes remain thin.
4. **Generator bounds:** G1 denominations/values only; totals/worked examples within identify/compare/relationship scope; no change/budget stems.
5. **Keep** sibling-scaffold tests for Making change, Budget-style totals, Place-value in currency.

With (1)–(4) written into the plan, **GO**. As written today: **BLOCK**.
