# Golden Principles

Opinionated invariants that keep this codebase legible and consistent for humans and coding agents. Each rule is tagged with what enforces it:

- ✅ **Mechanized** — pre-commit, CI, framework, or type system will catch it.
- ⚠️ **Advisory** — reviewer-enforced; the agent must remember.
- 💭 **Aspirational** — target shape, not currently true everywhere.

Per-artifact specifics (SQLAlchemy field rules, FastAPI dependency wiring, React component patterns, Tailwind tokens) live in `docs/artifacts/`. Per-domain shape (chat, sandbox, ACP, etc.) lives in `docs/domains/`. This file is what's true *across* the codebase.

When a principle and a local pattern conflict: prefer the principle for new code; legacy violations are migrated opportunistically, not silently emulated.

---

## 1. Architectural posture

- ⚠️ **Single-process app.** No distributed-system patterns — no cross-instance locks, no cross-process heartbeats, no consensus. Background work runs as `asyncio` tasks in the API process.
- ⚠️ **Redis is pub/sub + cache only.** Not a task broker, not a coordination layer.
- ⚠️ **Treat per-user request handling as effectively sequential.** Don't flag bugs that only appear under overlapping concurrent requests (retries, double-submit, multi-tab) unless the task explicitly asks for concurrency hardening.
- ⚠️ **`frontend/backend-sidecar/` is a build artifact.** Never edit. All backend source lives in `backend/`.
- ⚠️ **ACP `field_meta` (`_meta`) is optional extensibility metadata.** Agents aren't required to read it. Don't use it for user-facing data; if ACP has no first-class field for a concept, it can't be reliably done through metadata.

## 2. Minimalism

- ⚠️ **Smallest fix wins.** Don't refactor or add abstractions as part of a bug fix. A one-line guard beats reworked control flow.
- ⚠️ **Don't optimize for "no regressions" or long-term resilience unless asked.** Favor simple direct changes over defensive scaffolding.
- ⚠️ **Don't build elaborate rollback/state-restoration for failure paths.** Log + best-effort recovery (e.g., re-queue) is sufficient.
- ⚠️ **Don't add resource cleanup (`try/finally` with `.cleanup()` / `.close()`) for short-lived provider/client objects.** GC handles lazy clients (e.g., `aiodocker.Docker`); only add cleanup for long-lived or pooled objects.
- ⚠️ **Don't add pre-flight compatibility checks when a natural fallback exists.** Let it fall through.
- ⚠️ **Validate at the boundary only.** If an API endpoint checks a value, downstream functions receiving it shouldn't re-validate.
- ⚠️ **Don't add backward-compat paths, fallback paths, or legacy shims unless asked.**
- ⚠️ **Don't create type aliases with no semantic value** (e.g., `StreamKind = str`).
- ⚠️ **Don't handle hypothetical input shapes.** Code for the format observed in logs/tests/types, not branches for unseen structures.
- ⚠️ **No no-op pass-through wrappers.** Wrappers must add concrete value (validation, transformation, error translation, compatibility boundary, stable public API).

## 3. Completion quality gate

Every task — bug fix or feature — ends with these checks. State explicitly in the PR description if any are intentionally skipped.

- ⚠️ **No dead code left behind.** Remove unused functions, exports, imports, constants, types, files, and stale wrappers in the same task.
- ⚠️ **Final dead-code sweep across touched areas and new files.**
- ⚠️ Verify before finishing:
  - New symbols are referenced (or intentionally public and documented).
  - Replaced symbols are removed and references updated.
- ⚠️ If something is intentionally left unused for compatibility, **say so explicitly in the final summary**.

## 4. Verification

- ⚠️ **Don't run tests, lints, type checks, or similar verification commands unless explicitly asked.** The user runs these.

## 5. Comments

- ⚠️ **Never use docstrings (`"""..."""`).** Always use inline `#` comments.
- ⚠️ **Comment the *why*, never the *what*.** Non-obvious logic, implicit conventions, design decisions, hidden constraints.
- ⚠️ **Keep comments short — 1–2 lines max.** If it needs more, simplify the code or move detail to the PR description.
- ⚠️ **Don't delete existing comments without asking.** They may capture context not obvious from code.
- ⚠️ **Prefer clear names over comments when code is self-explanatory.**
- ⚠️ **No decorative section comments** (e.g., `# ── Section ──────`).
- ⚠️ **Place comments inside methods/classes**, not above them — method comments are the first line in the body, explaining *why*, not restating the name.
  - ✅ `# Read from the API host, not the sandbox — sandbox containers don't have the user's global git config`
  - ❌ `# Yield persisted events after a given seq` (restates name)

## 6. Exceptions

- ⚠️ **Keep `try/except` narrow** — wrap only the code needing the specific recovery; safely-propagating code stays outside the `try`.
- ⚠️ **Narrow `except` clauses to specific types.** Never `except Exception` when failure modes are known.
- ⚠️ **Don't translate exceptions across boundaries just to change the type.** Catch-and-wrap only when the caller needs a different status/shape.
- ⚠️ **When catching a `ServiceException` subclass at the API boundary, use `exc.status_code`** — don't hardcode a status that shadows the exception's classification.
- ⚠️ **When a function receives an optional targeting parameter (e.g., `cwd`, `workspace_id`) and the value is invalid, raise** — don't silently fall back to a default target.

