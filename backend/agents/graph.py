from langgraph.graph import StateGraph, END
import logging

from backend.agents.state import CopilotState
from backend.agents.nodes import (
    router_node,
    research_node,
    planner_node,
    critic_node,
    docs_node,
    finalize_node
)

logger = logging.getLogger(__name__)

def after_research(state: CopilotState) -> str:
    intent = state.get("intent", "factual")
    if intent in ("planning", "documentation", "factual"):
        return intent
    return "factual"

def after_critic(state: CopilotState) -> str:
    needs_rev = state.get("needs_revision", False)
    rev_count = state.get("revision_count", 0)
    
    # We allow at most 1 revision total (revision_count < 1)
    if needs_rev and rev_count < 1:
        logger.info("Critic requested revision, and revision limit not reached. Routing to planner for revision.")
        return "revise"
        
    logger.info("Proceeding to finalize (either approved or revision limit reached).")
    return "done"

# Build Graph
workflow = StateGraph(CopilotState)

workflow.add_node("router", router_node)
workflow.add_node("research", research_node)
workflow.add_node("planner", planner_node)
workflow.add_node("critic", critic_node)
workflow.add_node("docs", docs_node)
workflow.add_node("finalize", finalize_node)

workflow.set_entry_point("router")
workflow.add_edge("router", "research")

workflow.add_conditional_edges(
    "research",
    after_research,
    {
        "planning": "planner",
        "documentation": "docs",
        "factual": "finalize"
    }
)

workflow.add_edge("planner", "critic")

workflow.add_conditional_edges(
    "critic",
    after_critic,
    {
        "revise": "planner",
        "done": "finalize"
    }
)

workflow.add_edge("docs", "finalize")
workflow.add_edge("finalize", END)

# Compile graph
app_graph = workflow.compile()
