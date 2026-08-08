import logging
import threading
from typing import List, Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from src.config import config
from src.shared.utils import setup_logging

logger = setup_logging("tide.embedding")

app = FastAPI(
    title="Tide Embedding Service",
    description="Local service running nomic-embed-text-v1.5 using SentenceTransformers",
    version="1.0"
)

# Global model container for lazy loading
model = None
model_lock = threading.Lock()

class EmbedRequest(BaseModel):
    texts: List[str] = Field(..., max_items=64, description="List of texts to embed. Max 64 items.")
    type: Literal["document", "query"] = Field("document", description="Prefix type required by Nomic Embed model.")

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    model_name: str

def get_model():
    global model
    if model is None:
        model_name = config.embedding_model_name
        logger.info(f"Lazy loading embedding model: {model_name}...")
        try:
            from sentence_transformers import SentenceTransformer
            # trust_remote_code=True is required for custom model architectures like Nomic Embed v1.5
            model = SentenceTransformer(model_name, trust_remote_code=True)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers model: {e}")
            raise RuntimeError(f"Model initialization failed: {e}")
    return model

@app.on_event("startup")
async def startup_event():
    logger.info("Embedding service starting up...")
    # Pre-load the model to save latency on the first request
    try:
        get_model()
    except Exception as e:
        logger.warning(f"Failed to pre-load model during startup (will retry on first request): {e}")

@app.post("/embed", response_model=EmbedResponse)
def embed_text(req: EmbedRequest):
    try:
        transformer = get_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding engine is unavailable: {e}")

    processed_texts = []
    prefix = "search_document: " if req.type == "document" else "search_query: "
    
    for text in req.texts:
        # Prepend prefix if not already present
        if not text.startswith(prefix):
            processed_texts.append(f"{prefix}{text}")
        else:
            processed_texts.append(text)

    logger.info(f"Generating embeddings for batch of size {len(processed_texts)}...")
    try:
        # Convert numpy arrays to float lists
        with model_lock:
            embeddings = transformer.encode(processed_texts, convert_to_numpy=True)
        embeddings_list = embeddings.tolist()
        return EmbedResponse(
            embeddings=embeddings_list,
            model_name=config.embedding_model_name
        )
    except Exception as e:
        logger.error(f"Failed to encode text batch: {e}")
        raise HTTPException(status_code=500, detail=f"Encoding failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.embedding.main:app",
        host=config.embedding_host,
        port=config.embedding_port,
        reload=True
    )
