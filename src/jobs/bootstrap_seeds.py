import sys
import logging
import requests
from datetime import datetime
from src.config import config
from src.database import get_sync_connection
from src.shared.utils import setup_logging

logger = setup_logging("tide.jobs.bootstrap_seeds")

# Define 25 technical seed concepts
SEED_CONCEPTS = [
    {
        "canonical_label": "postgresql",
        "aliases": ["postgres", "postgresql-database", "psql"],
        "description": "PostgreSQL is a powerful, open-source object-relational database system known for reliability, feature robustness, and performance. It supports advanced data types like JSONB and extensions like pgvector for vector search."
    },
    {
        "canonical_label": "fastapi",
        "aliases": ["fastapi-framework", "fastapi-api"],
        "description": "FastAPI is a modern, fast, high-performance web framework for building APIs with Python 3.8+ based on standard Python type hints. It is built on Starlette and Pydantic for data validation."
    },
    {
        "canonical_label": "supabase",
        "aliases": ["supabase-db", "supabase-platform"],
        "description": "Supabase is an open-source Firebase alternative providing a Postgres database, authentication, instant APIs, Edge Functions, Realtime subscriptions, and vector storage."
    },
    {
        "canonical_label": "docker",
        "aliases": ["docker-containers", "dockerfile"],
        "description": "Docker is a platform designed to help developers build, share, run, and orchestrate containerized applications. It isolates software in lightweight packages called containers."
    },
    {
        "canonical_label": "kubernetes",
        "aliases": ["k8s", "kubernetes-cluster"],
        "description": "Kubernetes is an open-source container orchestration system for automating software deployment, scaling, and management. It manages clusters of containerized applications."
    },
    {
        "canonical_label": "git",
        "aliases": ["git-version-control", "github-git"],
        "description": "Git is a distributed version control system designed to track changes in source code during software development, facilitating collaboration among programmers."
    },
    {
        "canonical_label": "python",
        "aliases": ["python-lang", "python3"],
        "description": "Python is an interpreted, high-level, general-purpose programming language. Its design philosophy emphasizes code readability, and it is widely used in data science, AI, and web development."
    },
    {
        "canonical_label": "machine-learning",
        "aliases": ["ml", "machine-learning-algorithms"],
        "description": "Machine learning is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data."
    },
    {
        "canonical_label": "large-language-models",
        "aliases": ["llm", "large-language-model", "llms", "gpt", "transformer-models"],
        "description": "Large Language Models are deep learning neural networks trained on vast text corpora to understand, summarize, generate, and predict text. They are based on the Transformer architecture."
    },
    {
        "canonical_label": "embeddings",
        "aliases": ["vector-embeddings", "text-embeddings", "nomic-embed"],
        "description": "Embeddings are low-dimensional, continuous vector representations of high-dimensional data (like text or images) that capture semantic relationships and contextual meanings."
    },
    {
        "canonical_label": "vector-databases",
        "aliases": ["vector-database", "vector-db", "pgvector", "pinecone", "chromadb", "qdrant"],
        "description": "Vector databases are specialized storage systems designed to index, store, and query high-dimensional vector embeddings efficiently, supporting fast nearest-neighbor similarity searches."
    },
    {
        "canonical_label": "retrieval-augmented-generation",
        "aliases": ["rag", "rag-pipeline", "retrieval-augmented"],
        "description": "Retrieval-Augmented Generation is an NLP architecture that optimizes LLM output by querying an authoritative external database or knowledge base to ground the generation with fresh factual data."
    },
    {
        "canonical_label": "ai-agents",
        "aliases": ["ai-agent", "agentic", "agentic-workflows", "autonomous-agents"],
        "description": "AI agents are autonomous software systems designed to perceive their environment, run reasoning steps, make decisions, and invoke external tools to achieve specific goals."
    },
    {
        "canonical_label": "graphql",
        "aliases": ["graphql-api", "graphql-schema"],
        "description": "GraphQL is a query language and server-side runtime for APIs that prioritizes giving clients exactly the data they request, enabling efficient data fetching and type safety."
    },
    {
        "canonical_label": "rust",
        "aliases": ["rust-lang", "rust-programming"],
        "description": "Rust is a multi-paradigm, general-purpose systems programming language focused on performance, type safety, and concurrency. It guarantees memory safety without a garbage collector."
    },
    {
        "canonical_label": "github",
        "aliases": ["github-platform", "gh"],
        "description": "GitHub is a developer platform that allows developers to create, store, manage, and share code repositories. It provides hosting for Git repositories, issue tracking, and CI/CD tools."
    },
    {
        "canonical_label": "hacker-news",
        "aliases": ["hn", "ycombinator"],
        "description": "Hacker News is a social news website run by Y Combinator focusing on computer science, entrepreneurship, technology, and engineering discussions."
    },
    {
        "canonical_label": "arxiv",
        "aliases": ["arxiv-papers", "arxiv-preprint"],
        "description": "arXiv is a free distribution service and open-access archive for scholarly articles in physics, mathematics, computer science, quantitative biology, and statistics."
    },
    {
        "canonical_label": "react",
        "aliases": ["reactjs", "react-library"],
        "description": "React is a free and open-source front-end JavaScript library developed by Meta for building user interfaces based on reusable UI components."
    },
    {
        "canonical_label": "typescript",
        "aliases": ["ts", "typescript-lang"],
        "description": "TypeScript is a strongly typed programming language that builds on JavaScript, giving you better tooling and type safety at any scale. It compiles to plain JavaScript."
    },
    {
        "canonical_label": "deep-learning",
        "aliases": ["neural-networks", "neural-network", "backpropagation"],
        "description": "Deep learning is a subset of machine learning based on artificial neural networks with multiple layers, enabling representation learning from raw data."
    },
    {
        "canonical_label": "leiden-algorithm",
        "aliases": ["leiden-clustering", "community-detection"],
        "description": "The Leiden algorithm is a general community detection algorithm that decomposes networks into cohesive subgroups or modular communities, improving on the Louvain method."
    },
    {
        "canonical_label": "umaps",
        "aliases": ["umap-projection", "dimension-reduction"],
        "description": "UMAP (Uniform Manifold Approximation and Projection) is a novel manifold learning technique for dimension reduction, preserving both local and global structure in 2D/3D visualizations."
    },
    {
        "canonical_label": "reinforcement-learning",
        "aliases": ["rl", "q-learning", "policy-gradient"],
        "description": "Reinforcement learning is an area of machine learning concerned with how software agents ought to take actions in an environment to maximize some notion of cumulative reward."
    },
    {
        "canonical_label": "microservices",
        "aliases": ["microservice-architecture", "soa"],
        "description": "Microservices is an architectural pattern that structures an application as a collection of autonomous, loosely coupled services, communicating via APIs."
    }
]

