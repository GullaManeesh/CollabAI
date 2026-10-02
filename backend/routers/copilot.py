from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

from backend.models.copilot import CopilotTurnRequest, CopilotTurnResponse, CopilotRunResponse, TraceStepResponse
from backend.models.messages import MessageResponse, Citation
from backend.dependencies import get_current_user, require_member
import backend.database as db
from backend.ws.manager import manager
from backend.services.copilot_service import run_copilot_turn_background

router = APIRouter(prefix="/copilot", tags=["copilot"])

@router.post("/{workspace_id}/turn", response_model=CopilotTurnResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_copilot_turn(
    workspace_id: str,
    req: CopilotTurnRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    workspace: dict = Depends(require_member)
):
    ws_oid = ObjectId(workspace_id)
    u_oid = ObjectId(current_user["id"])
    query = req.content.strip()
    
    # 1. Fetch copilot channel for workspace
    copilot_channel = await db.channels_col.find_one({
        "workspace_id": ws_oid,
        "type": "copilot"
    })
    
    if not copilot_channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copilot channel not found in this workspace"
        )
        
    ch_oid = copilot_channel["_id"]
    now = datetime.utcnow()
    
    # 2. Persist user's message in copilot channel
    msg_doc = {
        "workspace_id": ws_oid,
        "channel_id": ch_oid,
        "sender_type": "user",
        "sender_id": u_oid,
        "sender_name": current_user["name"],
        "content": query,
        "citations": [],
        "run_id": None,
        "mentioned_agents": [],
        "indexed": False,
        "created_at": now
    }
    
    res_msg = await db.messages_col.insert_one(msg_doc)
    msg_id = res_msg.inserted_id
    
    # Broadcast human message to WS
    human_msg_formatted = MessageResponse(
        id=str(msg_id),
        workspace_id=workspace_id,
        channel_id=str(ch_oid),
        sender_type="user",
        sender_id=current_user["id"],
        sender_name=current_user["name"],
        content=query,
        citations=[],
        run_id=None,
        mentioned_agents=[],
        indexed=False,
        created_at=now
    )
    await manager.broadcast_to_workspace(workspace_id, {
        "type": "message",
        "message": human_msg_formatted.dict()
    })
    
    # 3. Create agent_run doc in DB
    run_doc = {
        "workspace_id": ws_oid,
        "channel_id": ch_oid,
        "user_id": u_oid,
        "query": query,
        "intent": None,
        "status": "running",
        "final_answer": None,
        "citations": [],
        "trace": [],
        "total_tokens": 0,
        "total_latency_ms": 0,
        "revision_count": 0,
        "error": None,
        "created_at": now
    }
    
    res_run = await db.agent_runs_col.insert_one(run_doc)
    run_id = res_run.inserted_id
    
    # 4. Trigger LangGraph in background task
    background_tasks.add_task(
        run_copilot_turn_background,
        workspace_id=workspace_id,
        channel_id=str(ch_oid),
        user_id=current_user["id"],
        run_id=str(run_id),
        query=query
    )
    
    return CopilotTurnResponse(
        run_id=str(run_id),
        message_id=str(msg_id)
    )

@router.get("/runs/{run_id}", response_model=CopilotRunResponse)
async def get_copilot_run_status(
    run_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        run_oid = ObjectId(run_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid run ID format"
        )
        
    run = await db.agent_runs_col.find_one({"_id": run_oid})
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copilot run trace not found"
        )
        
    # Verify user membership in workspace
    ws_oid = run["workspace_id"]
    u_oid = ObjectId(current_user["id"])
    
    workspace = await db.workspaces_col.find_one({
        "_id": ws_oid,
        "members.user_id": u_oid
    })
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of the workspace for this run"
        )
        
    # Format trace steps
    formatted_trace = []
    for step in run.get("trace", []):
        formatted_trace.append(
            TraceStepResponse(
                step=step["step"],
                agent=step["agent"],
                input_summary=step.get("input_summary"),
                output_summary=step.get("output_summary"),
                provider=step.get("provider"),
                model=step.get("model"),
                tokens_in=step.get("tokens_in", 0),
                tokens_out=step.get("tokens_out", 0),
                latency_ms=step.get("latency_ms", 0),
                started_at=step.get("started_at", datetime.utcnow())
            )
        )
        
    return CopilotRunResponse(
        id=str(run["_id"]),
        workspace_id=str(run["workspace_id"]),
        channel_id=str(run["channel_id"]),
        user_id=str(run["user_id"]),
        query=run["query"],
        intent=run.get("intent"),
        status=run["status"],
        final_answer=run.get("final_answer"),
        citations=[Citation(**c) for c in run.get("citations", [])],
        trace=formatted_trace,
        total_tokens=run.get("total_tokens", 0),
        total_latency_ms=run.get("total_latency_ms", 0),
        revision_count=run.get("revision_count", 0),
        error=run.get("error"),
        created_at=run["created_at"],
        completed_at=run.get("completed_at")
    )

@router.get("/{workspace_id}/history", response_model=list[MessageResponse])
async def get_copilot_channel_history(
    workspace_id: str,
    current_user: dict = Depends(get_current_user),
    workspace: dict = Depends(require_member)
):
    ws_oid = ObjectId(workspace_id)
    
    # 1. Fetch copilot channel
    copilot_channel = await db.channels_col.find_one({
        "workspace_id": ws_oid,
        "type": "copilot"
    })
    
    if not copilot_channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copilot channel not found in workspace"
        )
        
    # 2. Fetch history messages (newest first, limit 50, then return oldest first)
    cursor = db.messages_col.find({"channel_id": copilot_channel["_id"]}).sort([("created_at", -1)]).limit(50)
    messages = await cursor.to_list(length=50)
    
    formatted_messages = []
    for msg in reversed(messages):
        formatted_messages.append(
            MessageResponse(
                id=str(msg["_id"]),
                workspace_id=str(msg["workspace_id"]),
                channel_id=str(msg["channel_id"]),
                sender_type=msg["sender_type"],
                sender_id=str(msg["sender_id"]) if isinstance(msg["sender_id"], ObjectId) else msg["sender_id"],
                sender_name=msg["sender_name"],
                content=msg["content"],
                citations=[Citation(**c) for c in msg.get("citations", [])],
                run_id=str(msg["run_id"]) if msg.get("run_id") else None,
                mentioned_agents=msg.get("mentioned_agents", []),
                indexed=msg.get("indexed", False),
                created_at=msg["created_at"]
            )
        )
        
    return formatted_messages
