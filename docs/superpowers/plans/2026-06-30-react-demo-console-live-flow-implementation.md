# React Demo Console Live Flow Implementation Plan

> **For agentic workers:** Implement inline in this session. Do not use subagents for this repository unless the user explicitly authorizes them. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded Live Demo Mode to the React demo console while preserving Static Demo Mode as the reliable interview fallback.

**Architecture:** Keep backend calls in a small frontend API client, keep run orchestration in a React hook, and keep `App.tsx` focused on presentation. The frontend consumes the canonical API contract and never becomes business authority.

**Tech Stack:** React 19, TypeScript, Vite, Vitest, Testing Library, existing FastAPI contract.

---

## File Structure

- Create `frontend/src/apiClient.ts`: typed browser fetch wrappers for health, run creation, run polling, result retrieval, and bounded error normalization.
- Create `frontend/src/useLiveRun.ts`: React state machine for static/live mode, health probe, run start, polling, and result retrieval.
- Modify `frontend/src/App.tsx`: wire the hook into existing panels and add the live controls/status surface.
- Modify `frontend/src/i18n.ts`: add Chinese/English copy for live mode controls and errors.
- Modify `frontend/src/styles.css`: add compact mode switch, live control, and error/result styles.
- Modify `frontend/src/App.test.tsx`: add RED/GREEN tests for live flow and static fallback.
- Modify `README.md` and `README_CN.md`: document demo console live/static modes.

## Task 1: Frontend API Client

**Files:**
- Create: `frontend/src/apiClient.ts`
- Test: `frontend/src/App.test.tsx`

- [x] Write failing tests that expect health success and failure to render bounded UI states.
- [x] Run `cd frontend && npm run test` and verify the tests fail because no live client/UI exists.
- [x] Implement `apiClient.ts` with `getHealth`, `startRun`, `getRun`, `getResult`, and `normalizeClientError`.
- [x] Run `cd frontend && npm run test` and keep existing static tests passing.
- [x] Commit `feat(frontend): add demo console api client`.

## Task 2: Live Run State Machine

**Files:**
- Create: `frontend/src/useLiveRun.ts`
- Modify: `frontend/src/App.test.tsx`

- [x] Write failing tests for `start -> poll -> result`, poll timeout, and stale response isolation.
- [x] Run `cd frontend && npm run test` and verify the tests fail for missing behavior.
- [x] Implement `useLiveRun` with explicit statuses: `static`, `checking`, `ready`, `starting`, `polling`, `result`, `error`.
- [x] Use stale request versioning equivalent to React cleanup/ignore semantics for async responses.
- [x] Run `cd frontend && npm run test`.
- [x] Commit `feat(frontend): orchestrate live demo runs`.

## Task 3: Console Presentation

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/i18n.ts`
- Modify: `frontend/src/styles.css`
- Modify: `frontend/src/App.test.tsx`

- [x] Write failing tests asserting Static Demo is default, Live Backend controls exist, and no chat textbox appears.
- [x] Run `cd frontend && npm run test` and verify expected failures.
- [x] Add mode switch, base URL input, health button, start button, live state panel, and canonical result preview.
- [x] Keep existing six operator screens and Chinese default.
- [x] Run `cd frontend && npm run test`.
- [x] Commit `feat(frontend): expose live demo console flow`.

## Task 4: Docs And Verification

**Files:**
- Modify: `README.md`
- Modify: `README_CN.md`
- Modify: `docs/superpowers/specs/2026-06-30-react-demo-console-live-flow-design.md`
- Modify: `docs/superpowers/plans/2026-06-30-react-demo-console-live-flow-implementation.md`

- [x] Update README docs to say the React demo console supports Static Demo and Live Backend modes.
- [x] Run `cd frontend && npm run test`.
- [x] Run `cd frontend && npm run lint`.
- [x] Run `cd frontend && npm run build`.
- [x] Run `python -m pytest tests/unit/test_frontend_retirement.py -q`.
- [x] Run `git diff --check`.
- [x] Commit `docs(frontend): document live demo console mode`.

## Final Review

- [x] Confirm no backend, API, DB, runtime, Docker, review, verification, LangGraph, DeepAgents, or LangSmith files changed.
- [x] Confirm no API key, `.env`, local path, raw traceback, or private Career/GStack path is present in the diff.
- [x] Confirm PR scope remains demo console frontend + docs only.
