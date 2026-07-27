# Curriculum-depth plan review — `g1_personal_finance` / Income, gifts, wants, and needs

**Verdict: BLOCK** (right next slice and right audit delta; three plan traps must be written into the goal before implement).

Direction matches the standards spine after money. As written, the candidate still under-specifies cumulative windows, job-skill inventory, and frozen-counter surfaces in ways that will fail tests or skip TEKS 1.9 content.

---

## Findings (must-fix first)

### 1. Cumulative checks: money’s check-2 “legacy neighbor” pattern will invert after this slice
**Severity: must-fix · Test / cumulative risk**

G1 goal order (`app/texas_grade_goals.py`):

| Check | Window | After this promotion |
|-------|--------|----------------------|
| **1** | place_value + add_subtract | already all ready |
| **2** | earlier: place_value, add_subtract, money; **current: personal_finance** | **all four ready** |
| **3** | earlier includes personal_finance + **shapes**; current data | **shapes/data still scaffold** |

Evidence: `build_texas_cumulative_quiz` uses `end = min(len(goals), max(2, check_number * 2))` (`app/content_depth/cumulative.py`).

`tests/test_content_depth_money.py` seeds check **2** and asserts both money reachability and `saw_legacy_neighbor`. That works only while personal_finance is thin. After promoting Income/gifts/wants/needs:

- check **2** becomes a fully ready window → `saw_legacy_neighbor` stays false → honesty assertion dies
- check **1** never samples personal finance

**Plan must split:**

1. **Check 2:** personal-finance items appear; every question non-`LEGACY`; all `scaffold_steps is None`
2. **Check 3:** still scaffold-free labels, but at least one `LEGACY` neighbor from thin shapes/data

Do not copy money’s single-check dual assertion.

---

### 2. Job skills are named by TEKS / the goal, but zero authored content exists
**Severity: must-fix · Pedagogy / TEKS completeness**

Evidence:

- Goal: *“Identify income, gifts, job skills, wants, and needs”* (`1.9`) — `texas_grade_goals.py` `g1_personal_finance`
- Coverage matrix: *“Identify income, gifts, job skills, wants, and needs”*
- Legacy generator only has four classify stems: rake leaves → income, birthday card → gift, headphones → want, school lunch → need (`app/financial_literacy.py` ~108–123)
- **No job-skill item family at all**

Candidate says “cover … job skills” without:

- a bounded skill inventory (child-accessible, non-stereotyped, no pay/salary)
- which reasoning form owns them (at least conceptual + one of procedural/transfer)
- what a correct answer looks like (named skill vs vague “work hard”)
- what is out of bounds (wages, “best job,” family career pressure)

Without that inventory, implementers will either skip 1.9’s job-skill strand or invent moralizing/adult labor content.

---

### 3. Frozen audit counters are implied, not enumerated
**Severity: must-fix · Test / docs risk**

Target `16 ready / 142 thin / 0 missing` is correct. Pins still at **15 / 143**:

| Surface | Current pin |
|---------|-------------|
| `tests/test_content_depth_framework.py` | `ready_count == 15`, `thin_count == 143` |
| `tests/test_content_depth_place_value.py` | `(15, 143, 0)` |
| `tests/test_content_depth_add_subtract.py` | `(15, 143, 0)` |
| `tests/test_content_depth_money.py` | `(15, 143, 0)` |
| `README.md` (multiple prose lines) | fifteen / 143 |
| `TODO.md` | remaining 143; money row 15/143 |
| `CONTINUITY.md` | latest receipt 15/143 |

Same class of failure that blocked the money plan. Candidate’s vague “frozen counter updates” is not enough.

---

### 4. Scaffold content is not G1-honest and fails distinct-stage readiness today
**Severity: must-fix pedagogy for worked examples · Evidence for why promotion is real work**

`data/content_depth/financial_literacy.json` for this subskill:

- `content_status: "scaffold"`
- guided and transfer prompts are **identical** (“earning 6 dollars for raking leaves”) → audit would fail “three distinct tasks” if marked ready
- guided explanation is try-this copy (“List three things you need…”) not a stage explanation
- application prefix is adult household budgeting (`generate_content_depth_manifests.py` skill default)
- procedure misconception is generic template prose

Ready promotion must replace this with three distinct G1 stages, not regenerate the scaffold as-is.

---

### 5. Diagnostic pair + context-sensitive need/want must be locked to answer keys
**Severity: must-fix if left soft · Diagnostic / audit risk**

Audit (`app/content_depth/audit.py`):

- transfer needs `learner` / `diagnose` / `correct`
- application needs `model` in prompt and `;` in answer; MC needs ≥2 model prefixes
- two misconception wrong answers, distinct from key, 1:1 with `spec.misconceptions` via `wrong_answers[index]` (`pilot_generators.py`)

