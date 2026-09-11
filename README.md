# Evals

Test cases that prove a skill or agent does the right thing, independent of whoever runs it (Devin today, maybe something else later).

## Convention

One file per case in `cases/`: input state in, expected BOX state (or expected refusal/escalation) out. Cover at least one happy path and one failure path per skill/agent.

Use placeholder identifiers only (`ENTITY_A`, `CPTY_X`) — never real entity, counterparty, or portfolio names, even in eval fixtures pulled from real screenshots.
