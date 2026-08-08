import os
import yaml
from pathlib import Path

# Locate root directory containing config.yaml
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config.yaml"

class Config:
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path
        self._data = {}
        self.load()

    def load(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}

    @property
    def database_url(self) -> str:
        # Prioritize environment variable over config file
        return os.getenv("TIDE_DATABASE_URL", self._data.get("database", {}).get("url", ""))

    @property
    def database_pool_min(self) -> int:
        return self._data.get("database", {}).get("pool_size_min", 5)

    @property
    def database_pool_max(self) -> int:
        return self._data.get("database", {}).get("pool_size_max", 20)

    @property
    def embedding_host(self) -> str:
        return self._data.get("services", {}).get("embedding", {}).get("host", "127.0.0.1")

    @property
    def embedding_port(self) -> int:
        return self._data.get("services", {}).get("embedding", {}).get("port", 8001)

    @property
    def embedding_model_name(self) -> str:
        return self._data.get("services", {}).get("embedding", {}).get("model_name", "nomic-ai/nomic-embed-text-v1.5")

    @property
    def embedding_batch_size(self) -> int:
        return self._data.get("services", {}).get("embedding", {}).get("batch_size", 64)

    @property
    def ingest_host(self) -> str:
        return self._data.get("services", {}).get("ingest", {}).get("host", "127.0.0.1")

    @property
    def ingest_port(self) -> int:
        return self._data.get("services", {}).get("ingest", {}).get("port", 8002)

    @property
    def ingest_similarity_threshold(self) -> float:
        return self._data.get("services", {}).get("ingest", {}).get("embedding_similarity_threshold", 0.55)

    @property
    def ema_alpha(self) -> float:
        return self._data.get("services", {}).get("ingest", {}).get("ema_alpha", 0.05)

    @property
    def read_api_host(self) -> str:
        return self._data.get("services", {}).get("read_api", {}).get("host", "127.0.0.1")

    @property
    def read_api_port(self) -> int:
        return self._data.get("services", {}).get("read_api", {}).get("port", 8003)

    @property
    def phrase_min_token_length(self) -> int:
        return self._data.get("phrase_extraction", {}).get("min_token_length", 3)

    @property
    def phrase_clean_pattern(self) -> str:
        return self._data.get("phrase_extraction", {}).get("clean_pattern", '[^a-zA-Z0-9\\s-]')

    @property
    def pending_similarity_threshold(self) -> float:
        return self._data.get("pending_pool", {}).get("similarity_threshold", 0.55)

    @property
    def pending_min_component_size(self) -> int:
        return self._data.get("pending_pool", {}).get("min_component_size", 3)

    @property
    def pending_ttl_days(self) -> int:
        return self._data.get("pending_pool", {}).get("ttl_days", 14)

    @property
    def pending_distinctive_token_threshold(self) -> float:
        return self._data.get("pending_pool", {}).get("distinctive_token_frequency_threshold", 0.01)

    @property
    def phrase_grad_min_count_7d(self) -> int:
        return self._data.get("phrase_graduation", {}).get("min_count_last_7d", 5)

    @property
    def phrase_grad_min_source_count(self) -> int:
        return self._data.get("phrase_graduation", {}).get("min_source_count", 2)

    @property
    def phrase_grad_velocity_multiplier(self) -> float:
        return self._data.get("phrase_graduation", {}).get("velocity_multiplier", 3.0)

    @property
    def phrase_grad_graduate_count_7d(self) -> int:
        return self._data.get("phrase_graduation", {}).get("graduate_count_last_7d", 10)

    @property
    def phrase_grad_min_title_appearances(self) -> int:
        return self._data.get("phrase_graduation", {}).get("min_title_appearances", 3)

    @property
    def phrase_grad_noise_days(self) -> int:
        return self._data.get("phrase_graduation", {}).get("noise_days", 30)

    @property
    def community_recency_decay_lambda(self) -> float:
        return self._data.get("community_detection", {}).get("recency_decay_lambda", 0.02)

    @property
    def community_min_edge_co_count(self) -> int:
        return self._data.get("community_detection", {}).get("min_edge_co_count", 2)

    @property
    def maintenance_merge_similarity(self) -> float:
        return self._data.get("concept_maintenance", {}).get("merge_similarity_threshold", 0.85)

    @property
    def maintenance_merge_shared_posts_ratio(self) -> float:
        return self._data.get("concept_maintenance", {}).get("merge_shared_posts_ratio", 0.30)

    @property
    def maintenance_split_min_posts(self) -> int:
        return self._data.get("concept_maintenance", {}).get("split_min_posts", 50)

    @property
    def maintenance_split_subcluster_min(self) -> int:
        return self._data.get("concept_maintenance", {}).get("split_subcluster_min_posts", 10)

    def get_scraper_config(self, scraper_name: str) -> dict:
        return self._data.get("scrapers", {}).get(scraper_name, {"enabled": False})

# Global configuration instance
config = Config()
