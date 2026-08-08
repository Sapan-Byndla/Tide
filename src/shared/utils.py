import re
import logging
from typing import List
import numpy as np

def setup_logging(name: str = "tide", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a logger with standard formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two numeric vectors."""
    a = np.array(v1)
    b = np.array(v2)
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))

def clean_text(text: str) -> str:
    """Applies basic cleaning to text (lowercasing, punctuation stripping)."""
    if not text:
        return ""
    # Lowercase and remove extra whitespace
    text = text.lower().strip()
    # Replace newlines with spaces
    text = re.sub(r'\s+', ' ', text)
    return text

def tokenize(text: str, min_length: int = 3) -> List[str]:
    """Tokenizes cleaned text into words, stripping punctuation."""
    cleaned = clean_text(text)
    # Remove punctuation except hyphens
    cleaned = re.sub(r'[^a-z0-9\s-]', '', cleaned)
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) >= min_length]
    return tokens