## 7. Input & security

- ⚠️ **Don't use Python `str.format()` or f-strings to interpolate untrusted content** that may contain `{`/`}` (diffs, code, JSON) — use concatenation or `string.Template`.
- ⚠️ **Add `Field(max_length=...)` to all `str` fields on Pydantic request models;** add `min_length=1` when empty is invalid.

## 8. Imports, typing, structure

- ✅ Ruff (CI + pre-commit on `backend/`) + ESLint/Prettier (CI + lint-staged on `frontend/`) handle formatting and basic lint.
- ✅ mypy strict on `backend/app/` (CI). TypeScript `strict: true` + `noUnusedLocals` + `noUnusedParameters` on `frontend/`.
- ⚠️ **No inline imports** unless needed to break a circular import.
- ⚠️ **Strong typing only.** No `# type: ignore`, `# pyright: ignore`, or `# noqa` to silence typing/import issues — fix types directly.
- ⚠️ **Don't define nested/inline functions.** Use module-level functions or class methods. A helper only used by a class must be a method on it.
- ⚠️ **Module-level constants go at the top of the file**, right after imports/logger/settings — never between classes or functions.
- ⚠️ **Don't call private methods (`_method`) across files.** Make them public (and rename) if cross-file use is needed.
- ⚠️ **Don't use `TypedDict` with `total=False`** when all keys are always present.
- ⚠️ **When a Pydantic response model field has a default, the corresponding frontend TypeScript type must mark it required.**
- ⚠️ **Don't introduce a new frontend type when an existing one has the same shape** — reuse directly.
- ⚠️ **When defining an abstract method signature during a refactor, verify every parameter gets a meaningful value from all call sites.**

## 9. Module organization

- ⚠️ **Logic lives where it belongs.** Factory methods go on the class they construct (e.g., `Chat.from_dict`, `SandboxService.create_for_user`).
- ⚠️ **Group related free functions into a class with static methods** (e.g., `StreamEnvelope.build()` + `StreamEnvelope.sanitize_payload()`).
- ⚠️ **Prefer one data structure over two** when one serves both purposes — derive properties (e.g., `path.is_relative_to(base_dir)`) instead of tracking a parallel set.
- ⚠️ **`backend/app/utils/`** — stateless pure functions only (parsing, formatting, validation). No I/O, DB, services, HTTP. Raise `ValueError`; let callers translate.
- ⚠️ **`backend/app/services/`** — stateful I/O-bound business logic (DB, API calls, sandbox commands). Instantiated with deps, injected via `Depends()`. Raise domain exceptions (`SandboxException`, `ChatException`, ...).
- ⚠️ **`backend/app/core/deps.py`** — FastAPI DI wiring; instantiate services, validate access, translate domain exceptions to `HTTPException` at the boundary.
- ⚠️ **`backend/app/core/security.py`** — auth/authz (token validation, password hashing, encryption, WebSocket auth handshake).
- ⚠️ **If a function does I/O or depends on a service, it doesn't belong in `utils/`.**
- ⚠️ **Endpoint files contain only route handlers** — all business logic belongs in services. Don't instantiate services in route handlers; add a factory in `deps.py` and inject via `Depends()`.
- ⚠️ **Place class definitions** (including `NamedTuple` / `TypedDict`) **at the top of the file** after imports — never between constants.

## 10. Naming

- ⚠️ **Method names describe intent, not mechanism** (`_consume_stream`, not `_iterate_events`).
- ⚠️ **Be concrete, not vague** (`_save_final_snapshot`, not `_persist_final_state`; `_close_redis`, not `_cleanup_redis`).
- ⚠️ **Keep names short when meaning holds** (`_try_create_checkpoint`, not `_create_checkpoint_if_needed`).
- ⚠️ **Don't put implementation details in public method names** (`execute_chat`, not `execute_chat_with_managed_resources`).
- ⚠️ **Use consistent terminology within a module** — pick "cancel" or "revoke", not both.
- ⚠️ **Don't prefix module-level constants with `_`.** Leading underscores are for private class methods/instance vars only.

## 11. Plans & docs

- ⚠️ **`docs/` is the system of record.** Update the doc in the same PR that changes behavior. Stale docs are worse than missing docs.
- ⚠️ **Plans:** small/medium plans live in the PR description; non-trivial plans live as checked-in `plans/active/{topic}.md`. See `plans/README.md`.
- 💭 **Broken-link checks and doc-vs-code drift detection** — open follow-up; not currently mechanized.

## 12. Throughput

- ⚠️ **PRs are short-lived.** If a branch lives more than a few days, split it.
- ⚠️ **A flaky test is a bug.** Fix it or quarantine explicitly with an issue link.
- ⚠️ **Refactors are separate PRs from features.** Reviewers shouldn't have to disentangle them.

---

## When to break a rule

These principles encode current taste. They will be wrong sometimes. When you break one:

1. Say so in the PR description.
2. Open a follow-up to either (a) update the principle or (b) bring the code back in line.

Silent exceptions are how invariants rot. Loud exceptions are how they evolve.
