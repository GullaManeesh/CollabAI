import json
import re
import time
import logging
from datetime import datetime
from bson import ObjectId

import backend.database as db
from backend.services.retrieval_service import retrieve, format_context
from backend.llm.client import complete
from backend.agents.prompts import ROUTER_PROMPT, RESEARCH_PROMPT, PLANNER_PROMPT, CRITIC_PROMPT, DOCS_PROMPT
from backend.agents.state import CopilotState
from backend.ws.manager import manager

logger = logging.getLogger(__name__)

async def _update_run_in_db(state: CopilotState, current_step: str, status: str = "running", final_answer: str = None, citations: list = None, error: str = None):
    run_oid = ObjectId(state["run_id"])
    
    total_tokens = sum(s.get("tokens_in", 0) + s.get("tokens_out", 0) for s in state["trace"])
    total_latency_ms = sum(s.get("latency_ms", 0) for s in state["trace"])
    
    update_doc = {
        "trace": state["trace"],
        "current_step": current_step,
        "status": status,
        "total_tokens": total_tokens,
        "total_latency_ms": total_latency_ms,
        "revision_count": state.get("revision_count", 0),
        "intent": state.get("intent")
    }
    
    if final_answer is not None:
        update_doc["final_answer"] = final_answer
    if citations is not None:
        update_doc["citations"] = citations
    if error is not None:
        update_doc["error"] = error
        
    if status in ("done", "failed"):
        update_doc["completed_at"] = datetime.utcnow()
        
    await db.agent_runs_col.update_one(
        {"_id": run_oid},
        {"$set": update_doc}
    )

def _build_trace_entry(step_num: int, agent: str, input_summary: str, output_summary: str, llm_res=None) -> dict:
    entry = {
        "step": step_num,
        "agent": agent,
        "input_summary": input_summary[:300],
        "output_summary": output_summary[:500],
        "started_at": datetime.utcnow()
    }
    if llm_res:
        entry.update({
            "provider": llm_res.provider,
            "model": llm_res.model,
            "tokens_in": llm_res.tokens_in,
            "tokens_out": llm_res.tokens_out,
            "latency_ms": llm_res.latency_ms
        })
    return entry

async def router_node(state: CopilotState) -> dict:
    logger.info(f"Running router node for run {state['run_id']}")
    
    # 1. Build messages including history context
    history_context = []
    for turn in state["history"][-2:]:  # last 2 turns
        role = "user" if turn.get("sender_type") == "user" else "assistant"
        history_context.append({"role": role, "content": turn.get("content", "")})
        
    router_messages = [{"role": "system", "content": ROUTER_PROMPT}]
    router_messages.extend(history_context)
    router_messages.append({"role": "user", "content": state["query"]})
    
    intent = "factual"
    reasoning = "default fallback"
    trace_entry = None
    
    try:
        llm_res = await complete(
            messages=router_messages,
            tier="small",
            json_mode=True,
            temperature=0.0
        )
        
        # Clean potential markdown block fences
        cleaned_text = re.sub(r"```json|```", "", llm_res.text).strip()
        parsed = json.loads(cleaned_text)
        
        intent = parsed.get("intent", "factual")
        reasoning = parsed.get("reasoning", "")
        
        trace_entry = _build_trace_entry(
            step_num=len(state["trace"]) + 1,
            agent="router",
            input_summary=state["query"],
            output_summary=llm_res.text,
            llm_res=llm_res
        )
    except Exception as e:
        logger.error(f"Router node execution failed: {e}. Defaulting to factual.")
        trace_entry = _build_trace_entry(
            step_num=len(state["trace"]) + 1,
            agent="router",
            input_summary=state["query"],
            output_summary=f"Router error: {str(e)}"
        )
        
    state["trace"].append(trace_entry)
    state["intent"] = intent
    state["current_step"] = "router"
    
    await _update_run_in_db(state, "router")
    return state

