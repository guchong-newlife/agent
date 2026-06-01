import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TraceStep:
    step_number: int
    event_type: str  # tool_call, tool_result
    tool_name: str | None = None
    arguments: dict | None = None
    result_summary: str | None = None
    result_count: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "step_number": self.step_number,
            "event_type": self.event_type,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result_summary": self.result_summary,
            "result_count": self.result_count,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
        }


class Tracer:
    def __init__(self):
        self._traces: dict[str, list[TraceStep]] = {}

    def start_trace(self, conversation_id: str, user_query: str):
        self._traces[conversation_id] = []

    def add_step(self, conversation_id: str, step: TraceStep):
        if conversation_id not in self._traces:
            self._traces[conversation_id] = []
        self._traces[conversation_id].append(step)

    def get_trace(self, conversation_id: str) -> list[dict]:
        return [s.to_dict() for s in self._traces.get(conversation_id, [])]

    def complete_trace(self, conversation_id: str, final_answer: str):
        if conversation_id in self._traces:
            self._traces[conversation_id].append(TraceStep(
                step_number=len(self._traces[conversation_id]) + 1,
                event_type="final_answer",
                result_summary=final_answer[:500],
            ))

    def new_conversation_id(self) -> str:
        return str(uuid.uuid4())


tracer = Tracer()