Recommended diagnostic pair (fits TEKS and current thin content):

1. **gift_as_income** — birthday/card money labeled “income”
2. **context_need_want** — same or similar item treated as need without the stem’s context (or need labeled want)

Candidate correctly bans “universal need.” Plan must require **context phrases in need/want stems** (weather, school day, broken vs working item) and seed tests that the same object can flip class with context.

Do **not** moralize wants (“wants are bad”).

---

### 6. Registration surfaces are listed correctly — add two hard constraints
**Severity: mostly OK · Scope risk if missed**

Candidate lists `PILOT_TARGETS`, `MISCONCEPTIONS`, `WORKED_EXAMPLES`, generator import, `_BUILDERS`, manifest regen. Confirm also:

- **New dedicated module** (e.g. `app/content_depth/pilot_income_gifts.py`) — do **not** overload `pilot_applied.finance` (that is G7 budget/net-worth/interest for the already-ready row)
- **Do not remove or rewrite**
  `("financial_literacy", "Budget percentages, net worth, interest, and incentives")`
- After regen, only
  `("financial_literacy", "Income, gifts, wants, and needs")`
  gains `content_status: "ready"` among the remaining FL scaffolds
- Optional: `VERTICAL_CONTEXT` entry in `scripts/generate_content_depth_manifests.py` for child-scale application stems (recommended, not required if worked examples + generator own the prompts)

---

### 7. Shared subskill with Grade 3
**Severity: note · Scope honesty**

`g3_personal_finance` reuses the same subskill string. Promoting it ready means G3 cumulative can pull depth archetypes for this row. Keep scenarios **grade-neutral and child-accessible** (chores, gifts, school lunch, umbrella in rain) — no “Grade 1 only” framing, no G3 scarcity/credit bleed (those are other subskills).

---

## What the candidate gets right

- Audit delta **15→16 / 143→142** matches one new ready target.
- Next Texas goal after `g1_money` is exactly `g1_personal_finance` with sole subskill Income/gifts/wants/needs.
- Four reasoning forms match the audit contract.
- Pedagogy guards (no beyond-G1 arithmetic, no family-income assumptions, no moralizing wants, no universal needs) are the right constraints.
- Sibling freeze of other financial_literacy subskills is correct.
- Registration list and release-gate shape match money’s successful receipt pattern.

---

## (1) Verdict

**BLOCK** on the candidate text as written.

**GO** only on the rewritten goal below (incorporates the three must-fixes and locks TEKS 1.9 job skills + cumulative split).

---

## (2) Must-fix issues (summary)

| # | Issue | Evidence |
|---|--------|----------|
| 1 | Cumulative neighbor honesty cannot stay on check 2 after promotion | `cumulative.py` end formula; G1 goals order; money test pattern |
| 2 | Job skills named by 1.9 / goal with no item family or inventory | `texas_grade_goals.py`; `financial_literacy.py` classify-only pool |
| 3 | Frozen 15/143 pins in four tests + README/TODO/CONTINUITY not listed | framework, place_value, add_subtract, money tests; README; TODO; CONTINUITY |
| 4 | Worked examples must be three distinct G1 tasks (scaffold duplicates) | `data/content_depth/financial_literacy.json` |
| 5 | Diagnostics must map gift≠income and context-sensitive need/want into answer keys | `audit.py` `_check_authored_question`; `pilot_generators` wrong_answers index |

---

## (3) Rewritten implementation goal

### Goal title
**Wave 1D — Promote Grade 1 personal finance depth for TEKS 1.9**

### In scope
Promote **only**:

```text
("financial_literacy", "Income, gifts, wants, and needs")
```

from scaffold → ready so the substantive audit moves:

```text
15 ready / 143 thin / 0 missing  →  16 ready / 142 thin / 0 missing
```

Texas mapping: **`g1_personal_finance`** only (TEKS **1.9**).

### Out of scope
- All other `financial_literacy` subskills (Saving/spending…, Scarcity…, Expenses…, Taxes…, Accounts…, Budget percentages…) stay **scaffold** and keep current generators/specs
- Do not rewrite the ready pilot
  `("financial_literacy", "Budget percentages, net worth, interest, and incentives")`
  or `pilot_applied.finance`
- **Making change** and other `money` scaffolds (G2 TEKS 2.5+)
- `g1_shapes` / `g1_data` depth authoring
- Broader “financial literacy wave” across grades 2–7
- Enabling Curriculum Depth by default
- Commits/pushes unless separately requested