async def research_node(state: CopilotState) -> dict:
    logger.info(f"Running research node for run {state['run_id']}")
    
    ws_oid = ObjectId(state["workspace_id"])
    query = state["query"]
    
    # 1. Retrieve documents / messages
    retrieved_chunks = await retrieve(workspace_id=ws_oid, query=query, k=6)
    
    # Serialize chunks for state
    serialized_chunks = []
    for chunk in retrieved_chunks:
        serialized_chunks.append({
            "text": chunk.text,
            "score": chunk.score,
            "source_type": chunk.source_type,
            "filename": chunk.filename,
            "page": chunk.page,
            "sender_name": chunk.sender_name,
            "document_id": chunk.document_id,
            "message_id": chunk.message_id,
            "created_at": chunk.created_at.isoformat()
        })
        
    state["retrieved"] = serialized_chunks
    context_str = format_context(retrieved_chunks)
    
    # Get workspace name
    workspace = await db.workspaces_col.find_one({"_id": ws_oid})
    ws_name = workspace["name"] if workspace else "Workspace"
    
    system_prompt = RESEARCH_PROMPT.format(
        workspace_name=ws_name,
        context=context_str
    )
    
    research_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]
    
    try:
        llm_res = await complete(
            messages=research_messages,
            tier="default",
            temperature=0.3
        )
        
        trace_entry = _build_trace_entry(
            step_num=len(state["trace"]) + 1,
            agent="research",
            input_summary=query,
            output_summary=llm_res.text,
            llm_res=llm_res
        )
        state["research_output"] = llm_res.text
    except Exception as e:
        logger.error(f"Research node failed: {e}")
        trace_entry = _build_trace_entry(
            step_num=len(state["trace"]) + 1,
            agent="research",
            input_summary=query,
            output_summary=f"Research error: {str(e)}"
        )
        state["research_output"] = f"Failed to retrieve and research workspace data: {str(e)}"
        
    state["trace"].append(trace_entry)
    state["current_step"] = "research"
    await _update_run_in_db(state, "research")
    return state

async def planner_node(state: CopilotState) -> dict:
    logger.info(f"Running planner node for run {state['run_id']}")
    
    ws_oid = ObjectId(state["workspace_id"])
    workspace = await db.workspaces_col.find_one({"_id": ws_oid})
    ws_name = workspace["name"] if workspace else "Workspace"
    
    # 1. Build prompt based on whether it is a revision or initial run
    is_revision = state.get("revision_count", 0) > 0
    
    system_prompt = PLANNER_PROMPT.format(
        workspace_name=ws_name
    )
    
    user_content = f"User Request: {state['query']}\n\nResearch Findings:\n{state['research_output']}"
    if is_revision:
        user_content += f"\n\nPrevious Plan:\n{state['plan_output']}\n\nCritique / Issues to Address:\n{state['critique']}"
        
    planner_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    parsed_tasks = []
    stripped_plan = ""
    
    try:
        llm_res = await complete(
            messages=planner_messages,
            tier="default",
            temperature=0.4
        )
        
        raw_text = llm_res.text
        
        # Extract json task list block at the end
        # Regex to capture ```json { ... } ``` or ``` { ... } ```
        json_pattern = re.compile(r"```(?:json)?\s*(\{\s*\"tasks\".*?\})\s*```", re.DOTALL)
        match = json_pattern.search(raw_text)
        
        if match:
            json_str = match.group(1).strip()
            # Strip block from text
            stripped_plan = raw_text.replace(match.group(0), "").strip()
            try:
                parsed_data = json.loads(json_str)
                parsed_tasks = parsed_data.get("tasks", [])
            except Exception as pe:
                logger.error(f"Failed to parse Planner task JSON block: {pe}")
        else:
            # Fallback if block is not fenced
            stripped_plan = raw_text
            # Try to search for raw JSON object if it exists at the end
            try:
                json_raw_match = re.search(r"(\{\s*\"tasks\".*?\})$", raw_text, re.DOTALL)
                if json_raw_match:
                    parsed_data = json.loads(json_raw_match.group(1))
                    parsed_tasks = parsed_data.get("tasks", [])
                    stripped_plan = raw_text.replace(json_raw_match.group(0), "").strip()
            except:
                pass
                
        # If parsing tasks succeeded, we store them in state
        state["tasks"] = parsed_tasks
        state["plan_output"] = stripped_plan
        
        trace_entry = _build_trace_entry(
            step_num=len(state["trace"]) + 1,
            agent="planner",
            input_summary=user_content,
            output_summary=raw_text,
            llm_res=llm_res
        )
    except Exception as e:
        logger.error(f"Planner node failed: {e}")
        trace_entry = _build_trace_entry(
            step_num=len(state["trace"]) + 1,
            agent="planner",
            input_summary=user_content,
            output_summary=f"Planner error: {str(e)}"
        )
        state["plan_output"] = f"Failed to generate plan: {str(e)}"
        
    state["trace"].append(trace_entry)
    state["revision_count"] = state.get("revision_count", 0) + 1
    state["current_step"] = "planner"
    await _update_run_in_db(state, "planner")
    return state

