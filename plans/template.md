# {Plan title}

**Status:** active
**Owner:** {your name or handle}
**Created:** YYYY-MM-DD
**Last updated:** YYYY-MM-DD
**Related:** {issue/PR links, Slack threads if any}

---

## Context

What is true today. The problem this plan solves. What surfaced this need (bug report, performance issue, ACP adapter change, product requirement). Two or three short paragraphs maximum.

## Goal

The one-paragraph outcome. Concrete enough that you'll know when you're done. If you can't write this, the plan isn't ready.

## Non-goals

What this plan explicitly does NOT do. Pre-empts scope creep. Most under-used and most valuable section.

## Approach

The plan in 5–15 bullets. File paths and patterns where possible. Each bullet should be small enough to be a meaningful PR or PR-section.

- [ ] Step 1 — concrete action, with file paths
- [ ] Step 2
- [ ] Step 3

If the work is large, break it into phases:

### Phase 1 — {what}
- [ ] ...

### Phase 2 — {what}
- [ ] ...

## Open questions

Things to resolve before or during execution. If there are none, delete this section — don't manufacture uncertainty.

- ⏳ {question} — needs {person/team/decision}

## Decision log

Append-only. Each entry: date, decision, why, alternatives considered. This is the section that pays compounding dividends.

- **YYYY-MM-DD:** decided to do X over Y. X gives us {benefit}; Y was rejected because {reason}. Considered Z but it would have required {cost}.

## Verification

How we'll know this worked. Be specific.

- Tests: which tests cover the behavior; what new tests are needed.
- Manual checks: API call to make, page to load, scenario to reproduce.
- Metrics: latency targets, error rate budgets — whatever applies.

## Rollout

If this changes runtime behavior:

- Feature flag: name and default.
- Backfill / data migration: order, expected duration, rollback plan.
- Monitoring: dashboards / alerts to watch.
- Rollback: how to revert if something breaks.

If none of these apply, delete the section.

## Done when

Concrete checklist that maps to "Goal." When every box is checked, set status to `completed` and `git mv` to `plans/completed/`.

- [ ] {observable thing 1}
- [ ] {observable thing 2}
- [ ] {observable thing 3}
