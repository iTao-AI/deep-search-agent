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

- [ ] Write failing tests that expect health success and failure to render bounded UI states.
- [ ] Run `cd frontend && npm run test` and verify the tests fail because no live client/UI exists.
- [ ] Implement `apiClient.ts` with `getHealth`, `startRun`, `getRun`, `getResult`, and `normalizeClientError`.
- [ ] Run `cd frontend && npm run test` and keep existing static tests passing.
- [ ] Commit `feat(frontend): add demo console api client`.

## Task 2: Live Run State Machine

**Files:**
- Create: `frontend/src/useLiveRun.ts`
- Modify: `frontend/src/App.test.tsx`

- [ ] Write failing tests for `start -> poll -> result`, poll timeout, and stale response isolation.
- [ ] Run `cd frontend && npm run test` and verify the tests fail for missing behavior.
- [ ] Implement `useLiveRun` with explicit statuses: `static`, `checking`, `ready`, `starting`, `polling`, `result`, `error`.
- [ ] Use React `useEffect` cleanup/ignore semantics for stale async responses.
- [ ] Run `cd frontend && npm run test`.
- [ ] Commit `feat(frontend): orchestrate live demo runs`.

## Task 3: Console Presentation

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/i18n.ts`
- Modify: `frontend/src/styles.css`
- Modify: `frontend/src/App.test.tsx`

- [ ] Write failing tests asserting Static Demo is default, Live Backend controls exist, and no chat textbox appears.
- [ ] Run `cd frontend && npm run test` and verify expected failures.
- [ ] Add mode switch, base URL input, health button, start button, live state panel, and canonical result preview.
- [ ] Keep existing six operator screens and Chinese default.
- [ ] Run `cd frontend && npm run test`.
- [ ] Commit `feat(frontend): expose live demo console flow`.

## Task 4: Docs And Verification

**Files:**
- Modify: `README.md`
- Modify: `README_CN.md`
- Modify: `docs/superpowers/specs/2026-06-30-react-demo-console-live-flow-design.md`
- Modify: `docs/superpowers/plans/2026-06-30-react-demo-console-live-flow-implementation.md`

- [ ] Update README docs to say the React demo console supports Static Demo and Live Backend modes.
- [ ] Run `cd frontend && npm run test`.
- [ ] Run `cd frontend && npm run lint`.
- [ ] Run `cd frontend && npm run build`.
- [ ] Run `python -m pytest tests/unit/test_frontend_retirement.py -q`.
- [ ] Run `git diff --check`.
- [ ] Commit `docs(frontend): document live demo console mode`.

## Final Review

- [ ] Confirm no backend, API, DB, runtime, Docker, review, verification, LangGraph, DeepAgents, or LangSmith files changed.
- [ ] Confirm no API key, `.env`, local path, raw traceback, or private Career/GStack path is present in the diff.
- [ ] Confirm PR scope remains demo console frontend + docs only.
