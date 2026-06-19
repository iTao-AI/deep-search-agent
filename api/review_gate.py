from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Callable, Literal, NotRequired, TypedDict

from api.review_models import ReviewDecisionRecord
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ReviewGateState(TypedDict):
    workflow_id: str
    run_id: str
    review_id: str
    review_revision: int
    decision_id: NotRequired[str]
    action: NotRequired[str]


@dataclass(frozen=True)
class CheckpointInspection:
    status: Literal["absent", "interrupted", "completed"]
    decision_id: str | None
    action: str | None


class ReviewGateMismatch(RuntimeError):
    pass


class ReviewGate:
    def __init__(
        self,
        checkpoint_path: str,
        decision_loader: Callable[[str], ReviewDecisionRecord | None],
    ):
        self._checkpoint_path = checkpoint_path
        self._decision_loader = decision_loader

    def _compile(self):
        Path(self._checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            self._checkpoint_path,
            check_same_thread=False,
            timeout=5,
        )
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        saver = SqliteSaver(connection)
        saver.setup()

        def wait_for_decision(state: ReviewGateState):
            decision_id = interrupt(
                {
                    "workflow_id": state["workflow_id"],
                    "run_id": state["run_id"],
                    "review_id": state["review_id"],
                    "review_revision": state["review_revision"],
                    "allowed_actions": ["approve", "reject"],
                }
            )
            decision = self._decision_loader(decision_id)
            expected = (
                state["run_id"],
                state["review_id"],
                state["review_revision"],
            )
            actual = (
                decision.run_id if decision else None,
                decision.review_id if decision else None,
                decision.review_revision if decision else None,
            )
            if actual != expected:
                raise ReviewGateMismatch("checkpoint_decision_mismatch")
            return {
                "decision_id": decision_id,
                "action": decision.action,
            }

        builder = StateGraph(ReviewGateState)
        builder.add_node("wait_for_decision", wait_for_decision)
        builder.add_edge(START, "wait_for_decision")
        builder.add_edge("wait_for_decision", END)
        return builder.compile(checkpointer=saver), connection

    def ensure_waiting(
        self,
        *,
        workflow_id: str,
        checkpoint_thread_id: str,
        run_id: str,
        review_id: str,
        review_revision: int,
    ) -> dict:
        graph, connection = self._compile()
        try:
            result = graph.invoke(
                {
                    "workflow_id": workflow_id,
                    "run_id": run_id,
                    "review_id": review_id,
                    "review_revision": review_revision,
                },
                config={
                    "configurable": {
                        "thread_id": checkpoint_thread_id,
                    }
                },
                durability="sync",
            )
            return result["__interrupt__"][0].value
        finally:
            connection.close()

    def resume(self, *, checkpoint_thread_id: str, decision_id: str) -> dict:
        graph, connection = self._compile()
        try:
            return graph.invoke(
                Command(resume=decision_id),
                config={"configurable": {"thread_id": checkpoint_thread_id}},
                durability="sync",
            )
        finally:
            connection.close()

    def inspect(self, checkpoint_thread_id: str) -> CheckpointInspection:
        graph, connection = self._compile()
        try:
            snapshot = graph.get_state(
                {"configurable": {"thread_id": checkpoint_thread_id}}
            )
            values = dict(snapshot.values or {})
            if snapshot.next:
                return CheckpointInspection(
                    status="interrupted",
                    decision_id=values.get("decision_id"),
                    action=values.get("action"),
                )
            if values.get("decision_id"):
                return CheckpointInspection(
                    status="completed",
                    decision_id=values["decision_id"],
                    action=values.get("action"),
                )
            return CheckpointInspection(
                status="absent",
                decision_id=None,
                action=None,
            )
        finally:
            connection.close()
