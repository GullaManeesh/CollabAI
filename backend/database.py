from motor.motor_asyncio import AsyncIOMotorClient
import pymongo
import dns.resolver
import logging
from backend.config import settings

logger = logging.getLogger(__name__)

# Module-level variables that will be initialized inside the lifespan handler
client: AsyncIOMotorClient = None
db = None

# Collection helpers
users_col = None
workspaces_col = None
channels_col = None
messages_col = None
documents_col = None
tasks_col = None
agent_runs_col = None
chunks_col = None

async def init_db():
    global client, db, users_col, workspaces_col, channels_col, messages_col, documents_col, tasks_col, agent_runs_col, chunks_col
    
    logger.info("Initializing MongoDB Client with URI...")
    if settings.MONGODB_URI.startswith("mongodb+srv://"):
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = ["8.8.8.8", "1.1.1.1"]
        dns.resolver.default_resolver = resolver
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DB_NAME]
    
    # Set up collections
    users_col = db["users"]
    workspaces_col = db["workspaces"]
    channels_col = db["channels"]
    messages_col = db["messages"]
    documents_col = db["documents"]
    tasks_col = db["tasks"]
    agent_runs_col = db["agent_runs"]
    chunks_col = db["chunks"]
    
    # Ping database to verify connection
    await db.command("ping")
    logger.info("MongoDB connection successful.")
    
    # Create indexes as specified in 03-DATA-MODEL.md
    logger.info("Creating MongoDB indexes...")
    
    # 1. Users: email unique
    await users_col.create_index([("email", pymongo.ASCENDING)], unique=True)
    
    # 2. Workspaces: members.user_id
    await workspaces_col.create_index([("members.user_id", pymongo.ASCENDING)])
    
    # 3. Channels: compound (workspace_id, type)
    await channels_col.create_index([
        ("workspace_id", pymongo.ASCENDING),
        ("type", pymongo.ASCENDING)
    ])
    
    # 4. Messages: (channel_id, created_at) and (workspace_id, indexed)
    await messages_col.create_index([
        ("channel_id", pymongo.ASCENDING),
        ("created_at", pymongo.ASCENDING)
    ])
    await messages_col.create_index([
        ("workspace_id", pymongo.ASCENDING),
        ("indexed", pymongo.ASCENDING)
    ])
    
    # 5. Documents: (workspace_id, created_at)
    await documents_col.create_index([
        ("workspace_id", pymongo.ASCENDING),
        ("created_at", pymongo.ASCENDING)
    ])
    
    # 6. Tasks: (workspace_id, status)
    await tasks_col.create_index([
        ("workspace_id", pymongo.ASCENDING),
        ("status", pymongo.ASCENDING)
    ])
    
    # 7. Agent Runs: (workspace_id, created_at)
    await agent_runs_col.create_index([
        ("workspace_id", pymongo.ASCENDING),
        ("created_at", pymongo.ASCENDING)
    ])
    
    # 8. Chunks: (workspace_id, document_id) for deletion, (workspace_id, source_type)
    await chunks_col.create_index([
        ("workspace_id", pymongo.ASCENDING),
        ("document_id", pymongo.ASCENDING)
    ])
    await chunks_col.create_index([
        ("workspace_id", pymongo.ASCENDING),
        ("source_type", pymongo.ASCENDING)
    ])
    
    logger.info("MongoDB indexes created successfully.")

async def close_db():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")