async def critic_node(state: CopilotState) -> dict:
    logger.info(f"Running critic node for run {state['run_id']}")
    
    ws_oid = ObjectId(state["workspace_id"])
    workspace = await db.workspaces_col.find_one({"_id": ws_oid})
    ws_name = workspace["name"] if workspace else "Workspace"
    
    # Format current revision limit constraint
    # Cap at 1 revision total
    needs_revision_val = "true | false"
    
    critic_prompt_formatted = CRITIC_PROMPT.format(needs_revision_val=needs_revision_val)
    
    critic_messages = [
        {"role": "system", "content": critic_prompt_formatted},
        {"role": "user", "content": f"Workspace: {ws_name}\nUser Query: {state['query']}\n\nProposed Plan:\n{state['plan_output']}"}
    ]
    
    needs_revision = False
    critique_str = ""
    
    try:
        llm_res = await complete(
            messages=critic_messages,
            tier="small",
            json_mode=True,
            temperature=0.1
        )
        
        cleaned_text = re.sub(r"```json|```", "", llm_res.text).strip()
        parsed = json.loads(cleaned_text)
        
        needs_revision = parsed.get("needs_revision", False)
        critique_str = cleaned_text
        
        trace_entry = _build_trace_entry(
            step_num=len(state["trace"]) + 1,
            agent="critic",
            input_summary=state["plan_output"],
            output_summary=llm_res.text,
            llm_res=llm_res
        )
    except Exception as e:
        logger.error(f"Critic node failed: {e}")
        trace_entry = _build_trace_entry(
            step_num=len(state["trace"]) + 1,
            agent="critic",
            input_summary=state["plan_output"],
            output_summary=f"Critic error: {str(e)}"
        )
        needs_revision = False
        critique_str = json.dumps({"needs_revision": False, "issues": [f"Critic failed: {str(e)}"], "strengths": []})
        
    state["trace"].append(trace_entry)
    state["needs_revision"] = needs_revision
    state["critique"] = critique_str
    state["current_step"] = "critic"
    await _update_run_in_db(state, "critic")
    return state

async def docs_node(state: CopilotState) -> dict:
    logger.info(f"Running docs node for run {state['run_id']}")
    
    ws_oid = ObjectId(state["workspace_id"])
    workspace = await db.workspaces_col.find_one({"_id": ws_oid})
    ws_name = workspace["name"] if workspace else "Workspace"
    
    # Format retrieved context
    # reconstruct RetrievedChunks
    from backend.services.retrieval_service import RetrievedChunk
    retrieved_list = []
    for c in state["retrieved"]:
        retrieved_list.append(
            RetrievedChunk(
                text=c["text"],
                score=c["score"],
                source_type=c["source_type"],
                filename=c.get("filename"),
                page=c.get("page"),
                sender_name=c.get("sender_name"),
                document_id=c.get("document_id"),
                message_id=c.get("message_id"),
                created_at=datetime.fromisoformat(c["created_at"]) if isinstance(c["created_at"], str) else c["created_at"]
            )
        )
    context_str = format_context(retrieved_list)
    
    system_prompt = DOCS_PROMPT.format(
        workspace_name=ws_name,
        context=context_str
    )
    
    docs_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state["query"]}
    ]
    
    try:
        llm_res = await complete(
            messages=docs_messages,
            tier="default",
            temperature=0.3
        )
        
        trace_entry = _build_trace_entry(
            step_num=len(state["trace"]) + 1,
            agent="docs",
            input_summary=state["query"],
            output_summary=llm_res.text,
            llm_res=llm_res
        )
        state["docs_output"] = llm_res.text
    except Exception as e:
        logger.error(f"Docs node failed: {e}")
        trace_entry = _build_trace_entry(
            step_num=len(state["trace"]) + 1,
            agent="docs",
            input_summary=state["query"],
            output_summary=f"Docs error: {str(e)}"
        )
        state["docs_output"] = f"Failed to generate documentation: {str(e)}"
        
    state["trace"].append(trace_entry)
    state["current_step"] = "docs"
    await _update_run_in_db(state, "docs")
    return state

