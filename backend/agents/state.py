from typing import TypedDict, List, Dict, Any, Optional

class CopilotState(TypedDict):
    workspace_id: str
    run_id: str
    channel_id: str
    user_id: str
    query: str
    history: List[Dict[str, Any]]
    intent: str                      # set by router
    retrieved: List[Dict[str, Any]]   # serialised RetrievedChunk
    research_output: str
    plan_output: str
    critique: str
    needs_revision: bool
    revision_count: int
    docs_output: str
    final_answer: str
    citations: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]
    trace: List[Dict[str, Any]]
    current_step: str
    status: str
