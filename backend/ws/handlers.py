from fastapi import WebSocket
from bson import ObjectId
from datetime import datetime
import re
import logging
import asyncio

import backend.database as db
from backend.ws.manager import manager
from backend.models.messages import MessageResponse, Citation

logger = logging.getLogger(__name__)

async def handle_ws_message(websocket: WebSocket, workspace_id: str, user_id: str, user_name: str, data: dict):
    msg_type = data.get("type")
    channel_id = data.get("channel_id")
    
    if not channel_id:
        return
        
    try:
        ch_oid = ObjectId(channel_id)
        ws_oid = ObjectId(workspace_id)
        u_oid = ObjectId(user_id)
    except Exception as e:
        logger.error(f"Invalid IDs in WS message: {e}")
        await websocket.send_json({"type": "error", "detail": "Invalid ID format"})
        return

    if msg_type == "message":
        content = data.get("content", "").strip()
        if not content:
            return
            
        # Parse mentions
        mentions = re.findall(r"@(research|planner|docs)\b", content)
        
        now = datetime.utcnow()
        msg_doc = {
            "workspace_id": ws_oid,
            "channel_id": ch_oid,
            "sender_type": "user",
            "sender_id": u_oid,
            "sender_name": user_name,
            "content": content,
            "citations": [],
            "run_id": None,
            "mentioned_agents": list(set(mentions)),
            "indexed": False,
            "created_at": now
        }
        
        # Save to database
        res = await db.messages_col.insert_one(msg_doc)
        msg_id = res.inserted_id
        
        response_obj = MessageResponse(
            id=str(msg_id),
            workspace_id=workspace_id,
            channel_id=channel_id,
            sender_type="user",
            sender_id=user_id,
            sender_name=user_name,
            content=content,
            citations=[],
            run_id=None,
            mentioned_agents=list(set(mentions)),
            indexed=False,
            created_at=now
        )
        
        # Broadcast user message
        ws_broadcast = {
            "type": "message",
            "message": response_obj.dict()
        }
        await manager.broadcast_to_workspace(workspace_id, ws_broadcast)
        
        # Hooks for subsequent phases:
        # Phase 5: check unindexed count and trigger message indexing in background
        # Phase 6: check agent mentions and trigger mention_service
        # We will import and call these dynamically or implement the handler check.
        asyncio.create_task(post_ws_message_hooks(workspace_id, channel_id, response_obj.dict()))
        
    elif msg_type == "typing":
        is_typing = data.get("is_typing", True)
        # Broadcast typing status to everyone else
        typing_broadcast = {
            "type": "typing",
            "channel_id": channel_id,
            "user_id": user_id,
            "user_name": user_name,
            "is_typing": is_typing
        }
        # To avoid sending typing indicator back to the sender,
        # we can broadcast it to all sockets in the workspace.
        # (It's fine if the sender gets it, the UI can filter it or ignore it).
        await manager.broadcast_to_workspace(workspace_id, typing_broadcast)

async def post_ws_message_hooks(workspace_id: str, channel_id: str, message: dict):
    # This will be enriched in Phase 5 and Phase 6.
    # Phase 5: Trigger message indexing check
    # Phase 6: Check for mentions and trigger agent complete
    
    # 1. Phase 5: Check if unindexed messages count >= 10
    try:
        from backend.services.ingest_service import check_and_index_messages_background
        asyncio.create_task(check_and_index_messages_background(workspace_id, channel_id))
    except ImportError:
        pass
        
    # 2. Phase 6: Check for mentions and respond
    try:
        from backend.services.mention_service import handle_chat_mentions
        if message.get("mentioned_agents"):
            asyncio.create_task(handle_chat_mentions(workspace_id, channel_id, message))
    except ImportError:
        pass
