from bson import ObjectId
from datetime import datetime
import os
import logging
import traceback

import backend.database as db
from backend.rag.parsers import parse_document
from backend.rag.chunking import chunk_document_pages
from backend.rag.embeddings import embed_documents

logger = logging.getLogger(__name__)

async def ingest_document_background(workspace_id: str, document_id: str, file_path: str, mime_type: str):
    logger.info(f"Starting background ingestion for document {document_id} in workspace {workspace_id}")
    
    ws_oid = ObjectId(workspace_id)
    doc_oid = ObjectId(document_id)
    
    try:
        # 1. Fetch document metadata
        doc = await db.documents_col.find_one({"_id": doc_oid})
        if not doc:
            logger.error(f"Document {document_id} not found in DB")
            return
            
        # 2. Parse document text and pages
        pages_data, total_pages = parse_document(file_path, mime_type)
        
        # 3. Chunk text
        chunks = chunk_document_pages(pages_data)
        
        if not chunks:
            logger.warning(f"No chunks created for document {document_id}")
            await db.documents_col.update_one(
                {"_id": doc_oid},
                {
                    "$set": {
                        "status": "indexed",
                        "page_count": total_pages,
                        "chunk_count": 0,
                        "error": None
                    }
                }
            )
            return
            
        # 4. Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = embed_documents(texts)
        
        # 5. Build chunk documents
        now = datetime.utcnow()
        chunk_docs = []
        for i, chunk in enumerate(chunks):
            chunk_docs.append({
                "workspace_id": ws_oid,
                "text": chunk["text"],
                "embedding": embeddings[i],
                "source_type": "document",
                "document_id": doc_oid,
                "filename": doc["filename"],
                "page": chunk["page"],
                "chunk_index": chunk["chunk_index"],
                "channel_id": None,
                "message_id": None,
                "sender_name": None,
                "run_id": None,
                "created_at": now
            })
            
        # 6. Insert chunks into MongoDB
        await db.chunks_col.insert_many(chunk_docs)
        
        # 7. Update document status
        await db.documents_col.update_one(
            {"_id": doc_oid},
            {
                "$set": {
                    "status": "indexed",
                    "page_count": total_pages,
                    "chunk_count": len(chunk_docs),
                    "error": None
                }
            }
        )
        logger.info(f"Ingestion successful for document {document_id}. Chunks indexed: {len(chunk_docs)}")
        
    except Exception as e:
        error_msg = f"Ingestion failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        await db.documents_col.update_one(
            {"_id": doc_oid},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e)
                }
            }
        )

async def check_and_index_messages_background(workspace_id: str, channel_id: str):
    """
    Checks if there are at least 10 unindexed messages in this channel,
    and batches them into 10-message chunks for vector embedding.
    """
    ws_oid = ObjectId(workspace_id)
    ch_oid = ObjectId(channel_id)
    
    logger.info(f"Checking unindexed messages for channel {channel_id}")
    
    # Query unindexed messages
    cursor = db.messages_col.find({
        "channel_id": ch_oid,
        "indexed": False
    }).sort([("created_at", 1)])
    
    unindexed_msgs = await cursor.to_list(length=200)
    
    if len(unindexed_msgs) < 10:
        logger.info(f"Only {len(unindexed_msgs)} unindexed messages in channel {channel_id}. Ingestion skipped.")
        return
        
    # Process in groups of 10
    batch_size = 10
    num_batches = len(unindexed_msgs) // batch_size
    
    logger.info(f"Indexing {num_batches * batch_size} messages in {num_batches} batches...")
    
    for b in range(num_batches):
        batch = unindexed_msgs[b * batch_size : (b + 1) * batch_size]
        msg_ids = [m["_id"] for m in batch]
        
        # Format block as per 05-AGENTS-AND-RAG.md: "[HH:MM] Name: content"
        formatted_lines = []
        for msg in batch:
            time_str = msg["created_at"].strftime("%H:%M")
            formatted_lines.append(f"[{time_str}] {msg['sender_name']}: {msg['content']}")
            
        text_block = "\n".join(formatted_lines)
        
        try:
            # Generate embedding
            embeddings = embed_documents([text_block])
            embedding = embeddings[0]
            
            # Create chunk
            last_msg = batch[-1]
            now = datetime.utcnow()
            
            chunk_doc = {
                "workspace_id": ws_oid,
                "text": text_block,
                "embedding": embedding,
                "source_type": "message",
                "document_id": None,
                "filename": None,
                "page": 0,
                "chunk_index": 0,
                "channel_id": ch_oid,
                "message_id": last_msg["_id"],
                "sender_name": last_msg["sender_name"],
                "run_id": None,
                "created_at": now
            }
            
            # Save chunk
            await db.chunks_col.insert_one(chunk_doc)
            
            # Mark messages as indexed
            await db.messages_col.update_many(
                {"_id": {"$in": msg_ids}},
                {"$set": {"indexed": True}}
            )
            
            logger.info(f"Successfully indexed batch of 10 messages ending at message {last_msg['_id']}")
            
        except Exception as e:
            logger.error(f"Failed to index message batch: {e}")
            # Keep them unindexed for retry next time
            continue
