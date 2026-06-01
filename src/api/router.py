import json
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from .schemas import ChatRequest, DirectSearchRequest
from ..agent.agent_loop import agent_loop
from ..agent.tracer import tracer
from ..agent.tool_registry import tool_registry
from ..search_engines.relational import relational_engine
from ..search_engines.vector_store import vector_engine
from ..search_engines.keyword_search import keyword_engine
from ..search_engines.log_search import log_engine
from ..search_engines.code_search import code_engine

router = APIRouter()


@router.post("/api/chat")
async def chat(req: ChatRequest):
    conversation_id = req.conversation_id or str(uuid.uuid4())

    async def event_stream():
        yield {"event": "conversation_id", "data": json.dumps({"conversation_id": conversation_id}, ensure_ascii=False)}

        async for event in agent_loop.run(req.query, conversation_id):
            yield {"event": event.type, "data": json.dumps(event.data, ensure_ascii=False)}

        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_stream())


@router.get("/api/conversations")
async def list_conversations():
    traces = tracer._traces
    result = []
    for cid, steps in traces.items():
        first_query = ""
        for s in steps:
            if s.event_type == "tool_call" and s.step_number == 1:
                first_query = s.arguments.get("query", "") if s.arguments else ""
        result.append({
            "conversation_id": cid,
            "step_count": len(steps),
            "first_query": first_query,
        })
    return {"conversations": result}


@router.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    trace_data = tracer.get_trace(conversation_id)
    if not trace_data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "steps": trace_data}


@router.post("/api/search/direct")
async def direct_search(req: DirectSearchRequest):
    engines = {
        "relational": relational_engine,
        "vector": vector_engine,
        "keyword": keyword_engine,
        "log": log_engine,
        "code": code_engine,
    }
    engine = engines.get(req.engine)
    if not engine:
        raise HTTPException(status_code=400, detail=f"Unknown engine: {req.engine}")
    results = engine.search(req.query, top_k=req.top_k)
    return {"results": [r.to_dict() for r in results]}


@router.get("/api/stats")
async def stats():
    return {
        "tool_count": len(tool_registry.get_tool_names()),
        "vector_collections": vector_engine.list_collections(),
        "tools": tool_registry.get_tool_names(),
    }
