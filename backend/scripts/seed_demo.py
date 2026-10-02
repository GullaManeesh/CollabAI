import asyncio
import os
import sys
from datetime import datetime, timedelta
import random

# Adjust python path to be able to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.auth import get_password_hash
from backend.routers.auth import get_avatar_color_for_email
from bson import ObjectId
import backend.database as db

async def seed_data():
    print("Connecting to database...")
    await db.init_db()
    
    # 1. Clear existing database for a clean start
    print("Clearing database collections...")
    await db.users_col.delete_many({})
    await db.workspaces_col.delete_many({})
    await db.channels_col.delete_many({})
    await db.messages_col.delete_many({})
    await db.documents_col.delete_many({})
    await db.tasks_col.delete_many({})
    await db.agent_runs_col.delete_many({})
    await db.chunks_col.delete_many({})
    
    # 2. Seed Users
    print("Seeding users...")
    password_hash = get_password_hash("password123")
    
    users = [
        {
            "name": "Gowtham",
            "email": "gowtham@example.com",
            "password_hash": password_hash,
            "avatar_color": get_avatar_color_for_email("gowtham@example.com"),
            "created_at": datetime.utcnow() - timedelta(days=15)
        },
        {
            "name": "Asha",
            "email": "asha@example.com",
            "password_hash": password_hash,
            "avatar_color": get_avatar_color_for_email("asha@example.com"),
            "created_at": datetime.utcnow() - timedelta(days=14)
        },
        {
            "name": "Kiran",
            "email": "kiran@example.com",
            "password_hash": password_hash,
            "avatar_color": get_avatar_color_for_email("kiran@example.com"),
            "created_at": datetime.utcnow() - timedelta(days=14)
        }
    ]
    
    users_inserted = []
    for u in users:
        res = await db.users_col.insert_one(u)
        u["id"] = res.inserted_id
        users_inserted.append(u)
        
    gowtham, asha, kiran = users_inserted
    
    # 3. Seed Workspace
    print("Seeding workspace...")
    ws = {
        "name": "Major Project — Team 7",
        "description": "CollabAI Shared workspace for final year design project",
        "owner_id": gowtham["id"],
        "members": [
            { "user_id": gowtham["id"], "name": gowtham["name"], "role": "owner", "joined_at": datetime.utcnow() - timedelta(days=15) },
            { "user_id": asha["id"], "name": asha["name"], "role": "member", "joined_at": datetime.utcnow() - timedelta(days=14) },
            { "user_id": kiran["id"], "name": kiran["name"], "role": "member", "joined_at": datetime.utcnow() - timedelta(days=14) }
        ],
        "created_at": datetime.utcnow() - timedelta(days=15)
    }
    
    ws_res = await db.workspaces_col.insert_one(ws)
    ws_id = ws_res.inserted_id
    
    # 4. Seed Channels
    print("Seeding channels...")
    chat_channel = {
        "workspace_id": ws_id,
        "type": "team_chat",
        "name": "general",
        "created_at": datetime.utcnow() - timedelta(days=15)
    }
    copilot_channel = {
        "workspace_id": ws_id,
        "type": "copilot",
        "name": "Project Copilot",
        "created_at": datetime.utcnow() - timedelta(days=15)
    }
    
    chat_res = await db.channels_col.insert_one(chat_channel)
    cop_res = await db.channels_col.insert_one(copilot_channel)
    
    chat_ch_id = chat_res.inserted_id
    cop_ch_id = cop_res.inserted_id
    
    # 5. Seed Documents
    print("Seeding documents...")
    docs_metadata = [
        ("system_architecture.pdf", "application/pdf", 120000, gowtham),
        ("database_schema.md", "text/markdown", 4500, asha),
        ("vector_search_atlas.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 42000, kiran)
    ]
    
    doc_ids = []
    for filename, mime, size, uploader in docs_metadata:
        doc_doc = {
            "workspace_id": ws_id,
            "filename": filename,
            "stored_path": f"./storage/{str(ws_id)}/seed_{filename}",
            "mime_type": mime,
            "size_bytes": size,
            "uploaded_by": uploader["id"],
            "uploader_name": uploader["name"],
            "status": "indexed",
            "error": None,
            "chunk_count": 8,
            "page_count": 3,
            "summary": f"This indexed document outlines details about {filename.replace('_', ' ')}. It covers technical definitions, constraints, and setup.",
            "created_at": datetime.utcnow() - timedelta(days=10)
        }
        res = await db.documents_col.insert_one(doc_doc)
        doc_ids.append(res.inserted_id)
        
    # 6. Seed Chunks (with 384 dimensions embeddings)
    print("Seeding mock vector chunks...")
    mock_chunks = [
        "The system uses FastAPI on the backend and React (Vite) on the frontend. Data flows between them via REST APIs and WebSockets for real-time chat updates.",
        "MongoDB Atlas is the single data store. Embeddings live in the 'chunks' collection and are queried with $vectorSearch against 'chunks_vec_index'.",
        "Fastembed is used as the local ONNX inference engine running BAAI/bge-small-en-v1.5, generating 384 dimensional embeddings locally on the CPU.",
        "LangGraph constructs the Copilot node orchestration pipeline: router -> research -> planner -> critic -> finalize. The critic runs at most once.",
        "The user database collection requires unique index on user emails. Workspaces embed memberships directly inside the workspace document.",
        "JSON schemas validate input payloads. Workspace isolation is guaranteed because workspace_id is a mandatory positional argument in retrieval queries.",
        "JWT tokens expire after 7 days and are signed with HS256. Passwords are encrypted using passlib with bcrypt hashing driver.",
        "The Tasks board has three columns: To Do, In Progress, and Done. Tasks created by Planner carry a specialized Planner Agent badge."
    ]
    
    for i, txt in enumerate(mock_chunks):
        # Generate dummy 384-dim normalized vector
        vec = [random.uniform(-0.1, 0.1) for _ in range(384)]
        norm = sum(x*x for x in vec) ** 0.5
        vec = [x / norm for x in vec]
        
        chunk_doc = {
            "workspace_id": ws_id,
            "text": txt,
            "embedding": vec,
            "source_type": "document",
            "document_id": doc_ids[i % len(doc_ids)],
            "filename": docs_metadata[i % len(doc_ids)][0],
            "page": (i // 3) + 1,
            "chunk_index": i,
            "channel_id": None,
            "message_id": None,
            "sender_name": None,
            "run_id": None,
            "created_at": datetime.utcnow() - timedelta(days=10)
        }
        await db.chunks_col.insert_one(chunk_doc)
        
    # 7. Seed Team Chat Messages (~30 messages)
    print("Seeding team chat conversation...")
    chat_dialogue = [
        (gowtham, "Hey team, welcome to our workspace. Let's make sure our scaffolding works."),
        (asha, "Thanks Gowtham! The database ping works fine. Health check returns connected."),
        (kiran, "Awesome. Did we decide on how to store vectors?"),
        (gowtham, "Yes, we are using MongoDB Atlas Vector Search. The spec says we shouldn't deploy a second vector database."),
        (asha, "Makes sense. It avoids synchronization errors when documents are deleted."),
        (kiran, "Great. @research where do we define the database collection schemas?"),
        # Agent Research Reply
        (None, "research", "The database collection schemas are defined in `03-DATA-MODEL.md`. The collections include `users`, `workspaces`, `channels`, `messages`, `documents`, `tasks`, `agent_runs`, and `chunks` [1]. Chunks hold 384-dimensional embeddings generated locally [3]."),
        (gowtham, "Nice, that answers it. By the way, I uploaded the system architecture document."),
        (asha, "I will write the FastAPI routers for Auth and Workspaces tonight."),
        (kiran, "Perfect. Don't forget that JWT tokens must expire after 7 days."),
        (asha, "Will do. Should I use passlib for bcrypt?"),
        (gowtham, "Yes, passlib with bcrypt is standard. Keep it async to prevent event loop blocking."),
        (kiran, "Hey @research what embedding model did we decide to use?"),
        # Agent Research Reply
        (None, "research", "The team decided to use `fastembed` running the `BAAI/bge-small-en-v1.5` model [3]. It emits 384-dimensional embeddings, runs locally via ONNX Runtime (~130 MB size), and is CPU-friendly [3]."),
        (kiran, "Perfect, thank you!"),
        (asha, "I've added the websocket manager. Connections are keyed by workspace_id."),
        (gowtham, "Great work Asha. Does it broadcast typing indicators?"),
        (asha, "Yes! When users type, a typing action is broadcast to the room."),
        (kiran, "Let's check if the client automatically reconnects when the server restarts."),
        (asha, "Yes, I implemented exponential backoff reconnection. It retries from 1s to 30s."),
        (gowtham, "Excellent. The quality floor requirements are met."),
        (kiran, "Should we check the tasks list? I will start designing the Tasks kanban board tomorrow.")
    ]
    
    current_time = datetime.utcnow() - timedelta(days=3)
    for sender, content_or_agent, *agent_text in chat_dialogue:
        current_time += timedelta(hours=2)
        
        if sender is not None:
            # Human message
            msg = {
                "workspace_id": ws_id,
                "channel_id": chat_ch_id,
                "sender_type": "user",
                "sender_id": sender["id"],
                "sender_name": sender["name"],
                "content": content_or_agent,
                "citations": [],
                "run_id": None,
                "mentioned_agents": ["research"] if "@research" in content_or_agent else [],
                "indexed": True,
                "created_at": current_time
            }
        else:
            # Agent message
            agent_key = content_or_agent
            text = agent_text[0]
            
            # Map mock citations
            citations = [
                {
                    "source_type": "document",
                    "document_id": doc_ids[1],
                    "filename": "database_schema.md",
                    "page": 1,
                    "snippet": "MongoDB Atlas is the single data store."
                }
            ]
            
            msg = {
                "workspace_id": ws_id,
                "channel_id": chat_ch_id,
                "sender_type": "agent",
                "sender_id": agent_key,
                "sender_name": f"{agent_key.capitalize()} Agent",
                "content": text,
                "citations": citations,
                "run_id": None,
                "mentioned_agents": [],
                "indexed": True,
                "created_at": current_time
            }
        await db.messages_col.insert_one(msg)
        
    # 8. Seed Copilot Runs and Planning Tasks
    print("Seeding copilot runs and planner tasks...")
    cop_run_id = ObjectId()
    now = datetime.utcnow()
    
    # Insert completed Copilot Run doc
    run_doc = {
        "_id": cop_run_id,
        "workspace_id": ws_id,
        "channel_id": cop_ch_id,
        "user_id": gowtham["id"],
        "query": "plan the next two weeks of backend API work",
        "intent": "planning",
        "status": "done",
        "final_answer": "### Sprint Plan: Backend API\nWe will implement JWT authentication, workspaces CRUD operations, and real-time WebSockets [1].\n\n#### Milestone 1: Auth Services\n- Build registration and login routers.\n- Implement passlib bcrypt hashing [7].\n\n#### Milestone 2: Workspace Management\n- Implement workspace creation and auto-channels [5].\n- Add invite endpoints.",
        "citations": [
            {
                "source_type": "document",
                "document_id": doc_ids[0],
                "filename": "system_architecture.pdf",
                "page": 1,
                "snippet": "The system uses FastAPI on the backend and React..."
            }
        ],
        "trace": [
            { "step": 1, "agent": "router", "input_summary": "plan the next two weeks...", "output_summary": '{"intent": "planning"}', "provider": "groq", "model": "llama-3.1-8b-instant", "tokens_in": 210, "tokens_out": 24, "latency_ms": 380, "started_at": now - timedelta(minutes=5) },
            { "step": 2, "agent": "research", "input_summary": "findings...", "output_summary": 'Retrieved details about authentication...', "provider": "groq", "model": "llama-3.3-70b-versatile", "tokens_in": 1200, "tokens_out": 300, "latency_ms": 1500, "started_at": now - timedelta(minutes=4) },
            { "step": 3, "agent": "planner", "input_summary": "sprint design...", "output_summary": 'Draft sprint milestones...', "provider": "groq", "model": "llama-3.3-70b-versatile", "tokens_in": 2500, "tokens_out": 600, "latency_ms": 2800, "started_at": now - timedelta(minutes=3) },
            { "step": 4, "agent": "critic", "input_summary": "review plan...", "output_summary": '{"needs_revision": false}', "provider": "groq", "model": "llama-3.1-8b-instant", "tokens_in": 3200, "tokens_out": 45, "latency_ms": 900, "started_at": now - timedelta(minutes=2) },
            { "step": 5, "agent": "finalize", "input_summary": "assembly...", "output_summary": 'Final Answer Generated', "started_at": now - timedelta(minutes=1) }
        ],
        "total_tokens": 7179,
        "total_latency_ms": 5580,
        "revision_count": 0,
        "error": None,
        "created_at": now - timedelta(minutes=5),
        "completed_at": now - timedelta(minutes=1)
    }
    await db.agent_runs_col.insert_one(run_doc)
    
    # Insert copilot chat messages
    cop_messages = [
        {
            "workspace_id": ws_id,
            "channel_id": cop_ch_id,
            "sender_type": "user",
            "sender_id": gowtham["id"],
            "sender_name": gowtham["name"],
            "content": "plan the next two weeks of backend API work",
            "citations": [],
            "run_id": None,
            "mentioned_agents": [],
            "indexed": False,
            "created_at": now - timedelta(minutes=5)
        },
        {
            "workspace_id": ws_id,
            "channel_id": cop_ch_id,
            "sender_type": "agent",
            "sender_id": "copilot",
            "sender_name": "Project Copilot",
            "content": run_doc["final_answer"],
            "citations": run_doc["citations"],
            "run_id": cop_run_id,
            "mentioned_agents": [],
            "indexed": True,
            "created_at": now - timedelta(minutes=1)
        }
    ]
    await db.messages_col.insert_many(cop_messages)
    
    # Insert Planner Agent tasks
    tasks = [
        {
            "workspace_id": ws_id,
            "title": "Implement JWT endpoints in auth.py",
            "description": "Create register, login and me endpoints as specified in API Specification.",
            "status": "todo",
            "priority": "high",
            "assignee_id": asha["id"],
            "assignee_name": asha["name"],
            "due_date": now + timedelta(days=2),
            "created_by": "agent:planner",
            "run_id": cop_run_id,
            "created_at": now,
            "updated_at": now
        },
        {
            "workspace_id": ws_id,
            "title": "Write dependencies.py checks",
            "description": "Implement require_member and require_owner workspace isolation handlers.",
            "status": "in_progress",
            "priority": "medium",
            "assignee_id": gowtham["id"],
            "assignee_name": gowtham["name"],
            "due_date": now + timedelta(days=4),
            "created_by": "agent:planner",
            "run_id": cop_run_id,
            "created_at": now,
            "updated_at": now
        },
        {
            "workspace_id": ws_id,
            "title": "Setup fastembed model warming",
            "description": "Configure the TextEmbedding singleton to initialize during FastAPI startup.",
            "status": "done",
            "priority": "low",
            "assignee_id": kiran["id"],
            "assignee_name": kiran["name"],
            "due_date": now - timedelta(days=1),
            "created_by": "agent:planner",
            "run_id": cop_run_id,
            "created_at": now,
            "updated_at": now
        }
    ]
    await db.tasks_col.insert_many(tasks)
    
    await db.close_db()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_data())
