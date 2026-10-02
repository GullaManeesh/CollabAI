import re
import logging
from datetime import datetime
from bson import ObjectId

import backend.database as db
from backend.ws.manager import manager
from backend.services.retrieval_service import retrieve, format_context
from backend.llm.client import complete, AllProvidersExhausted
from backend.models.messages import MessageResponse, Citation

logger = logging.getLogger(__name__)

RESEARCH_PROMPT = """You are the Research Agent in the workspace "{workspace_name}". You answer using ONLY the workspace context provided below. This context is the team's own material — their uploaded documents, their chat history, their previous plans.

Rules:
1. Cite every factual claim with the bracketed number of its source, like [2].
2. If the context does not contain the answer, say exactly what is missing and what the team would need to upload or discuss. Do not fill the gap from general knowledge.
3. Distinguish what the team has decided from what they have only discussed.
4. Be concise. Keep your answer under 250 words.

WORKSPACE CONTEXT:
{context}"""

PLANNER_LIGHT_PROMPT = """You are the Planner Agent in the workspace "{workspace_name}". You turn research findings into an executable plan for this specific team.
You will be given: the user's request and the workspace context (findings, discussions, decisions).

Produce:
1. A short paragraph stating the approach and the single biggest risk in it.
2. A milestone breakdown with realistic sequencing and stated dependencies.

Ground the plan in what this team actually has — their stack, their deadlines, their progress as shown in the context.
Cap your answer at roughly 250 words. Do not emit any task lists or JSON blocks. Cite sources with bracketed numbers like [1], [3].

WORKSPACE CONTEXT:
{context}"""

DOCS_PROMPT = """You are the Documentation Agent in the workspace "{workspace_name}". You write documents from the team's own workspace material.

Rules:
1. Use the workspace context as the source of truth — real names, real stack, real decisions. Never invent a feature, dependency, or endpoint.
2. Match the format the user asked for.
3. Where the context is insufficient, insert `> TODO: <what is needed>` rather than guessing.
4. Keep your answer concise, under 250 words. Cite sources with bracketed numbers like [1], [2].

WORKSPACE CONTEXT:
{context}"""

AGENT_PROMPTS = {
    "research": RESEARCH_PROMPT,
    "planner": PLANNER_LIGHT_PROMPT,
    "docs": DOCS_PROMPT
}

AGENT_NAMES = {
    "research": "Research Agent",
    "planner": "Planner Agent",
    "docs": "Documentation Agent"
}

async def handle_chat_mentions(workspace_id: str, channel_id: str, human_message: dict):
    ws_oid = ObjectId(workspace_id)
    ch_oid = ObjectId(channel_id)
    
    mentions = human_message.get("mentioned_agents", [])
    if not mentions:
        return
        
    # Fetch workspace metadata
    workspace = await db.workspaces_col.find_one({"_id": ws_oid})
    ws_name = workspace["name"] if workspace else "Workspace"
    
    # Process each mentioned agent sequentially
    for agent_key in mentions:
        if agent_key not in AGENT_PROMPTS:
            continue
            
        # 1. Broadcast typing indicator
        logger.info(f"Agent {agent_key} typing in workspace {workspace_id}")
        typing_indicator = {
            "type": "agent_typing",
            "channel_id": channel_id,
            "agent": agent_key
        }
        await manager.broadcast_to_workspace(workspace_id, typing_indicator)
        
        # 2. Extract clean query (remove mention chips like @research)
        clean_query = re.sub(r"@\w+", "", human_message["content"]).strip()
        
        try:
            # 3. Retrieve workspace context (k=6)
            chunks = await retrieve(workspace_id=ws_oid, query=clean_query, k=6)
            context_str = format_context(chunks)
            
            # 4. Generate response using LLM Client
            system_prompt = AGENT_PROMPTS[agent_key].format(
                workspace_name=ws_name,
                context=context_str
            )
            
            messages_payload = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": clean_query}
            ]
            
            llm_res = await complete(
                messages=messages_payload,
                tier="default",
                temperature=0.3
            )
            
            # 5. Build citations list
            citations_out = []
            seen_indices = set()
            # Find bracketed citation tags like [1], [2], etc.
            matches = re.findall(r"\[([1-6])\]", llm_res.text)
            for m in matches:
                idx = int(m) - 1
                if idx < len(chunks) and idx not in seen_indices:
                    seen_indices.add(idx)
                    c = chunks[idx]
                    citations_out.append({
                        "source_type": c.source_type,
                        "document_id": c.document_id,
                        "filename": c.filename,
                        "page": c.page,
                        "snippet": c.text[:200]
                    })
                    
            # 6. Save agent response message
            now = datetime.utcnow()
            agent_msg_doc = {
                "workspace_id": ws_oid,
                "channel_id": ch_oid,
                "sender_type": "agent",
                "sender_id": agent_key,
                "sender_name": AGENT_NAMES[agent_key],
                "content": llm_res.text,
                "citations": citations_out,
                "run_id": None,
                "mentioned_agents": [],
                "indexed": True, # Prevents indexing agent messages in background batches
                "created_at": now
            }
            
            res = await db.messages_col.insert_one(agent_msg_doc)
            msg_id = res.inserted_id
            
            # Construct response object
            response_obj = MessageResponse(
                id=str(msg_id),
                workspace_id=workspace_id,
                channel_id=channel_id,
                sender_type="agent",
                sender_id=agent_key,
                sender_name=AGENT_NAMES[agent_key],
                content=llm_res.text,
                citations=[Citation(**c) for c in citations_out],
                run_id=None,
                mentioned_agents=[],
                indexed=True,
                created_at=now
            )
            
            # 7. Broadcast agent response to WebSocket
            ws_broadcast = {
                "type": "agent_message",
                "message": response_obj.dict()
            }
            await manager.broadcast_to_workspace(workspace_id, ws_broadcast)
            logger.info(f"Agent {agent_key} successfully replied in channel {channel_id}")
            
        except AllProvidersExhausted as e:
            logger.error(f"Failed to call LLM for agent {agent_key}: {e}")
            error_msg = {
                "type": "error",
                "channel_id": channel_id,
                "detail": "Both AI providers are rate-limited. Try again in a minute."
            }
            await manager.broadcast_to_workspace(workspace_id, error_msg)
        except Exception as e:
            logger.error(f"Error handling agent mention: {e}")
            error_msg = {
                "type": "error",
                "channel_id": channel_id,
                "detail": f"Agent error occurred: {str(e)}"
            }
            await manager.broadcast_to_workspace(workspace_id, error_msg)
