"""Cross-platform pain point clustering using semantic similarity.

Groups similar pain points from different sources (Reddit, Twitter, YouTube, etc.)
to enable multi-source validation and aggregated engagement scoring.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional

from langchain_openai import OpenAIEmbeddings
import numpy as np

from processor.viral_app.models import PainPoint
from config.settings import OPENAI_API_KEY, EMBEDDING_MODEL, EMBEDDING_SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)


@dataclass
class PainPointCluster:
    """A group of semantically similar pain points from multiple sources."""
    
    representative: str  # Best description of the problem
    pain_points: list[PainPoint] = field(default_factory=list)
    source_breakdown: dict[str, int] = field(default_factory=dict)  # {source: total_engagement}
    total_engagement: int = 0
    
    def add_pain_point(self, pp: PainPoint):
        """Add a pain point to this cluster and update aggregates."""
        self.pain_points.append(pp)
        
        # Aggregate engagement by source
        source = pp.source.lower()
        self.source_breakdown[source] = self.source_breakdown.get(source, 0) + pp.engagement
        self.total_engagement += pp.engagement
    
    @property
    def source_count(self) -> int:
        """Number of unique sources in this cluster."""
        return len(self.source_breakdown)
    
    @property
    def sources_list(self) -> list[str]:
        """List of sources, sorted by engagement."""
        return sorted(self.source_breakdown.keys(), key=lambda s: self.source_breakdown[s], reverse=True)


class ClusteringEngine:
    """
    Groups similar pain points using embedding-based semantic similarity.
    
    Uses OpenAI embeddings to compute similarity between pain point descriptions,
    then groups them using a greedy clustering approach with a similarity threshold.
    """
    
    def __init__(
        self,
        similarity_threshold: Optional[float] = None,
        embedding_model: Optional[str] = None,
    ):
        """
        Initialize the clustering engine.
        
        Args:
            similarity_threshold: Minimum cosine similarity to group pain points (0-1).
                                  Higher = stricter matching. Uses settings default if None.
            embedding_model: OpenAI embedding model to use. Uses settings default if None.
        """
        self.similarity_threshold = similarity_threshold or EMBEDDING_SIMILARITY_THRESHOLD
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model or EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY,
        )
        self.embedding_calls = 0
    
    def cluster(self, pain_points: list[PainPoint]) -> list[PainPointCluster]:
        """
        Cluster pain points by semantic similarity.
        
        Args:
            pain_points: List of extracted pain points from all sources.
            
        Returns:
            List of clusters, sorted by total engagement (descending).
        """
        if not pain_points:
            return []
        
        logger.info(f"Clustering {len(pain_points)} pain points...")
        
        # Get embeddings for all pain points
        texts = [pp.problem for pp in pain_points]
        embeddings = self._get_embeddings(texts)
        
        if embeddings is None:
            # Fallback: each pain point is its own cluster
            logger.warning("Embedding failed, falling back to no clustering")
            return self._fallback_clusters(pain_points)
        
        # Greedy clustering
        clusters = self._greedy_cluster(pain_points, embeddings)
        
        # Sort by total engagement
        clusters.sort(key=lambda c: c.total_engagement, reverse=True)
        
        logger.info(f"Created {len(clusters)} clusters from {len(pain_points)} pain points")
        self._log_cluster_stats(clusters)
        
        return clusters
    
    def _get_embeddings(self, texts: list[str]) -> Optional[np.ndarray]:
        """Get embeddings for a list of texts."""
        try:
            # Batch embed
            result = self.embeddings.embed_documents(texts)
            self.embedding_calls += 1
            return np.array(result)
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return None
    
    def _greedy_cluster(
        self,
        pain_points: list[PainPoint],
        embeddings: np.ndarray,
    ) -> list[PainPointCluster]:
        """
        Greedy clustering: assign each point to the most similar existing cluster,
        or create a new cluster if no match above threshold.
        """
        clusters: list[PainPointCluster] = []
        cluster_embeddings: list[np.ndarray] = []  # Centroid of each cluster
        
        for i, pp in enumerate(pain_points):
            emb = embeddings[i]
            
            # Find best matching cluster
            best_cluster_idx = -1
            best_similarity = 0.0
            
            for j, centroid in enumerate(cluster_embeddings):
                similarity = self._cosine_similarity(emb, centroid)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_cluster_idx = j
            
            if best_similarity >= self.similarity_threshold and best_cluster_idx >= 0:
                # Add to existing cluster
                clusters[best_cluster_idx].add_pain_point(pp)
                # Update centroid (running average)
                n = len(clusters[best_cluster_idx].pain_points)
                cluster_embeddings[best_cluster_idx] = (
                    cluster_embeddings[best_cluster_idx] * (n - 1) + emb
                ) / n
            else:
                # Create new cluster
                new_cluster = PainPointCluster(representative=pp.problem)
                new_cluster.add_pain_point(pp)
                clusters.append(new_cluster)
                cluster_embeddings.append(emb.copy())
        
        # Update representative to be the highest-engagement pain point in each cluster
        for cluster in clusters:
            if cluster.pain_points:
                best_pp = max(cluster.pain_points, key=lambda p: p.engagement)
                cluster.representative = best_pp.problem
        
        return clusters
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def _fallback_clusters(self, pain_points: list[PainPoint]) -> list[PainPointCluster]:
        """Fallback: each pain point becomes its own cluster."""
        clusters = []
        for pp in pain_points:
            cluster = PainPointCluster(representative=pp.problem)
            cluster.add_pain_point(pp)
            clusters.append(cluster)
        return clusters
    
    def _log_cluster_stats(self, clusters: list[PainPointCluster]):
        """Log clustering statistics."""
        multi_source = sum(1 for c in clusters if c.source_count > 1)
        avg_size = sum(len(c.pain_points) for c in clusters) / len(clusters) if clusters else 0
        
        logger.info(f"  Multi-source clusters: {multi_source}/{len(clusters)}")
        logger.info(f"  Average cluster size: {avg_size:.1f}")
        
        # Log top 3 clusters
        for i, c in enumerate(clusters[:3]):
            sources = ", ".join(f"{s}({v})" for s, v in c.source_breakdown.items())
            logger.info(f"  Top {i+1}: '{c.representative[:50]}...' [{sources}]")
    
    def get_usage_stats(self) -> dict:
        """Get embedding API usage statistics."""
        return {
            "embedding_calls": self.embedding_calls,
        }
