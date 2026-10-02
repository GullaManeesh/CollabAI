from fastapi import APIRouter

router = APIRouter(prefix="/channels", tags=["channels"])
# Currently, channels are managed as part of Workspace detail and Message routes.
