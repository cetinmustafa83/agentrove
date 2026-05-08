# Definition of Done

Before opening a PR, verify each item below. If a box can't be checked, say so in the PR description — don't silently skip.

---

## Universal checklist

- [ ] **Plan documented.** Small/medium → 3–10 bullets stated up front (issue, conversation, or PR description). Non-trivial → checked-in `plans/active/{topic}.md` linked from the PR. Either way: domains touched, pattern choices, verification approach.

- [ ] **Golden principles followed.** Walk through `docs/golden_principles.md` for the layers you touched. If you broke a rule, say so and link a follow-up.

- [ ] **Dead-code sweep.** No unused functions, exports, imports, constants, types, files, or stale wrappers left behind. Replaced symbols are deleted; references updated. (See golden principle §3.)

- [ ] **Comments are inline `#` (Python) / `//` (TS), short, and explain *why*** — not what. No new docstrings. No decorative section banners. (See golden principle §5.)

- [ ] **No `# type: ignore` / `# noqa` / `// @ts-ignore` introduced** to silence type or lint errors. Fix the underlying issue. (See golden principle §8.)

- [ ] **Docs / artifact maps updated.** If you changed a state machine, vocabulary, cross-domain edge, or load-bearing pattern, the relevant `docs/domains/*.md` or `docs/artifacts/**/*.md` was updated *in the same PR*.

---

## Per-artifact extras

### SQLAlchemy models / Alembic migrations

- [ ] Migration generated via `docker compose exec api alembic revision --autogenerate -m "..."` — not hand-written from scratch (manual edits for correctness are fine).
- [ ] Migration filename describes the change (Alembic-default slug is OK).
- [ ] All new columns have explicit `nullable=` set.
- [ ] Columns with Python defaults also have `server_default=` (the two go together).
- [ ] String columns have explicit max length (e.g., `String(64)`).
- [ ] DateTime columns use `DateTime(timezone=True)`.
- [ ] No redundant `index=True` on an FK column already covered by a composite index that starts with that column.
- [ ] Don't edit a merged migration — write a new one.

### FastAPI endpoints

- [ ] Route handler contains only routing concerns. Business logic is in a service.
- [ ] Services are injected via `Depends()` from `core/deps.py` — endpoints don't import `SessionLocal`.
- [ ] All Pydantic request `str` fields have `Field(max_length=...)`. `min_length=1` when empty is invalid.
- [ ] Domain exceptions (`ChatException`, `SandboxException`, etc.) are raised; status codes come from `exc.status_code`, not hardcoded.
- [ ] Pydantic response model fields with defaults are mirrored as **required** in the matching frontend TypeScript type.

### Backend services

- [ ] Service is class-based, instantiated in `deps.py`, takes its `SessionLocal` factory as a constructor arg.
- [ ] Domain exception raised, not bare `Exception` / `ValueError`.
- [ ] `try/except` blocks are narrow (named exception type, smallest scope).

### Backend tests

- [ ] Tests live directly under `backend/tests/` (e.g., `tests/test_auth.py`) — not nested by endpoint folder.
- [ ] Tests go through HTTP/WebSocket routes — no standalone service tests.
- [ ] External boundaries (email, Docker, ACP/provider processes, Redis) are stubbed; the rest runs real.
- [ ] Provider tests use fake ACP boundaries — no live Claude/Codex/OpenCode/Cursor/Copilot calls.

### Frontend components

- [ ] No raw `<button>`, `<input>`, `<select>`, or `<a>` for interactive elements when a `components/ui/primitives/` primitive exists. Use `variant="unstyled"` for fully custom looks.
- [ ] Hooks (`useState`, `useCallback`, `useMemo`, `useEffect`) never appear after a conditional early return.
- [ ] Mount-only effects use `useMountEffect()`, not raw `useEffect(() => ..., [])`.
- [ ] Tailwind: no hardcoded hex / default-palette colors; semantic tokens only (`surface-*`, `text-text-*`, `border-border-*`). Every light class has a `dark:` counterpart.
- [ ] Heavy libraries (`xlsx`, `jszip`, `xterm`, `@monaco-editor/react`, `react-vnc`, `qrcode`, `dompurify`, `mermaid`) are dynamically imported.
- [ ] No barrel/`index.ts` files added — import from source directly.

### ACP / provider changes

- [ ] Don't put user-facing data in `_meta` / `field_meta`. If ACP has no first-class field, surface the limitation, don't smuggle.
- [ ] Per-provider behavior matches what `docs/domains/providers.md` documents. If you change adapter behavior, update the domain map in the same PR.

### Streaming / `StreamEnvelope`

- [ ] `StreamEnvelope.sanitize_payload()` is applied to outbound payloads with arbitrary content.
- [ ] New event kinds: added to `SNAPSHOT_EVENT_KINDS` if they should be persisted; control events flush immediately.
- [ ] Reconnection contract preserved (`?seq=N` resumes from the right point).

### Sandbox / Git

- [ ] Cwd is propagated through the full chain (backend endpoint → service → frontend service → React Query hook → UI). Don't silently fall back to workspace root.
- [ ] React Query keys for cwd-scoped operations include `cwd` in the key; bulk invalidation uses a prefix key (e.g., `gitBranchesAll(id)`).

---

## When something fails

- **Tests** — fix the test or fix the code; never skip without an issue link.
- **CI flake** — re-run once. If it flakes again, surface it; don't keep retrying silently.
- **Pre-commit not installed** — `git config core.hooksPath .githooks` to enable.

---

## What this checklist isn't

- Not a substitute for reading the artifact docs and domain maps **before** writing code.
- Not a substitute for a real plan.
- Not a license to mechanically tick boxes — each item exists because something broke once.
