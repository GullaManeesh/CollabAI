from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from bson import ObjectId
from bson.errors import InvalidId
import logging

from backend.auth import decode_access_token
import backend.database as db
from backend.ws.manager import manager
from backend.ws.handlers import handle_ws_message

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str, token: str = Query(...)):
    # 1. Validate JWT Token
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        logger.warning(f"WS connection rejected: invalid token")
        # 4401 indicates Unauthorized in WebSocket context
        await websocket.close(code=4401)
        return
        
    user_id = payload["sub"]
    
    # 2. Check IDs are valid ObjectIds
    try:
        u_oid = ObjectId(user_id)
        ws_oid = ObjectId(workspace_id)
    except InvalidId:
        logger.warning(f"WS connection rejected: invalid ID format")
        await websocket.close(code=4401)
        return

    # 3. Retrieve user profile
    user = await db.users_col.find_one({"_id": u_oid})
    if not user:
        logger.warning(f"WS connection rejected: user {user_id} not found")
        await websocket.close(code=4401)
        return

    # 4. Validate workspace membership
    workspace = await db.workspaces_col.find_one({
        "_id": ws_oid,
        "members.user_id": u_oid
    })
    if not workspace:
        logger.warning(f"WS connection rejected: user {user['name']} not a member of {workspace_id}")
        # 4403 indicates Forbidden in WebSocket context
        await websocket.close(code=4403)
        return
        
    # 5. Accept socket connection and handle messages
    await manager.connect(websocket, workspace_id, user_id, user["name"])
    
    try:
        while True:
            # block waiting for client JSON payload
            data = await websocket.receive_json()
            await handle_ws_message(websocket, workspace_id, user_id, user["name"], data)
    except WebSocketDisconnect:
        await manager.disconnect(websocket, workspace_id)
    except Exception as e:
        logger.error(f"WS exception for user {user['name']} in workspace {workspace_id}: {e}")
        await manager.disconnect(websocket, workspace_id)