def get_embedding(text: str) -> list[float]:
    """Calls the local embedding service on port 8001."""
    url = f"http://{config.embedding_host}:{config.embedding_port}/embed"
    payload = {"texts": [text], "type": "document"}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            raise Exception(f"Failed to generate embedding: {resp.text}")
        return resp.json()["embeddings"][0]
    except Exception as e:
        logger.error(f"Error calling embedding service: {e}")
        raise

def bootstrap():
    logger.info("Starting seed concept bootstrapping...")
    
    # 1. Generate embeddings for all seeds
    for concept in SEED_CONCEPTS:
        logger.info(f"Generating embedding for: {concept['canonical_label']}...")
        try:
            # Embed the description paragraph
            emb = get_embedding(concept["description"])
            concept["embedding"] = emb
        except Exception as e:
            logger.error(f"Skipping {concept['canonical_label']} due to embedding error: {e}")
            sys.exit(1)
            
    # 2. Connect to database and insert seeds
    logger.info("Connecting to database to insert concepts...")
    try:
        with get_sync_connection() as conn:
            with conn.cursor() as cur:
                # Disable active statuses if we want to overwrite, or skip existing
                # For safety, we skip or update existing canonical_labels
                for c in SEED_CONCEPTS:
                    cur.execute(
                        """
                        INSERT INTO concepts (canonical_label, aliases, embedding, status, created_at, post_count)
                        VALUES (%s, %s, %s, 'active', NOW(), 0)
                        ON CONFLICT (canonical_label) DO UPDATE
                        SET aliases = EXCLUDED.aliases, embedding = EXCLUDED.embedding
                        """,
                        (c["canonical_label"], c["aliases"], c["embedding"])
                    )
                conn.commit()
        logger.info("Successfully bootstrapped 25 seed concepts in Supabase!")
    except Exception as e:
        logger.error(f"Database insertion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    bootstrap()