### Pedagogy bounds (hard)
| Bound | Requirement |
|-------|-------------|
| Earned income vs gifts | Income = money/goods received for work or a job-like task; gift = received without earning |
| Needs vs wants | Classification depends on **stated context**; never teach “X is always a need/want” |
| Job skills (1.9) | Child names a useful skill for a simple, named role (e.g. listening carefully, counting, reading labels, organizing, being on time) — **not** wages, prestige, or “best job” |
| Arithmetic | No multi-step money arithmetic, weekly totals, tax, interest, profit |
| Family income | No household salary/parent income assumptions as the model of income |
| Moralizing | Wants are optional, not “bad”; needs are necessary **in the scenario**, not virtues |
| Language | Child-scale scenarios (school, chores, gifts, weather, simple community roles) |

### Required reasoning forms
Dedicated typed generator module, e.g. `app/content_depth/pilot_income_gifts.py` (or `pilot_personal_finance.py`), exporting one builder:

```text
builder(ReasoningKind) -> PilotProblem
```

| Form | Behavior |
|------|----------|
| **Conceptual** | Mental model: source of money (earned vs gift) **or** need vs want **or** “skills help people do jobs” — multiple-choice labels stay in G1 vocabulary |
| **Procedural** | Classify a single scenario as income / gift / need / want **or** select the skill that matches a named simple job |
| **Transfer / error-analysis** | Prompt contains `learner` (or diagnose/correct): e.g. learner calls birthday money “income,” or calls a context-optional item a “need” |
| **Application** | Prompt requires selecting a model; answer is `model; result` with `;` (e.g. `income-or-gift model; gift` or `need-want model; want` or `job-skill model; careful listening`) |

Seed pool must, across 100 seeds, exercise **all three TEKS strands**: income↔gift, context need↔want, job skills.

**Bounded job-skill inventory (minimum 6 roles × ≥1 skill each), examples of allowed roles:** librarian, nurse’s helper, baker, bus driver, classroom helper, veterinarian helper — skills like reading, careful counting, following steps, gentle handling, organizing, listening. Ban salary, hiring, “dream job,” and gender/race stereotypes.

**Context-sensitive need/want:** at least some item pairs where context flips class (e.g. umbrella in heavy rain walk vs sunny indoor day; water after recess vs extra soda when not thirsty). Prompts must carry the context clause.

### Misconceptions (exactly two, answer-keyed)
Register in `MISCONCEPTIONS` with recovery → concept then procedure:

1. `gift_as_income` — feedback: money from a gift is not earned income
2. `context_need_want` — feedback: need vs want depends on the situation, not the object name alone

Generator `wrong_answers` order must match these two codes. Wrong answers appear in MC choices.

### Worked examples (exactly three distinct stages)
In `WORKED_EXAMPLES` for the target only:

| Stage | Distinct task theme |
|-------|---------------------|
| model | Income vs gift (chore/earned vs birthday/card) |
| guided | Context-sensitive need vs want |
| transfer | Job skill for a simple named role **or** correcting a gift-as-income error |

Stages must be `model` / `guided` / `transfer`, three **different** prompts, non-empty expected answers. Do not ship the current scaffold’s duplicated rake-leaves prompts.

### Intuition + Khan
Enrich in `app/financial_literacy.py` `_INTUITION_BY_SUBSKILL["Income, gifts, wants, and needs"]`:

- **Mental model:** name source (earned vs gift), then decide need vs want from the situation; jobs use skills
- **Common mistake:** gift-as-income and/or treating wants as universal needs
- **Try this:** child-scale classify list **or** name one skill for one simple job — no spending plan that sneaks G2 saving arithmetic

Keep existing parent-controlled Khan mapping (`khan_url_for` / registry). Do not hard-enable external links.

### Exact registration surfaces
1. `app/content_depth/pilot_specs.py`
   - add target to `PILOT_TARGETS`
   - `MISCONCEPTIONS[target]` (two rows above)
   - `WORKED_EXAMPLES[target]` (three stages above)
2. New `app/content_depth/pilot_income_gifts.py` (typed, `implicit` N/A; full type hints; ≤300 LOC)
3. `app/content_depth/pilot_generators.py`
   - import builder
   - `_BUILDERS[("financial_literacy", "Income, gifts, wants, and needs")] = ...`
4. Regenerate:
   `python scripts/generate_content_depth_manifests.py`
   → `data/content_depth/financial_literacy.json` shows this subskill `content_status: "ready"`; **other FL subskills remain scaffold**
5. Intuition copy update in `app/financial_literacy.py`
6. Optional: `VERTICAL_CONTEXT` child-scale application string for this pair in `generate_content_depth_manifests.py`

