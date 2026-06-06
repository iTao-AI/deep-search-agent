# Agent Tool Client Implementation Plan

**Goal:** Expose Deep Search Agent as a stable Agent Tool client for upper-layer orchestration.

## Task 1: RED Tests

- [x] Add unit tests for `tools/deep_search_agent_tool.py`.
- [x] Test healthcheck URL and JSON response.
- [x] Test start-task request body and auth header.
- [x] Test get-task and token-usage endpoints.
- [x] Test structured error handling for HTTP failures.
- [x] Add API test for `GET /health`.
- [x] Run focused tests and confirm RED.

## Task 2: GREEN Implementation

- [x] Add `GET /health` to `api/server.py`.
- [x] Add `tools/deep_search_agent_tool.py`.
- [x] Implement env/default config handling.
- [x] Implement GET/POST JSON helpers.
- [x] Implement CLI commands.

## Task 3: Docs

- [x] Add neutral integration docs for the tool client.
- [x] Link from docs index if present.

## Task 4: Verification

- [x] Run focused P18 tests.
- [x] Run relevant API/unit tests.
- [x] Run secret/private-context scan over changed public files.
- [x] Commit P18 changes without staging unrelated `AGENTS.md`.
