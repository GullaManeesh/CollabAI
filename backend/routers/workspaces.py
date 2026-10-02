from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import List

from backend.models.workspaces import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceDetailResponse,
    WorkspaceListResponse,
    AddMemberRequest,
    WorkspaceMembersListResponse,
    WorkspaceMemberResponse,
    WorkspaceChannels,
    WorkspaceStats
)
from backend.dependencies import get_current_user, require_member, require_owner
import backend.database as db

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    ws_in: WorkspaceCreate,
    current_user: dict = Depends(get_current_user)
):
    now = datetime.utcnow()
    user_obj_id = ObjectId(current_user["id"])
    
    # 1. Create Workspace doc
    ws_doc = {
        "name": ws_in.name.strip(),
        "description": ws_in.description.strip() if ws_in.description else "",
        "owner_id": user_obj_id,
        "members": [
            {
                "user_id": user_obj_id,
                "name": current_user["name"],
                "role": "owner",
                "joined_at": now
            }
        ],
        "created_at": now
    }
    
    ws_result = await db.workspaces_col.insert_one(ws_doc)
    ws_id = ws_result.inserted_id
    
    # 2. Auto-create the two channels: general (team_chat) and Project Copilot (copilot)
    chat_channel = {
        "workspace_id": ws_id,
        "type": "team_chat",
        "name": "general",
        "created_at": now
    }
    
    copilot_channel = {
        "workspace_id": ws_id,
        "type": "copilot",
        "name": "Project Copilot",
        "created_at": now
    }
    
    chat_res = await db.channels_col.insert_one(chat_channel)
    copilot_res = await db.channels_col.insert_one(copilot_channel)
    
    return WorkspaceResponse(
        id=str(ws_id),
        name=ws_doc["name"],
        description=ws_doc["description"],
        owner_id=str(user_obj_id),
        members=[
            WorkspaceMemberResponse(
                user_id=str(user_obj_id),
                name=current_user["name"],
                role="owner",
                joined_at=now,
                avatar_color=current_user.get("avatar_color")
            )
        ],
        channels=WorkspaceChannels(
            team_chat=str(chat_res.inserted_id),
            copilot=str(copilot_res.inserted_id)
        ),
        created_at=now
    )

@router.get("", response_model=List[WorkspaceListResponse])
async def list_workspaces(current_user: dict = Depends(get_current_user)):
    user_obj_id = ObjectId(current_user["id"])
    
    cursor = db.workspaces_col.find({"members.user_id": user_obj_id})
    workspaces = await cursor.to_list(length=100)
    
    result = []
    for ws in workspaces:
        ws_id = ws["_id"]
        
        # Count members
        member_count = len(ws.get("members", []))
        
        # Find user's role
        role = "member"
        for m in ws.get("members", []):
            if m["user_id"] == user_obj_id:
                role = m.get("role", "member")
                break
                
        # Find last activity (latest message in the workspace)
        # default to workspace created_at
        last_activity = ws.get("created_at", datetime.utcnow())
        latest_msg = await db.messages_col.find_one(
            {"workspace_id": ws_id},
            sort=[("created_at", -1)]
        )
        if latest_msg:
            last_activity = latest_msg["created_at"]
            
        result.append(
            WorkspaceListResponse(
                id=str(ws_id),
                name=ws["name"],
                member_count=member_count,
                role=role,
                last_activity_at=last_activity
            )
        )
        
    return result

