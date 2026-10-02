from fastapi import WebSocket
from typing import Dict, Set, List
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Maps workspace_id (str) -> set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Maps WebSocket -> (user_id, user_name)
        self.socket_users: Dict[WebSocket, tuple] = {}

    async def connect(self, websocket: WebSocket, workspace_id: str, user_id: str, user_name: str):
        await websocket.accept()
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = set()
        self.active_connections[workspace_id].add(websocket)
        self.socket_users[websocket] = (user_id, user_name)
        
        logger.info(f"User {user_name} ({user_id}) connected to workspace {workspace_id} via WS")
        # Broadcast presence update
        await self.broadcast_presence(workspace_id)

    async def disconnect(self, websocket: WebSocket, workspace_id: str):
        if workspace_id in self.active_connections:
            self.active_connections[workspace_id].discard(websocket)
            if not self.active_connections[workspace_id]:
                del self.active_connections[workspace_id]
                
        if websocket in self.socket_users:
            user_id, user_name = self.socket_users[websocket]
            del self.socket_users[websocket]
            logger.info(f"User {user_name} ({user_id}) disconnected from workspace {workspace_id}")
            
        # Broadcast updated presence
        await self.broadcast_presence(workspace_id)

    async def broadcast_to_workspace(self, workspace_id: str, message: dict):
        if workspace_id not in self.active_connections:
            return
            
        disconnected_sockets = set()
        connections = self.active_connections[workspace_id].copy()
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WS message to a socket in workspace {workspace_id}: {e}")
                disconnected_sockets.add(connection)
                
        for socket in disconnected_sockets:
            await self.disconnect(socket, workspace_id)

    async def broadcast_presence(self, workspace_id: str):
        if workspace_id not in self.active_connections:
            return
            
        # Get unique user IDs of online users
        online_users = set()
        for socket in self.active_connections[workspace_id]:
            if socket in self.socket_users:
                online_users.add(self.socket_users[socket][0])
                
        presence_msg = {
            "type": "presence",
            "online_user_ids": list(online_users)
        }
        await self.broadcast_to_workspace(workspace_id, presence_msg)

manager = ConnectionManager()
