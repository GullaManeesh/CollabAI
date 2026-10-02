from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import Optional, List

from backend.models.tasks import TaskCreate, TaskUpdate, TaskResponse
from backend.dependencies import get_current_user, require_member
import backend.database as db

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/{workspace_id}", response_model=List[TaskResponse])
async def list_tasks(
    workspace_id: str,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    workspace: dict = Depends(require_member)
):
    ws_oid = ObjectId(workspace_id)
    
    query = {"workspace_id": ws_oid}
    if status_filter:
        query["status"] = status_filter
        
    cursor = db.tasks_col.find(query).sort([("created_at", -1)])
    tasks = await cursor.to_list(length=200)
    
    result = []
    for task in tasks:
        result.append(
            TaskResponse(
                id=str(task["_id"]),
                workspace_id=workspace_id,
                title=task["title"],
                description=task.get("description", ""),
                status=task["status"],
                priority=task["priority"],
                assignee_id=str(task["assignee_id"]) if task.get("assignee_id") else None,
                assignee_name=task.get("assignee_name"),
                due_date=task.get("due_date"),
                created_by=task["created_by"],
                run_id=str(task["run_id"]) if task.get("run_id") else None,
                created_at=task["created_at"],
                updated_at=task["updated_at"]
            )
        )
    return result

@router.post("/{workspace_id}", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    workspace_id: str,
    task_in: TaskCreate,
    current_user: dict = Depends(get_current_user),
    workspace: dict = Depends(require_member)
):
    ws_oid = ObjectId(workspace_id)
    now = datetime.utcnow()
    
    task_doc = {
        "workspace_id": ws_oid,
        "title": task_in.title.strip(),
        "description": task_in.description.strip() if task_in.description else "",
        "status": "todo",
        "priority": task_in.priority.lower() if task_in.priority in ("high", "medium", "low") else "medium",
        "assignee_id": None,
        "assignee_name": None,
        "due_date": task_in.due_date,
        "created_by": f"user:{current_user['id']}",
        "run_id": None,
        "created_at": now,
        "updated_at": now
    }
    
    res = await db.tasks_col.insert_one(task_doc)
    task_id = res.inserted_id
    
    return TaskResponse(
        id=str(task_id),
        workspace_id=workspace_id,
        title=task_doc["title"],
        description=task_doc["description"],
        status=task_doc["status"],
        priority=task_doc["priority"],
        assignee_id=None,
        assignee_name=None,
        due_date=task_doc["due_date"],
        created_by=task_doc["created_by"],
        run_id=None,
        created_at=now,
        updated_at=now
    )

@router.patch("/{workspace_id}/{task_id}", response_model=TaskResponse)
async def update_task(
    workspace_id: str,
    task_id: str,
    task_in: TaskUpdate,
    workspace: dict = Depends(require_member)
):
    try:
        task_oid = ObjectId(task_id)
        ws_oid = ObjectId(workspace_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task or workspace ID"
        )
        
    # Check if task exists and belongs to workspace
    existing = await db.tasks_col.find_one({"_id": task_oid, "workspace_id": ws_oid})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found in this workspace"
        )
        
    # Build update doc
    update_data = {}
    
    if task_in.title is not None:
        update_data["title"] = task_in.title.strip()
    if task_in.description is not None:
        update_data["description"] = task_in.description.strip()
    if task_in.status is not None:
        if task_in.status not in ("todo", "in_progress", "done"):
            raise HTTPException(status_code=400, detail="Invalid status")
        update_data["status"] = task_in.status
    if task_in.priority is not None:
        if task_in.priority not in ("high", "medium", "low"):
            raise HTTPException(status_code=400, detail="Invalid priority")
        update_data["priority"] = task_in.priority
    if task_in.assignee_id is not None:
        if task_in.assignee_id == "":
            update_data["assignee_id"] = None
            update_data["assignee_name"] = None
        else:
            try:
                update_data["assignee_id"] = ObjectId(task_in.assignee_id)
            except InvalidId:
                raise HTTPException(status_code=400, detail="Invalid assignee_id format")
            
            # Look up assignee name
            user = await db.users_col.find_one({"_id": update_data["assignee_id"]})
            if user:
                update_data["assignee_name"] = user["name"]
    if task_in.due_date is not None:
        update_data["due_date"] = task_in.due_date
        
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await db.tasks_col.update_one({"_id": task_oid}, {"$set": update_data})
        
    # Fetch updated
    updated_task = await db.tasks_col.find_one({"_id": task_oid})
    
    return TaskResponse(
        id=str(updated_task["_id"]),
        workspace_id=workspace_id,
        title=updated_task["title"],
        description=updated_task.get("description", ""),
        status=updated_task["status"],
        priority=updated_task["priority"],
        assignee_id=str(updated_task["assignee_id"]) if updated_task.get("assignee_id") else None,
        assignee_name=updated_task.get("assignee_name"),
        due_date=updated_task.get("due_date"),
        created_by=updated_task["created_by"],
        run_id=str(updated_task["run_id"]) if updated_task.get("run_id") else None,
        created_at=updated_task["created_at"],
        updated_at=updated_task["updated_at"]
    )

@router.delete("/{workspace_id}/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    workspace_id: str,
    task_id: str,
    workspace: dict = Depends(require_member)
):
    try:
        task_oid = ObjectId(task_id)
        ws_oid = ObjectId(workspace_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid IDs"
        )
        
    res = await db.tasks_col.delete_one({"_id": task_oid, "workspace_id": ws_oid})
    if res.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found in this workspace"
        )
        
    return status.HTTP_204_NO_CONTENT
