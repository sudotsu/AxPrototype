Short, blunt take:
You’ve mostly built “five people rewriting the same blog post.” Linear order alone doesn’t create collaboration; structured hand‑offs do. Until each role passes typed artifacts (not prose) and is hard‑checked to produce only its unique slice, you’ll keep getting convergent essays.
Below is a practical, opinionated plan to make AxP behave like role‑specific specialists that actually collaborate.

Big picture: switch from prose chain → artifact pipeline
Principle: Each role transforms and links structured artifacts on a shared blackboard, then (optionally) adds a short human‑readable note. Downstream roles consume the registry JSON, not upstream prose. You already have ID discipline and a soft redundancy nudge—good start. Now force it.
What changes the game

Artifact Registry (the blackboard):
results['registry'] holds typed entries keyed by stable IDs with explicit cross‑refs:

S[]: strategy objects: {s_id, title, audience, hooks, 3_step_plan, acceptance_tests[]}

A[]: analysis objects: {a_id, s_refs[], kpi_table[], falsifications[], risks[]}

P[]: production assets/specs: {p_id, a_refs[], spec_type, body}
(spec_type ∈ {api, ddl, config, copy_block, wiring, prompt_pack})

C[]: courier schedule rows: {day, time, channel, p_id, kpi_target, owner_action}

X[] (critic issues): {x_id, refs:{s[],a[],p[],c[]}, issue, fix, severity, proof_scores}

Hard shape validators + strict re‑prompt:
After each role, run a schema check. On failure: STRICT MODE: “Return ONLY the required sections in exact order/JSON; no narrative.” Include a 2–3 line few‑shot per section to pin shape. No pass → no handoff.

Handoff policy = “JSON first, prose optional”:
Downstream roles receive:

The registry slice they need (not the whole essay).

A role‑specific note (1–3 lines max) if absolutely needed.
Remove the temptation to paraphrase.

Critic as a live gate, not just a finale:
Run a lightweight critic check after each role (schema + referential integrity + overlap score). If it fails, trigger one rewrite for that role, then continue. The heavy audit still happens at the end.

Hybrid linear + micro‑loops (two short Q&As):

After Analyst → give Producer one Q&A turn with Analyst (to pin specs vs KPIs).

After Producer → give Courier one Q&A turn with Producer (to pin P‑IDs → channels/timing).
That’s it—two extra exchanges, huge cohesion boost.

Objective isolation:
Stop shoving the same “deployment checklist + rationale” objective into every role prompt. Create a single ObjectiveSpec object and feed only the relevant fields to each role. Otherwise the global objective will keep overpowering role differences.

Exclusion lists (ban cross‑role shapes):
In config, forbid phrases/forms that belong to other roles (e.g., “deployment checklist” for Producer, “architecture rationale” for Courier). If detected, auto re‑prompt.

Final composer:
A stitcher consumes S/A/P/C/X and emits:

Executive summary

Linked artifact index (S/A/P/C)

Risk & readiness tag

Schedule highlights & KPI dashboard
That’s the polished “report.” None of the upstream agents should try to write it.

What “world‑class” looks like (per role)
Strategist (world‑class)

Output: 3–5 S‑objects + S‑Index + acceptance tests (Gherkin or bullet checks).

No how‑to guides. No schedules. No specs.

Example S object:
{
"s_id":"S-3",
"title":"Mid-market upsell wedge",
"audience":["Ops Managers (100–1000 FTE)"],
"hooks":["Cut handoffs by 40% in 30 days"],
"three_step_plan":["Foot-in-door audit","Pilot in 1 BU","Land & expand"],
"acceptance_tests":[
"Within 30 days, pilot reduces cycle time ≥25%",
"NPS delta in pilot BU ≥ +10"
]
}

Analyst (world‑class)

Output: A‑objects tied to S‑IDs, with falsifications and a numeric KPI table (targets + timeframes), plus a validation matrix. Zero “best‑practices prose.”

Example KPI row: {"metric":"Cycle time","target":-25,"unit":"%","by_day":30,"s_ref":"S-3"}

Producer (world‑class)

Output: P‑assets (APIs/contracts, DDL, config tables, copy blocks) each referencing A‑IDs. No schedules, no audits, no checklists.

Example P assets:

spec_type:"api" with endpoints, request/response, error codes

spec_type:"copy_block" with headline, subhead, CTA variants keyed to audiences in S

Courier (world‑class)

Output: tables only for schedule & DM scripts; KPI tracker rows; each line references a P‑ID.

Example row: {"day":"D3","time":"14:00","channel":"Email","p_id":"P-7","kpi_target":"CTR ≥ 4%","owner_action":"Send Variant B to Segment 2"}

Critic (world‑class)

Output: Compliance report, 5‑Proof audit table (Truthfulness, Specificity, Feasibility, Novelty, Compliance), Issue→Fix with S/A/P/C refs, Final score + diagnostics. No guides.

Minimal schemas (use JSON Schema or light regex)
Keep it simple and fast. Example (trim to your taste):
// strategist.schema.json
{
"type":"object",
"required":["S","s_index"],
"properties":{
"S":{"type":"array","minItems":3,
"items":{"type":"object","required":["s_id","title","audience","hooks","three_step_plan","acceptance_tests"],
"properties":{
"s_id":{"type":"string","pattern":"^S-\\d+$"},
          "title":{"type":"string"},
          "audience":{"type":"array","items":{"type":"string"}},
          "hooks":{"type":"array","items":{"type":"string"}},
          "three_step_plan":{"type":"array","minItems":3,"items":{"type":"string"}},
          "acceptance_tests":{"type":"array","minItems":2,"items":{"type":"string"}}
        }
      }},
    "s_index":{"type":"array","items":{"type":"string","pattern":"^S-\\d+$"}}
}
}

