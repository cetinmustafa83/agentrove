# Plans

Plans are first-class artifacts in this repo. They capture *why* and *how* before the code is written, and they survive context compaction so the next person — or agent — can pick up where the last one left off.

---

## When to write a plan

| Size | Where the plan lives |
|---|---|
| **Small / medium** (single domain, < 1 day of work) | Stated up front — in the issue, conversation, or PR description. 3–10 bullets. No checked-in file. |
| **Non-trivial** (multi-domain, schema/migration changes, ACP/streaming/sandbox surgery, materially uncertain approach) | Checked-in plan in `plans/active/{topic}.md` using `template.md`. The PR links it. |

When in doubt, write the file. The cost of a 50-line markdown is far less than the cost of three engineers (or agents) discovering the design halfway through.

---

## Folder layout

```
plans/
├── README.md          ← this file
├── template.md        ← copy this when starting a new plan
├── active/            ← in-flight plans
└── completed/         ← landed plans, kept as design history
```

**Don't delete completed plans.** They are the design history — they explain why the code looks the way it does, what alternatives were considered, what was rejected.

---

## Lifecycle

1. **Start:** copy `plans/template.md` to `plans/active/{topic}.md`. Fill in context, goal, non-goals, approach.
2. **Work:** as decisions get made, append to the **Decision log** with date, choice, reason, alternatives considered. Update **Status** when state changes (active → paused → completed).
3. **Land:** when the work ships, set status to `completed` and `git mv` the plan to `plans/completed/`.
4. **Reverse / supersede:** if a plan is overtaken by a different approach, link the new plan from the old one and mark the old one `superseded`.

---

## Naming

- Lowercase, underscores, descriptive: `per_message_checkpoints.md`, `acp_session_modes.md`.
- No dates in filenames — `Created` and `Last updated` go inside the file.
- No sequence numbers — these aren't ADRs.
- For technical-debt plans, prefix with `debt_`: `debt_legacy_streaming_envelope.md`.

---

## What a plan is *not*

- Not a PR description — PR descriptions are about a single change; a plan can span many.
- Not an ADR — ADRs record a decision after the fact. Plans steer work before it happens.
- Not a wishlist — every plan should have an owner and a status.
- Not a TODO file — concrete next steps belong in the **Approach** section.

---

## Discipline

- **One plan per checked-in file.** Don't bundle.
- **Update the decision log as you go**, not at the end.
- **Keep approach concrete.** File paths and patterns where possible.
- **Flag open questions when they exist.** Don't manufacture them; if the approach is settled, say so.
- **Reference the plan from the PR.** Reviewers should see context without leaving the PR page.