@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
async def get_workspace_detail(
    workspace_id: str,
    workspace: dict = Depends(require_member)
):
    ws_id = ObjectId(workspace["id"])
    
    # 1. Fetch channel IDs
    chat_channel = await db.channels_col.find_one({"workspace_id": ws_id, "type": "team_chat"})
    copilot_channel = await db.channels_col.find_one({"workspace_id": ws_id, "type": "copilot"})
    
    # If they somehow don't exist (e.g. legacy data), auto create them
    now = datetime.utcnow()
    if not chat_channel:
        chat_doc = {"workspace_id": ws_id, "type": "team_chat", "name": "general", "created_at": now}
        res = await db.channels_col.insert_one(chat_doc)
        chat_channel = {"_id": res.inserted_id}
    if not copilot_channel:
        cop_doc = {"workspace_id": ws_id, "type": "copilot", "name": "Project Copilot", "created_at": now}
        res = await db.channels_col.insert_one(cop_doc)
        copilot_channel = {"_id": res.inserted_id}
        
    channels = WorkspaceChannels(
        team_chat=str(chat_channel["_id"]),
        copilot=str(copilot_channel["_id"])
    )
    
    # 2. Enrich members with avatar colors from users collection
    enriched_members = []
    for member in workspace.get("members", []):
        m_uid = member["user_id"]
        # Find user profile
        user_profile = await db.users_col.find_one({"_id": m_uid})
        avatar_color = user_profile.get("avatar_color") if user_profile else None
        
        enriched_members.append(
            WorkspaceMemberResponse(
                user_id=str(m_uid),
                name=member["name"],
                role=member["role"],
                joined_at=member["joined_at"],
                avatar_color=avatar_color
            )
        )
        
    # 3. Calculate statistics
    msg_count = await db.messages_col.count_documents({"workspace_id": ws_id})
    doc_count = await db.documents_col.count_documents({"workspace_id": ws_id})
    task_count = await db.tasks_col.count_documents({"workspace_id": ws_id})
    chunk_count = await db.chunks_col.count_documents({"workspace_id": ws_id})
    
    stats = WorkspaceStats(
        message_count=msg_count,
        document_count=doc_count,
        task_count=task_count,
        indexed_chunks=chunk_count
    )
    
    return WorkspaceDetailResponse(
        id=workspace["id"],
        name=workspace["name"],
        description=workspace.get("description", ""),
        owner_id=str(workspace["owner_id"]),
        members=enriched_members,
        channels=channels,
        stats=stats,
        created_at=workspace["created_at"]
    )

@router.post("/{workspace_id}/members", response_model=WorkspaceMembersListResponse)
async def add_workspace_member(
    workspace_id: str,
    req: AddMemberRequest,
    workspace: dict = Depends(require_owner)
):
    ws_id = ObjectId(workspace["id"])
    email_clean = req.email.lower().strip()
    
    # Find user with that email
    new_user = await db.users_col.find_one({"email": email_clean})
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )
        
    new_user_id = new_user["_id"]
    
    # Check if already a member
    is_already_member = any(m["user_id"] == new_user_id for m in workspace.get("members", []))
    
    if not is_already_member:
        # Append member
        member_entry = {
            "user_id": new_user_id,
            "name": new_user["name"],
            "role": "member",
            "joined_at": datetime.utcnow()
        }
        await db.workspaces_col.update_one(
            {"_id": ws_id},
            {"$push": {"members": member_entry}}
        )
        # Fetch updated workspace members list
        workspace = await db.workspaces_col.find_one({"_id": ws_id})
        
    # Enrich and return members
    enriched_members = []
    for member in workspace.get("members", []):
        m_uid = member["user_id"]
        user_profile = await db.users_col.find_one({"_id": m_uid})
        avatar_color = user_profile.get("avatar_color") if user_profile else None
        
        enriched_members.append(
            WorkspaceMemberResponse(
                user_id=str(m_uid),
                name=member["name"],
                role=member["role"],
                joined_at=member["joined_at"],
                avatar_color=avatar_color
            )
        )
        
    return WorkspaceMembersListResponse(members=enriched_members)

@router.delete("/{workspace_id}/members/{user_id}", response_model=WorkspaceMembersListResponse)
async def remove_workspace_member(
    workspace_id: str,
    user_id: str,
    workspace: dict = Depends(require_owner)
):
    ws_id = ObjectId(workspace["id"])
    try:
        user_obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
        
    # Cannot remove the owner
    if user_obj_id == workspace["owner_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the owner of the workspace"
        )
        
    # Pull member
    await db.workspaces_col.update_one(
        {"_id": ws_id},
        {"$pull": {"members": {"user_id": user_obj_id}}}
    )
    
    # Fetch updated workspace
    updated_ws = await db.workspaces_col.find_one({"_id": ws_id})
    
    # Enrich and return
    enriched_members = []
    for member in updated_ws.get("members", []):
        m_uid = member["user_id"]
        user_profile = await db.users_col.find_one({"_id": m_uid})
        avatar_color = user_profile.get("avatar_color") if user_profile else None
        
        enriched_members.append(
            WorkspaceMemberResponse(
                user_id=str(m_uid),
                name=member["name"],
                role=member["role"],
                joined_at=member["joined_at"],
                avatar_color=avatar_color
            )
        )
        
    return WorkspaceMembersListResponse(members=enriched_members)
