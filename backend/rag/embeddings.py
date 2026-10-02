from fastembed import TextEmbedding
import logging

logger = logging.getLogger(__name__)

_model = None            # load once, module-level singleton

def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        logger.info("Initializing fastembed model (BAAI/bge-small-en-v1.5)...")
        _model = TextEmbedding("BAAI/bge-small-en-v1.5")   # 384-dim, ~130 MB ONNX
        logger.info("fastembed model initialized successfully.")
    return _model

def embed_documents(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    # embed returns a generator of numpy arrays, convert to list of floats
    return [v.tolist() for v in get_model().embed(texts, batch_size=32)]

def embed_query(text: str) -> list[float]:
    # query_embed returns a generator of numpy arrays, get the first one
    return next(get_model().query_embed(text)).tolist()
