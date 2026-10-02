from bson import ObjectId
from datetime import datetime
import logging
import asyncio

import backend.database as db
from backend.agents.graph import app_graph
from backend.ws.manager import manager

logger = logging.getLogger(__name__)

async def run_copilot_turn_background(workspace_id: str, channel_id: str, user_id: str, run_id: str, query: str):
    logger.info(f"Starting background Copilot turn for run {run_id} in channel {channel_id}")
    
    ws_oid = ObjectId(workspace_id)
    ch_oid = ObjectId(channel_id)
    run_oid = ObjectId(run_id)
    u_oid = ObjectId(user_id)
    
    try:
        # 1. Fetch last 10 messages for history
        cursor = db.messages_col.find({"channel_id": ch_oid}).sort([("created_at", -1)]).limit(10)
        history_msgs = await cursor.to_list(length=10)
        
        # Format history as list of dicts for CopilotState
        history_turns = []
        for msg in reversed(history_msgs):
            history_turns.append({
                "sender_type": msg["sender_type"],
                "sender_name": msg["sender_name"],
                "content": msg["content"]
            })
            
        # 2. Form initial state
        initial_state = {
            "workspace_id": workspace_id,
            "run_id": run_id,
            "channel_id": channel_id,
            "user_id": user_id,
            "query": query,
            "history": history_turns,
            "intent": "factual",
            "retrieved": [],
            "research_output": "",
            "plan_output": "",
            "critique": "",
            "needs_revision": False,
            "revision_count": 0,
            "docs_output": "",
            "final_answer": "",
            "citations": [],
            "tasks": [],
            "trace": [],
            "current_step": "router",
            "status": "running"
        }
        
        # 3. Invoke LangGraph Graph
        # We set a timeout of 120s as per 05-AGENTS-AND-RAG.md failure handling
        # Since it is async, we can run it with asyncio.wait_for
        await asyncio.wait_for(
            app_graph.ainvoke(initial_state),
            timeout=120.0
        )
        
    except asyncio.TimeoutError:
        logger.error(f"Copilot run {run_id} timed out after 120 seconds.")
        await db.agent_runs_col.update_one(
            {"_id": run_oid},
            {
                "$set": {
                    "status": "failed",
                    "error": "Copilot run timed out after 120 seconds.",
                    "completed_at": datetime.utcnow()
                }
            }
        )
        # Broadcast error to WebSocket
        error_msg = {
            "type": "error",
            "channel_id": channel_id,
            "detail": "Copilot run timed out. Please try again."
        }
        await manager.broadcast_to_workspace(workspace_id, error_msg)
        
    except Exception as e:
        logger.error(f"Error executing copilot turn for run {run_id}: {e}", exc_info=True)
        await db.agent_runs_col.update_one(
            {"_id": run_oid},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.utcnow()
                }
            }
        )
        # Broadcast error to WebSocket
        error_msg = {
            "type": "error",
            "channel_id": channel_id,
            "detail": f"Copilot execution failed: {str(e)}"
        }
        await manager.broadcast_to_workspace(workspace_id, error_msg)
