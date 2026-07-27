# Wave 1D Goal: Grade 1 Personal Finance Depth

Status: ready for implementation after Codex and Grok 4.5 review on 2026-07-15.

Grok review: `reviews/grok/curriculum-depth-g1-personal-finance-goal-review-20260715.md`

## Objective

Promote only:

```text
("financial_literacy", "Income, gifts, wants, and needs")
```

from `scaffold` to `ready`. This completes the next standards-ordered Texas Grade 1 goal,
`g1_personal_finance` (TEKS 1.9), and moves the substantive depth audit from:

```text
15 ready / 143 thin / 0 missing
```

to:

```text
16 ready / 142 thin / 0 missing
```

## Why This Is Next

The completed Grade 1 sequence is place value, addition/subtraction, then coin values. The next thin,
quiz-ready goal in `app/texas_grade_goals.py` is personal finance. `Making change` belongs to Grade 2,
and promoting the remaining financial-literacy rows together would mix later-grade saving, credit,
profit, tax, account, and interest concepts into this bounded Grade 1 slice.

## Learning Contract

Author three related but distinct reasoning axes. Prompts must identify which axis is being used instead
of presenting all labels as though they describe the same property.

1. **Source:** earned income versus a gift.
2. **Purpose in context:** a need versus a want in the stated situation.
3. **Capability:** a useful skill matched to a simple, named job or community task.

Use the child-facing routine:

1. Ask what is being classified: source, purpose, or skill.
2. Point to the evidence in the scenario.
3. Name the category or skill and explain it in one short reason.

### Hard pedagogy bounds

- Income is received for work or a job-like task; a gift is received without being earned.
- Need/want classifications depend on explicit context. No object is taught as universally a need or want.
- Wants are optional in the scenario, not bad, selfish, or irresponsible.
- Job-skill prompts use child-accessible roles and concrete skills, without wages, prestige, hiring,
  career pressure, or demographic stereotypes.
- Use at least six role/skill pairings across the seed pool. Suitable examples include classroom helper
  and organizing, baker and following steps, librarian and sorting, bus driver and careful attention,
  animal-care helper and gentle handling, and shop helper and counting.
- Use child-scale scenarios involving school, chores, gifts, weather, food, and community roles.
- Do not introduce multi-step money arithmetic, weekly savings totals, budgets, tax, interest, profit,
  credit, salaries, or assumptions about a family's income.
- Keep scenarios grade-neutral enough for the shared Grade 3 mapping without importing Grade 3 scarcity
  or credit content.

## Authored Question Forms

Create a dedicated, fully typed module such as `app/content_depth/pilot_income_gifts.py`, with one builder:

```text
builder(ReasoningKind) -> PilotProblem
```

- **Conceptual:** choose the correct reasoning axis or explain earned versus received, contextual
  necessity, or why a named skill helps with a task.
- **Procedural:** apply the three-step routine to one source, purpose, or job-skill scenario.
- **Transfer/error analysis:** explicitly ask the learner to diagnose or correct either gift-as-income
  reasoning or a need/want judgment that ignores context.
- **Application:** require model selection and return `model; result`, such as
  `income-or-gift model; gift`, `need-want model; want`, or
  `job-skill model; careful counting`.

Across at least 100 deterministic seeds, authored output must exercise income, gift, need, want, all three
axes, and the bounded job-skill inventory. Both typed and multiple-choice requests must work. Multiple-choice
questions must include the correct answer and two distinct diagnostic answers.

## Misconception Contract

Register exactly two answer-keyed misconception recoveries, in this order so they match
`PilotProblem.wrong_answers`:

1. `gift_as_income`: receiving money does not make it earned income.
2. `context_need_want`: need versus want follows the stated situation, not the object name alone.

The first recovery routes to the conceptual archetype and the second to the procedural archetype.
Wrong answers must differ from the key and appear in multiple-choice options.

## Worked Example and Help Contract

Replace the current duplicated scaffold stages with three distinct tasks:

1. `model`: distinguish earned income from a gift.
2. `guided`: classify a need or want using an explicit context clue.
3. `transfer`: match a concrete skill to a simple role, or correct a gift-as-income error.

