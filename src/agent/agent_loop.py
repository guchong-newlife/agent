import json
import asyncio
import time
from dataclasses import dataclass
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI
from ..config import settings
from .tool_registry import tool_registry
from .tool_definitions import TOOL_DEFINITIONS, SYSTEM_PROMPT
from .tracer import tracer, TraceStep


@dataclass
class AgentEvent:
    type: str  # tool_call, tool_result, final_answer, error
    data: dict


class AgentLoop:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )

    async def run(self, user_query: str, conversation_id: str) -> AsyncGenerator[AgentEvent, None]:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ]

        tracer.start_trace(conversation_id, user_query)
        iteration = 0

        while iteration < settings.agent_max_iterations:
            iteration += 1

            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=settings.deepseek_model,
                        messages=messages,
                        tools=TOOL_DEFINITIONS,
                        tool_choice="auto",
                        stream=False,
                    ),
                    timeout=30,
                )
            except asyncio.TimeoutError:
                yield AgentEvent(type="error", data={"message": "模型响应超时"})
                break

            choice = response.choices[0]
            assistant_message = choice.message

            if assistant_message.tool_calls:
                tool_results = []
                for tc in assistant_message.tool_calls:
                    tool_name = tc.function.name
                    try:
                        tool_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

                    yield AgentEvent(type="tool_call", data={
                        "tool_name": tool_name,
                        "arguments": tool_args,
                        "iteration": iteration,
                    })

                    try:
                        result = await asyncio.wait_for(
                            tool_registry.execute(tool_name, **tool_args),
                            timeout=15,
                        )
                    except asyncio.TimeoutError:
                        result = [{"error": "工具执行超时"}]

                    summary = self._summarize_result(result)
                    yield AgentEvent(type="tool_result", data={
                        "tool_name": tool_name,
                        "result_summary": summary,
                        "result_count": len(result),
                        "iteration": iteration,
                    })

                    tracer.add_step(conversation_id, TraceStep(
                        step_number=iteration,
                        event_type="tool_call",
                        tool_name=tool_name,
                        arguments=tool_args,
                    ))
                    tracer.add_step(conversation_id, TraceStep(
                        step_number=iteration,
                        event_type="tool_result",
                        tool_name=tool_name,
                        result_summary=summary,
                        result_count=len(result),
                    ))

                    result_text = json.dumps(result, ensure_ascii=False)
                    if len(result_text) > 8000:
                        result_text = result_text[:8000] + "...(结果已截断)"

                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tc],
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_text,
                    })

            else:
                content = assistant_message.content or ""
                yield AgentEvent(type="final_answer", data={
                    "content": content,
                    "iterations": iteration,
                    "trace": tracer.get_trace(conversation_id),
                })
                tracer.complete_trace(conversation_id, content)
                return

        yield AgentEvent(type="final_answer", data={
            "content": "已达到最大搜索轮次。基于目前已收集的信息，建议您缩小问题范围后再试。",
            "iterations": iteration,
            "trace": tracer.get_trace(conversation_id),
        })

    def _summarize_result(self, result: list[dict]) -> str:
        if not result:
            return "未找到匹配结果"
        if len(result) <= 3:
            items = []
            for r in result[:3]:
                title = r.get("title") or r.get("name") or r.get("id", "?")
                items.append(str(title))
            return f"找到 {len(result)} 条结果: {', '.join(items)}"
        items = []
        for r in result[:3]:
            title = r.get("title") or r.get("name") or r.get("id", "?")
            items.append(str(title))
        return f"找到 {len(result)} 条结果，前3条: {', '.join(items)}"


agent_loop = AgentLoop()
