from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from bson.errors import InvalidId

from backend.auth import decode_access_token
import backend.database as db

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload["sub"]
    try:
        user_obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user token payload",
        )
        
    user = await db.users_col.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Return user as dict with str id
    user["id"] = str(user["_id"])
    return user

async def require_member(workspace_id: str, current_user: dict = Depends(get_current_user)) -> dict:
    try:
        ws_obj_id = ObjectId(workspace_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workspace ID format",
        )
        
    workspace = await db.workspaces_col.find_one({"_id": ws_obj_id})
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
        
    # Check membership
    user_obj_id = ObjectId(current_user["id"])
    is_member = False
    user_role = None
    for member in workspace.get("members", []):
        if member["user_id"] == user_obj_id:
            is_member = True
            user_role = member.get("role")
            break
            
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace",
        )
        
    # Add convenience fields
    workspace["id"] = str(workspace["_id"])
    workspace["current_user_role"] = user_role
    return workspace

async def require_owner(workspace_id: str, current_user: dict = Depends(get_current_user)) -> dict:
    workspace = await require_member(workspace_id, current_user)
    if workspace["current_user_role"] != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners can perform this action",
        )
    return workspace
