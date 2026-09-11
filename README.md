# Skills

A skill is one narrow, testable capability — e.g. "create a legal entity in BOX", "map a chart of accounts", "validate static data completeness". An agent composes skills; a skill never calls another skill.

## Convention

```
skills/<skill-name>/
  SKILL.md       # what it does, inputs, outputs, preconditions, failure modes
```

Skills live at this repo's **top level**, as a sibling of `agents/` — never nested inside one agent's
folder (e.g. not `agents/branch-config-agent/skills/…`), even for a skill mostly associated with one
agent. This repo's agents can, and do, share skills — `sigom-box-fe-configs-agent` already calls
`branch-config-agent`'s `mine-fe-branch-config` and `propose-branch-config` (see its AGENT.md's "Skills
it may call") — and a skill nested under one agent's folder would misstate that from the start.

**Where scripts for a skill *built in this repo* go.** This repo has not built a real script yet — every
skill here is either external code (below) or "not yet implemented." When one of this repo's own agents
gets its first real skill (e.g. `sigom-box-fe-configs-agent`'s `generate-fe-config-sql`), its script goes
in a top-level **`scripts/`** folder, a sibling of `skills/` — `scripts/generate_fe_config_sql.py`, named
to match its skill. One script per skill, not nested inside the skill's own folder. The `SKILL.md` names
its script and the exact CLI invocation under a "How to run" section rather than owning a private copy.

**Where scripts for an *externally-built* agent's skills go.** They don't — `branch-config-agent` (see
`agents/branch-config-agent/AGENT.md`) is real, already-built code living entirely in its own repo,
`plugins/agent-plugins/branch-config-agent/{skills,scripts}/` (`scripts/` a sibling of `skills/` *there*,
at that repo's own root — the precedent the rule above generalizes from). Nothing from that repo is
copied here. This repo only references those skills by name — in an `AGENT.md`'s "Skills it may call"
table, or in a doc like `agent-architecture.md` — never duplicates their code or holds a second
`SKILL.md` for them. If one of them is ever brought into this repo instead (rather than called
externally), that's a deliberate migration to flag and document as such, not a quiet copy.

This only works cleanly because a skill here has exactly one script. If a skill is genuinely meant to be
reusable with a materially different implementation per caller, that's the case for nesting a `scripts/`
under the skill's own folder instead of the shared top-level one — flag it explicitly when that's true
rather than assuming the default.

## Rules

- Name skills as verbs: `create-legal-entity`, not `entity-creation-stuff`.
- `SKILL.md` must state what happens on failure — retry, abort, or escalate to a human. "Undefined" is not acceptable.
- No real entity/counterparty/portfolio names in examples — use `ENTITY_A`, `CPTY_X`.
- Every skill needs at least one case in `evals/cases/`.

See `example-create-legal-entity/` for the template.