Each stage needs a distinct prompt, a useful explanation, and a non-empty expected answer.

Update the existing `FinancialIntuition` entry with:

- **Mental model:** first name the axis, then use scenario evidence.
- **Common mistake:** treating every received dollar as income or ignoring context for needs and wants.
- **Try this:** classify one source and one contextual choice, then name a useful skill for a simple job.

Keep the existing Khan mapping optional and controlled by the parent external-links setting.

## Exact Implementation Surfaces

1. Add the dedicated typed builder module, kept at or below 300 LOC.
2. Update `app/content_depth/pilot_specs.py`:
   - add the target to `PILOT_TARGETS`;
   - add its two `MISCONCEPTIONS` rows;
   - add its three `WORKED_EXAMPLES` stages.
3. Update `app/content_depth/pilot_generators.py`:
   - import the builder;
   - register the target in `_BUILDERS`.
4. Update `app/financial_literacy.py` intuition content while preserving the existing parent-controlled
   Khan URL mapping.
5. Regenerate `data/content_depth/financial_literacy.json` with
   `scripts/generate_content_depth_manifests.py`.
6. Preserve the existing ready target
   `Budget percentages, net worth, interest, and incentives` and its `pilot_applied.finance` builder.
7. Keep every financial-literacy row that is currently scaffolded as scaffolded except the target.

## Test Contract

Add a focused module such as `tests/test_content_depth_income_gifts.py`, kept at or below 300 LOC.

It must prove:

- `g1_personal_finance` maps to the promoted target and its spec is ready;
- worked stages are exactly `model`, `guided`, and `transfer`, with three distinct tasks;
- each archetype works for typed and multiple-choice requests across many seeds;
- transfer prompts meet the diagnostic-language contract;
- application prompts contain `model` and answers contain `;`;
- the two diagnostic wrong answers are distinct, keyed, and present in MC choices;
- 100-seed output reaches all three learning axes, all four core labels, and job-skill prompts;
- contextual need/want stems include context and avoid universal or moralizing language;
- later-grade terms such as interest, tax, profit, credit, and budget percentages do not appear;
- the target becomes ready, previously scaffolded finance siblings remain thin, and the existing advanced
  finance pilot remains ready;
- the audit reports exactly `16 ready / 142 thin / 0 missing`.

### Cumulative regression split

Promotion changes the Grade 1 cumulative windows and must update the existing money test:

- **Check 2:** across a bounded seed sweep, personal-finance questions are reachable; every question is
  authored (`ReasoningKind` is not `LEGACY`) and every `scaffold_steps` value is `None`.
- **Check 3:** every `scaffold_steps` value remains `None`, while at least one `LEGACY` neighbor remains
  reachable from the still-thin shapes/data goals.

Do not retain the money test's old assertion that check 2 must contain a legacy neighbor.

## Frozen Counters and Truth Surfaces

Update `15/143` to `16/142` in:

- `tests/test_content_depth_framework.py`
- `tests/test_content_depth_place_value.py`
- `tests/test_content_depth_add_subtract.py`
- `tests/test_content_depth_money.py`
- all matching `README.md` statements
- `TODO.md`, including a checked Wave 1D row and 142 remaining thin subskills
- `CONTINUITY.md`, with the implementation and verification receipt

## Release Gates

All of the following must pass:

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
python scripts/template_dry_run.py --samples 3 --mc --require-external-id
python -W default::ResourceWarning -m unittest discover -s tests -q
python -m app.main --smoke-test
git diff --check
```

The audit command is expected to exit nonzero until every one of the 158 subskills is ready, but its summary
must be exactly `ready=16 thin=142 missing=0`. Template dry-run must report zero failures and zero missing
external IDs. No commit or push is part of this goal unless separately requested.

## Definition of Done

Wave 1D is complete only when the target is substantively authored across all four reasoning forms, the Grade 1
personal-finance cumulative window is fully depth-authored, thin-neighbor honesty is preserved in check 3, all
truth surfaces report 16/142/0, every release gate passes, and the implementation receipt records the final test
and file-size evidence.
