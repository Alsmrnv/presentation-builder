from sentence_transformers import SentenceTransformer
import torch

from .retriever import Retriever

class SimpleRetriever(Retriever):
    def __init__(self, segments: list[str]):
        super().__init__(segments)
        device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model = SentenceTransformer('ai-forever/FRIDA', device=device)

        search_segments = [f"search_document: {seg}" for seg in self.segments]
        self.segments_embeddings = self.model.encode(search_segments, convert_to_tensor=True)

    def retrieve_relevant_segments(self, slides: list[str], limit=5) -> list[str]:
        if len(self.segments) == 1:
            return [self.segments[0]]

        search_query = [f"slide number {i + 1} name: {q}" for (i, q) in enumerate(slides)]
        query_embeddings = self.model.encode(search_query, convert_to_tensor=True)

        relevant_slide_segments = []

        i = 1
        for query_embedding in query_embeddings:
            sim_scores = (query_embedding @ self.segments_embeddings.T).squeeze(0)
            _, topk_indices = torch.topk(sim_scores, k=limit)
            top_segments = " ".join([self.segments[i] for i in topk_indices])
            print(f"{i}:", top_segments, '\n')
            i += 1
            relevant_slide_segments.append(top_segments)

        return relevant_slide_segments

    def clear(self):
        del self.model
        torch.cuda.empty_cache()
