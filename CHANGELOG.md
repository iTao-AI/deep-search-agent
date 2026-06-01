# Changelog

All notable changes to this project are documented in this file.

## [0.0.1.0] - 2026-06-02

### Added

- Added API key protection for REST API routes and WebSocket connections, with development-mode passthrough when `API_SECRET` is unset.
- Added SQLite-backed task persistence so task status can be queried after server restarts through `GET /api/tasks/{thread_id}`.
- Added GitHub Actions CI for backend tests and frontend production builds.
- Added Phase 8 production-readiness spec, implementation plan, and public evidence documentation.

### Changed

- Switched example LLM configuration toward DeepSeek defaults while keeping OpenAI-compatible environment variables.
- Wired frontend API calls to send `X-API-Key`, and WebSocket connections to pass `api_key` where browser APIs cannot set custom headers.
- Reduced duplicate Tavily calls by routing the real `internet_search` tool through per-thread search de-duplication.
- Restored prompt execution-order instructions and normalized prompt config line endings.

### Fixed

- Fixed CORS preflight handling so browser requests still work when API key auth is enabled.
- Fixed repeated frontend thread submissions by resetting existing SQLite task rows instead of failing on duplicate `thread_id`.
- Fixed WebSocket auth failures retrying forever by surfacing a clear client-side error.
- Fixed evidence docs so benchmark and E2E follow-up status no longer claim unsupported token before/after conclusions.
