import re
import logging
from typing import List, Set
import asyncpg
from src.shared.utils import tokenize

logger = logging.getLogger("tide.ingest.phrases")

# Basic set of English stopwords to avoid installing NLTK/scikit-learn datasets just for scaffolding
STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "arent", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "cant", "cannot", "could",
    "did", "didnt", "do", "does", "doesnt", "doing", "dont", "down", "during", "each", "few", "for", "from", "further",
    "had", "hadnt", "has", "hasnt", "have", "havent", "having", "he", "hed", "hell", "hes", "her", "here", "heres",
    "hers", "herself", "him", "himself", "his", "how", "hows", "i", "id", "if", "in", "into", "is", "isnt", "it",
    "its", "itself", "lets", "me", "more", "most", "mustnt", "my", "myself", "no", "nor", "not", "of", "off", "on",
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shant", "she",
    "shed", "shell", "shes", "should", "shouldnt", "so", "some", "such", "than", "that", "thats", "the", "their",
    "theirs", "them", "themselves", "then", "there", "theres", "these", "they", "theyd", "theyll", "theyre", "theyve",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasnt", "we", "wed", "well",
    "were", "weve", "werent", "what", "whats", "when", "whens", "where", "wheres", "which", "while", "who", "whos",
    "whom", "why", "whys", "with", "wont", "would", "wouldnt", "you", "youd", "youll", "youre", "youve", "your",
    "yours", "yourself", "yourselves"
}

# Denylist for generic technical phrases that shouldn't graduate
GENERIC_DENYLIST: Set[str] = {
    "open source", "machine learning", "artificial intelligence", "large language", "language model", 
    "deep learning", "neural network", "software engineering", "source code", "pull request", "github repo",
    "read me", "bug fix", "command line", "operating system", "web application", "user interface", "data structure",
    "programming language", "software development", "web dev", "cloud computing"
}

def extract_phrases(title: str, body: str) -> List[str]:
    """Tokenizes text and extracts distinctive bigrams and trigrams, filtering stopwords."""
    text_content = f"{title} {body or ''}"
    tokens = tokenize(text_content, min_length=3)
    
    if len(tokens) < 2:
        return []
        
    phrases = []
    
    # Generate Bigrams
    for i in range(len(tokens) - 1):
        w1, w2 = tokens[i], tokens[i+1]
        # Skip if all words are stopwords or match denylist
        if w1 in STOPWORDS and w2 in STOPWORDS:
            continue
        phrase = f"{w1} {w2}"
        if phrase not in GENERIC_DENYLIST:
            phrases.append(phrase)
            
    # Generate Trigrams
    for i in range(len(tokens) - 2):
        w1, w2, w3 = tokens[i], tokens[i+1], tokens[i+2]
        if w1 in STOPWORDS and w2 in STOPWORDS and w3 in STOPWORDS:
            continue
        phrase = f"{w1} {w2} {w3}"
        if phrase not in GENERIC_DENYLIST:
            phrases.append(phrase)
            
    # Return unique phrases
    return list(set(phrases))

async def record_phrase_observations(conn: asyncpg.Connection, post_id: int, source: str, phrases: List[str]):
    """Inserts a list of phrase observations for a given post."""
    if not phrases:
        return
        
    logger.info(f"Recording {len(phrases)} phrase observations for post {post_id}...")
    
    # Batch insert to avoid individual hits
    query = """
        INSERT INTO phrase_observations (phrase, post_id, source, observed_at)
        VALUES ($1, $2, $3, NOW())
    """
    
    # Prepare batch execution values
    data = [(phrase, post_id, source) for phrase in phrases]
    try:
        await conn.executemany(query, data)
    except Exception as e:
        logger.error(f"Failed to save phrase observations: {e}")
        raise
