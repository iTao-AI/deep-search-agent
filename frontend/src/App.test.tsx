import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("Decision Research Agent demo console", () => {
  it("renders the six required operator screens in navigation", () => {
    render(<App />);

    const navigation = screen.getByRole("navigation", {
      name: /demo console screens/i
    });

    [
      "Command Center",
      "Run Lifecycle",
      "Evidence Ledger",
      "Review / Verification",
      "Canonical Result",
      "Architecture Explain Mode"
    ].forEach((screenName) => {
      expect(within(navigation).getByRole("button", { name: screenName })).toBeInTheDocument();
    });
  });

  it("defaults to Chinese and can switch to English", async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByRole("heading", { name: "运行控制台" })).toBeInTheDocument();
    expect(screen.getByText("Agent-first / human-governed / Evidence-governed")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "English" }));

    expect(screen.getByRole("heading", { name: "Run Console" })).toBeInTheDocument();
    expect(screen.getByText("Agent-first / human-governed / Evidence-governed")).toBeInTheDocument();
  });

  it("does not expose chat input or message bubble as the primary interaction", () => {
    render(<App />);

    expect(screen.queryByPlaceholderText(/message|chat|输入消息|聊天/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: /message|chat|输入消息|聊天/i })).not.toBeInTheDocument();
    expect(document.querySelector(".chat-bubble")).not.toBeInTheDocument();
  });

  it("shows static demo data for lifecycle, evidence, review, verification, and result", () => {
    render(<App />);

    expect(screen.getAllByText("run_demo_talent_2026_06_29").length).toBeGreaterThan(0);
    expect(screen.getByText(/evidence_frozen/)).toBeInTheDocument();
    expect(screen.getByText(/ev_001/)).toBeInTheDocument();
    expect(screen.getByText(/claim_candidate_signal/)).toBeInTheDocument();
    expect(screen.getByText("approved")).toBeInTheDocument();
    expect(screen.getByText("verified")).toBeInTheDocument();
    expect(screen.getByText("decision-brief.md")).toBeInTheDocument();
    expect(screen.getByText(/python tools\/decision_research_agent_tool.py run/)).toBeInTheDocument();
  });
});
