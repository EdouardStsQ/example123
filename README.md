# Queries

Reusable, verified read-only queries against BOX/TPC/GBO, kept as runnable SQL plus a sample of what they return — so an agent (or a person) can see the shape of the output without running anything.

This got its own subfolder under `reference/` as soon as we had more than a couple of these — a query and a table write-up are both "reference" material but different enough in shape to file separately.

## Convention

Each query is a matched pair, same basename:

- `<query-name>.sql` — the query itself, with a header comment stating the schema/environment it targets and what question it answers
- `<query-name>.sample-results.csv` — a small illustrative result set, **not a live data dump**

Add a new pair rather than editing an existing query's meaning in place — if the query changes materially, bump it (`list-entity-static-data-v2.sql`) and mark the old one deprecated in its header comment, since agents/skills may already reference it by name.

## Rules

- Placeholder identifiers only, in both the SQL and the CSV — `ENTITY_A`, `CPTY_X`, never a real entity, counterparty, or portfolio name. This applies even when a query was drafted by running it against real data — scrub before committing.
- Read-only queries only. Anything that writes belongs in a skill (`skills/`), not here, so it goes through the same review/eval bar as other automation.
- State the schema/environment in the `.sql` header comment (`-- schema: BOX, env: UAT`) — the same query text can mean different things in different environments.
