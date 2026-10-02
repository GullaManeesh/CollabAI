from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import Optional, List

from backend.models.messages import MessageCreate, MessageResponse, MessagesListResponse, Citation
from backend.dependencies import get_current_user
import backend.database as db
from backend.ws.manager import manager

router = APIRouter(tags=["messages"])

async def get_channel_and_verify_membership(channel_id: str, current_user: dict):
    try:
        ch_oid = ObjectId(channel_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid channel ID format"
        )
        
    channel = await db.channels_col.find_one({"_id": ch_oid})
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
        
    ws_oid = channel["workspace_id"]
    u_oid = ObjectId(current_user["id"])
    
    # Check if user is member of workspace
    workspace = await db.workspaces_col.find_one({
        "_id": ws_oid,
        "members.user_id": u_oid
    })
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )
        
    return channel, workspace

@router.get("/channels/{channel_id}/messages", response_model=MessagesListResponse)
async def get_messages(
    channel_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    before: Optional[datetime] = Query(default=None),
    current_user: dict = Depends(get_current_user)
):
    channel, workspace = await get_channel_and_verify_membership(channel_id, current_user)
    ch_oid = channel["_id"]
    
    query = {"channel_id": ch_oid}
    if before:
        query["created_at"] = {"$lt": before}
        
    # Query limit + 1 to determine if there is a next page
    cursor = db.messages_col.find(query).sort([("created_at", -1)]).limit(limit + 1)
    messages = await cursor.to_list(length=limit + 1)
    
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]
        
    # Convert Mongo docs to Pydantic and reverse to return oldest-first
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
        
    return MessagesListResponse(messages=formatted_messages, has_more=has_more)

@router.post("/channels/{channel_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def post_message(
    channel_id: str,
    msg_in: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    channel, workspace = await get_channel_and_verify_membership(channel_id, current_user)
    ws_id = channel["workspace_id"]
    ch_oid = channel["_id"]
    u_oid = ObjectId(current_user["id"])
    now = datetime.utcnow()
    
    # Parse mentions
    content = msg_in.content
    import re
    mentions = re.findall(r"@(research|planner|docs)\b", content)
    
    msg_doc = {
        "workspace_id": ws_id,
        "channel_id": ch_oid,
        "sender_type": "user",
        "sender_id": u_oid,
        "sender_name": current_user["name"],
        "content": content,
        "citations": [],
        "run_id": None,
        "mentioned_agents": list(set(mentions)),
        "indexed": False,
        "created_at": now
    }
    
    res = await db.messages_col.insert_one(msg_doc)
    msg_id = res.inserted_id
    
    response_obj = MessageResponse(
        id=str(msg_id),
        workspace_id=str(ws_id),
        channel_id=str(ch_oid),
        sender_type="user",
        sender_id=str(u_oid),
        sender_name=current_user["name"],
        content=content,
        citations=[],
        run_id=None,
        mentioned_agents=list(set(mentions)),
        indexed=False,
        created_at=now
    )
    
    # Broadcast to WebSocket
    ws_msg = {
        "type": "message",
        "message": response_obj.dict()
    }
    # Wait for broadcast
    await manager.broadcast_to_workspace(str(ws_id), ws_msg)
    
    # Trigger background hooks (indexing, agent mentions)
    import asyncio
    from backend.ws.handlers import post_ws_message_hooks
    asyncio.create_task(post_ws_message_hooks(str(ws_id), channel_id, response_obj.dict()))
    
    return response_obj