Mirror this for Analyst/Producer/Courier/Critic. Enforce ID patterns and cross‑ref integrity:

All A[].s_refs[] must exist in S.

All P[].a_refs[] must exist in A.

All C[].p_id must exist in P.

All X[].refs.\* must point to valid IDs.

If any check fails → STRICT MODE re‑prompt with the tiny few‑shot.

Few‑shot snippets (tiny, per section)
Keep them short so they shape output without inviting prose creep.
Strategist few‑shot
S-1: Hook = "Reduce cycle time 25% in 30 days"
S-1 Acceptance tests:

- Pilot cycle time ≤ 75% of baseline by Day 30
- Pilot NPS delta ≥ +10 vs control
  S-ID Index: S-1, S-2, S-3

Analyst few‑shot
A-2 (refs: S-1):
KPI Table:

- "Cycle time %Δ", target -25, by_day 30
  Falsifications:
- If baseline variance > 20%, target invalid
  Validation:
- t-test on cycle time vs control (p<0.05)
  A-ID Map: A-1→S-2, A-2→S-1

Producer few‑shot
P-4 (refs: A-2) spec_type=api
/metrics/pilot POST -> {team_id, window} => {cycle_time_delta, n}
Errors: 400 invalid_team, 403 window_too_short
P-ID Index: P-3, P-4, P-7

Courier few‑shot
D1–D7 Schedule (rows):
D3, 14:00, Email, P-4, KPI CTR ≥4%, Owner: GrowthOps
DM Script (P-7): 3 openers, 1 CTA
KPI Tracker Rows: day, metric, target, observed, delta

Critic few‑shot
5-Proof Audit:
P-4 Feasibility=4/5 (spec complete), Specificity=5/5
Issue→Fix:
X-3: Missing A-ref on P-7 → Add a_refs:[A-2]
Final Score: 84/100

Flow (concrete and minimal)
ObjectiveSpec
│
▼
Strategist ──(schema gate)──▶ registry.S
│
▼
Analyst ──(schema+refs gate)──▶ registry.A
│ Q&A (1 turn)
▼
Producer ──(schema+refs gate)──▶ registry.P
│ Q&A (1 turn)
▼
Courier ──(schema+refs gate)──▶ registry.C
│
▼
Critic (heavy) ──▶ registry.X + audit
│
▼
Composer ──▶ Executive report + Linked Index + KPI dash

Governance signals (log them every step):

REDUNDANCY: trigram Jaccard (you have it) + optional embedding cosine.

SPECIFICITY_RATIO: numbers/tables/tokens ÷ total tokens.

REF_INTEGRITY: % of cross‑refs resolved.

NOVELTY: % of tokens not present in upstream slice.

SHAPE_COMPLIANCE: pass/fail + missing fields.

Switch any soft signal to hard per role via config when you’re ready.

Concrete changes to implement now (low‑friction)

Registry + slices:

Add results['registry'] = {"S":[],"A":[],"P":[],"C":[],"X":[]}

Pass only the needed slice + ObjectiveSpec into each role prompt.

Schema gates:

5 JSON schemas (tiny).

Validate + STRICT MODE loop with your tiny few‑shots from config/role_examples/\*.md.

Exclusion lists:

config/role_shapes.json per role: banned phrases + banned sections.

Light Critic gate after each role:

Don’t write essays; just enforce shape + referential integrity + overlap.

Composer:

Deterministic function that reads S/A/P/C/X and emits the final executive report.

Nobody else writes the “report.”

Temperature shaping:

Strategist/Analyst/Critic: low temp (structure).

Producer/Courier: medium temp (asset breadth) but schema‑locked.

Objective isolation:

Create ObjectiveSpec and give each role only the fields it needs (e.g., Analyst gets targets/time horizons; Producer gets audiences + approved hooks; Courier gets channels & P‑IDs).

Why this will stop the convergence

Roles can’t restate what they don’t see. Handoffs are JSON slices, not essays.

Validators make “wrong shape” impossible. The only way to pass is to produce the role’s artifact.

Cross‑refs force collaboration. You literally can’t produce a P without an A; can’t schedule without a P; critic can’t score without S/A/P/C.

Two tiny Q&As inject co‑creation where ambiguity lives (KPIs→specs, specs→schedule) without exploding turns.

Pitfalls to avoid

Over‑templating: If your few‑shots are verbose, models will copy style. Keep them microscopic.

Global “objective” leaking: If every prompt includes the same instruction block, convergence returns. Isolate it.

Letting the critic drift into essay mode: Keep interim critic purely mechanical; reserve the long audit for the end.

A simple “done vs world‑class” acceptance bar

Done: All schemas pass; 100% ref integrity; redundancy < 0.55 per step.

World‑class: Above + Producer ships at least 3 distinct spec types tied to different A‑IDs; Courier produces a D1–D7 schedule with KPI targets per row; Critic delivers Issue→Fix with references across ≥3 ID types and a 5‑Proof table.

You’re close. The IDs, redundancy checks, and contracts are the right instincts. The real unlock is shape‑first + JSON‑only handoffs, with a tiny bit of Q&A and a strict critic gate at every step. Do that, and AxP stops sounding like one author with five hats—and starts behaving like a team.
