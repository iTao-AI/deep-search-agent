import { useCallback, useRef, useState } from "react";

import {
  DEFAULT_BACKEND_BASE_URL,
  getHealth,
  getResult,
  getRun,
  normalizeClientError,
  startRun,
  type ClientError,
  type HealthResponse,
  type RunCreationResponse,
  type RunProjection,
  type RunResultResponse
} from "./apiClient";

export type DemoMode = "static" | "live";
export type LiveStatus =
  | "static"
  | "idle"
  | "checking"
  | "ready"
  | "starting"
  | "polling"
  | "result"
  | "error";

export type LiveRunOptions = {
  pollIntervalMs?: number;
  waitTimeoutMs?: number;
};

export type LiveRunState = {
  baseUrl: string;
  created?: RunCreationResponse;
  error?: ClientError;
  health?: HealthResponse;
  mode: DemoMode;
  result?: RunResultResponse;
  run?: RunProjection;
  status: LiveStatus;
};

const DEFAULT_POLL_INTERVAL_MS = 1000;
const DEFAULT_WAIT_TIMEOUT_MS = 600_000;
const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled", "timeout", "timed_out"]);

export function useLiveRun(options: LiveRunOptions = {}) {
  const pollIntervalMs = options.pollIntervalMs ?? DEFAULT_POLL_INTERVAL_MS;
  const waitTimeoutMs = options.waitTimeoutMs ?? DEFAULT_WAIT_TIMEOUT_MS;
  const requestVersion = useRef(0);
  const [state, setState] = useState<LiveRunState>({
    baseUrl: DEFAULT_BACKEND_BASE_URL,
    mode: "static",
    status: "static"
  });

  const isCurrent = useCallback((version: number) => requestVersion.current === version, []);
  const nextVersion = useCallback(() => {
    requestVersion.current += 1;
    return requestVersion.current;
  }, []);

  const setMode = useCallback(
    (mode: DemoMode) => {
      nextVersion();
      setState((current) => ({
        ...current,
        error: undefined,
        mode,
        status: mode === "static" ? "static" : "idle"
      }));
    },
    [nextVersion]
  );

  const setBaseUrl = useCallback(
    (baseUrl: string) => {
      nextVersion();
      setState((current) => ({
        ...current,
        baseUrl,
        error: undefined,
        health: undefined,
        status: current.mode === "static" ? "static" : "idle"
      }));
    },
    [nextVersion]
  );

  const checkHealth = useCallback(async () => {
    const version = nextVersion();
    const baseUrl = state.baseUrl;
    setState((current) => ({ ...current, error: undefined, mode: "live", status: "checking" }));
    try {
      const health = await getHealth(baseUrl);
      if (!isCurrent(version)) {
        return;
      }
      setState((current) => ({
        ...current,
        error: undefined,
        health,
        mode: "live",
        status: "ready"
      }));
    } catch (error) {
      if (!isCurrent(version)) {
        return;
      }
      setState((current) => ({
        ...current,
        error: normalizeClientError(error),
        mode: "live",
        status: "error"
      }));
    }
  }, [isCurrent, nextVersion, state.baseUrl]);

  const runGoldenPath = useCallback(async () => {
    const version = nextVersion();
    const baseUrl = state.baseUrl;
    let activeRunId: string | undefined;
    setState((current) => ({
      ...current,
      created: undefined,
      error: undefined,
      mode: "live",
      result: undefined,
      run: undefined,
      status: "starting"
    }));
    try {
      const created = await startRun(baseUrl);
      activeRunId = created.run_id;
      if (!isCurrent(version)) {
        return;
      }
      setState((current) => ({ ...current, created, status: "polling" }));

      const run = await pollRun({
        baseUrl,
        isCurrent: () => isCurrent(version),
        pollIntervalMs,
        runId: created.run_id,
        waitTimeoutMs
      });
      if (!isCurrent(version)) {
        return;
      }
      setState((current) => ({ ...current, run }));

      const result = await getResult(baseUrl, created.run_id);
      if (!isCurrent(version)) {
        return;
      }
      setState((current) => ({
        ...current,
        result,
        run,
        status: "result"
      }));
    } catch (error) {
      if (!isCurrent(version)) {
        return;
      }
      setState((current) => ({
        ...current,
        error: normalizeClientError(error, activeRunId),
        status: "error"
      }));
    }
  }, [isCurrent, nextVersion, pollIntervalMs, state.baseUrl, waitTimeoutMs]);

  return {
    checkHealth,
    runGoldenPath,
    setBaseUrl,
    setMode,
    state
  };
}

async function pollRun({
  baseUrl,
  isCurrent,
  pollIntervalMs,
  runId,
  waitTimeoutMs
}: {
  baseUrl: string;
  isCurrent: () => boolean;
  pollIntervalMs: number;
  runId: string;
  waitTimeoutMs: number;
}) {
  const deadline = Date.now() + waitTimeoutMs;
  while (isCurrent()) {
    const run = await getRun(baseUrl, runId);
    if (isTerminal(run.execution_status)) {
      return run;
    }
    const remainingMs = deadline - Date.now();
    if (remainingMs <= 0) {
      throw new Error("run_wait_timeout");
    }
    await sleep(Math.min(pollIntervalMs, remainingMs));
  }
  throw new Error("stale_request");
}

function isTerminal(status: string | undefined) {
  return typeof status === "string" && TERMINAL_STATUSES.has(status);
}

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}