### Tests (new focused module)
`tests/test_content_depth_income_gifts.py` (or `..._personal_finance.py`), modeled on money:

1. **Goal readiness:** `g1_personal_finance` maps to the target; depth spec READY; worked stages model/guided/transfer with 3 distinct prompts + keys
2. **Archetype forms:** for each archetype, many seeds, `typed` and `mc`; 2 misconceptions; wrong ≠ correct; MC contains key + diagnostic wrongs; transfer error language; application has `model` + `;`
3. **Pedagogy bounds over ≥100 seeds:**
   - sees income, gift, need, want **and** job-skill prompts
   - no interest/tax/profit/budget-percent language
   - no “always a need/want” universal wording
   - need/want stems include context tokens
   - no moralizing want language (e.g. “selfish,” “bad”)
4. **Cumulative:**
   - check **2:** at least one `financial_literacy` question; all questions non-`LEGACY`; all `scaffold_steps is None`
   - check **3:** all `scaffold_steps is None`; at least one `LEGACY` from thin neighbors (shapes/data)
5. **Audit honesty:** report `(16, 142, 0)`; target row `ready`; **every other** financial_literacy subskill still `scaffold`/`thin`

### Frozen counter + truth updates
Bump **15/143 → 16/142** in:

- `tests/test_content_depth_framework.py`
- `tests/test_content_depth_place_value.py`
- `tests/test_content_depth_add_subtract.py`
- `tests/test_content_depth_money.py`
- `README.md` (all “fifteen / 143” prose)
- `TODO.md` (check off this slice; remaining thin = 142)
- `CONTINUITY.md` (receipt + gates)

### Release gates (must all pass)
```bash
python -m py_compile app/content_depth/*.py tests/test_content_depth*.py \
  scripts/audit_content_depth.py scripts/generate_content_depth_manifests.py
python -W default::ResourceWarning -m unittest -v \
  tests.test_content_depth_income_gifts \
  tests.test_content_depth_money \
  tests.test_content_depth_add_subtract \
  tests.test_content_depth_place_value \
  tests.test_content_depth_framework \
  tests.test_content_depth_proof \
  tests.test_content_depth_serialization \
  tests.test_content_depth_templates \
  tests.test_content_depth_units \
  tests.test_texas_grade_goals \
  tests.test_texas_financial_literacy \
  tests.test_fall_readiness_audit \
  tests.test_public_docs
python scripts/audit_content_depth.py --seeds 100 --summary-only
# expect: ready=16 thin=142 missing=0 ; nonzero exit until full rollout
python scripts/template_dry_run.py --samples 3 --mc --require-external-id
python -W default::ResourceWarning -m unittest discover -s tests -q
python -m app.main --smoke-test
git diff --check
```

File-size gate: new pilot + new test modules each ≤300 LOC (money precedent: ~73 / ~109).

---

## (4) Why this slice next — not Making change, not a FL wave

**Standards order (Texas Grade 1 catalog):**

1. `g1_place_value` — **ready**
2. `g1_add_subtract` — **ready**
3. `g1_money` (Dollar-coin values only) — **ready**
4. **`g1_personal_finance` (this subskill) — next thin quiz-ready goal**
5. `g1_shapes` / `g1_data` — later G1 depth

**Not Making change:**
`Making change` is under **`g2_money`** (TEKS **2.5** collection/change), explicitly left scaffold when G1 money shipped (`CONTINUITY.md` money receipt; money sibling tests). Jumping to it skips TEKS **1.9** and breaks the Grade 1 fall-alignment spine.

**Not a broader financial-literacy wave:**
Six other FL subskills encode G2–G7 ideas (saving multi-week totals, scarcity/credit, profit, tax, registers, interest). Promoting them as a batch would (a) pull beyond Grade 1 arithmetic/decision models, (b) explode scope past the single-goal authoring pattern that got place-value → add/subtract → money through the 100-seed gate, and (c) contradict TODO’s “remaining thin rows in planned waves” discipline. One standards-ordered ready row keeps audit honesty and cumulative windows interpretable.

**Why this row is substantive, not a rename:**
Legacy content is a 4-item classify list with no job skills; depth scaffold has duplicate worked stages and generic misconceptions. Ready status requires a real generator, three distinct stages, two keyed recoveries, job-skill coverage, and context-safe need/want pedagogy — then 16/142 with neighbors still thin.

---

**Bottom line:** Candidate targets the correct next standards-ordered cell. **BLOCK** until the plan hard-codes (1) check-2 full-ready vs check-3 neighbor-legacy split, (2) a bounded job-skill inventory and form coverage, and (3) explicit frozen-counter file list. The rewritten goal above is the GO-ready implementation brief; no files were edited in this review.