async def finalize_node(state: CopilotState) -> dict:
    logger.info(f"Running finalize node for run {state['run_id']}")
    
    intent = state["intent"]
    final_answer = ""
    
    if intent == "factual":
        final_answer = state["research_output"]
    elif intent == "planning":
        plan = state["plan_output"]
        
        # Assemble critique summary if it was critiqued
        critique_summary = ""
        if state.get("critique"):
            try:
                parsed = json.loads(state["critique"])
                issues = parsed.get("issues", [])
                strengths = parsed.get("strengths", [])
                
                if issues or strengths:
                    critique_summary = "\n\n---\n### Planner-Critic Audit Summary\n"
                    if strengths:
                        critique_summary += "**Strengths Identified:**\n" + "\n".join(f"- {s}" for s in strengths) + "\n"
                    if issues:
                        critique_summary += "**Addressed Revision Issues:**\n" + "\n".join(f"- {i}" for i in issues) + "\n"
                    critique_summary += "\n*Verdict: Plan revised and approved by Critic Agent.*"
            except Exception as e:
                logger.error(f"Failed to assemble critique summary: {e}")
                
        final_answer = plan + critique_summary
    elif intent == "documentation":
        final_answer = state["docs_output"]
        
    # Extract citations mapping from the final answer bracketed digits [n] back to retrieved chunks
    citations_out = []
    seen_indices = set()
    matches = re.findall(r"\[([1-6])\]", final_answer)
    
    # retrieved chunks are in state["retrieved"]
    retrieved = state["retrieved"]
    for m in matches:
        idx = int(m) - 1
        if idx < len(retrieved) and idx not in seen_indices:
            seen_indices.add(idx)
            c = retrieved[idx]
            citations_out.append({
                "source_type": c["source_type"],
                "document_id": c.get("document_id"),
                "filename": c.get("filename"),
                "page": c.get("page"),
                "snippet": c["text"][:200]
            })
            
    # Save final structured tasks if intent is planning
    if intent == "planning" and state.get("tasks"):
        now = datetime.utcnow()
        ws_oid = ObjectId(state["workspace_id"])
        run_oid = ObjectId(state["run_id"])
        
        task_docs = []
        for task in state["tasks"]:
            task_docs.append({
                "workspace_id": ws_oid,
                "title": task.get("title", "Plan Task"),
                "description": task.get("description", ""),
                "status": "todo",
                "priority": task.get("priority", "medium").lower() if task.get("priority") in ("high", "medium", "low") else "medium",
                "assignee_id": None,
                "assignee_name": None,
                "due_date": None,
                "created_by": "agent:planner",
                "run_id": run_oid,
                "created_at": now,
                "updated_at": now
            })
            
        if task_docs:
            await db.tasks_col.insert_many(task_docs)
            logger.info(f"Successfully inserted {len(task_docs)} Planner Agent tasks into database.")
            
    # Save agent response as message inside the channel
    ch_oid = ObjectId(state["channel_id"])
    ws_oid = ObjectId(state["workspace_id"])
    run_oid = ObjectId(state["run_id"])
    user_oid = ObjectId(state["user_id"])
    
    now = datetime.utcnow()
    agent_msg_doc = {
        "workspace_id": ws_oid,
        "channel_id": ch_oid,
        "sender_type": "agent",
        "sender_id": "copilot",
        "sender_name": "Project Copilot",
        "content": final_answer,
        "citations": citations_out,
        "run_id": run_oid,
        "mentioned_agents": [],
        "indexed": True, # Copilot messages are indexed via run answers, avoid double indexing
        "created_at": now
    }
    
    await db.messages_col.insert_one(agent_msg_doc)
    
    # Broadcast agent message to WebSocket
    ws_broadcast = {
        "type": "agent_message",
        "message": {
            "id": str(agent_msg_doc["_id"]),
            "workspace_id": state["workspace_id"],
            "channel_id": state["channel_id"],
            "sender_type": "agent",
            "sender_id": "copilot",
            "sender_name": "Project Copilot",
            "content": final_answer,
            "citations": citations_out,
            "run_id": state["run_id"],
            "mentioned_agents": [],
            "indexed": True,
            "created_at": now.isoformat()
        }
    }
    await manager.broadcast_to_workspace(state["workspace_id"], ws_broadcast)
    
    # Update final status of run doc in DB
    trace_entry = _build_trace_entry(
        step_num=len(state["trace"]) + 1,
        agent="finalize",
        input_summary="Consolidating outputs",
        output_summary="Final output saved"
    )
    state["trace"].append(trace_entry)
    state["final_answer"] = final_answer
    state["citations"] = citations_out
    
    await _update_run_in_db(state, "finalize", status="done", final_answer=final_answer, citations=citations_out)
    logger.info(f"Copilot run {state['run_id']} finished successfully.")
    return state
