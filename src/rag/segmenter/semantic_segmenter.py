from transformers import AutoTokenizer
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from typing import List
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
from sklearn.metrics.pairwise import cosine_distances
from tqdm import tqdm

from .segmenter import Segmenter

class SemanticSegmenter(Segmenter):
    def __init__(self, data: str, model_name: str = 'ai-forever/FRIDA'):
        super().__init__(data)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = SentenceTransformer(model_name)

    def split(self) -> List[str]:
        sentences = sent_tokenize(self.data)

        chunks = []
        batch_size = 500

        for i in tqdm(range(0, len(sentences), batch_size), desc="split"):
            batch_sentences = sentences[i:i + batch_size]
            embeddings = self.get_sentence_embeddings(batch_sentences)
            batch_clusters = self.cluster_sentences(batch_sentences, embeddings)
            batch_chunks = self.merge_clusters(batch_clusters)
            chunks.extend(batch_chunks)

        return chunks

    def get_sentence_embeddings(self, sentences: List[str]) -> np.ndarray:
        embeddings = self.model.encode(sentences, convert_to_tensor=False)

        return embeddings

    def cluster_sentences(self, sentences: List[str], embeddings: np.ndarray,
                          threshold: float = 0.7) -> List[List[str]]:
        if len(sentences) <= 3:
            return [sentences]

        # cosine_sim = np.dot(embeddings, embeddings.T)

        # distance = 1 - cosine_sim

        distance = cosine_distances(embeddings)

        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=threshold,
            metric='precomputed',
            linkage='average'
        )

        labels = clustering.fit_predict(distance)

        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(sentences[i])

        return list(clusters.values())

    def merge_clusters(self, clusters: List[List[str]]) -> List[str]:
        chunks = []

        for cluster in tqdm(clusters, desc="Merge clasters"):
            chunk = " ".join(cluster)
            if len(chunk) > 500:
                sentences = cluster
                current_part = []
                current_length = 0

                for sentence in sentences:
                    if current_length + len(sentence) > 500 and current_part:
                        chunks.append(" ".join(current_part))
                        current_part = [sentence]
                        current_length = len(sentence)
                    else:
                        current_part.append(sentence)
                        current_length += len(sentence)

                if current_part:
                    chunks.append(" ".join(current_part))
            else:
                chunks.append(chunk)

        return chunks