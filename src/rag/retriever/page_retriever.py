from sentence_transformers import SentenceTransformer
import torch

from .retriever import Retriever

class PageRetriever(Retriever):
    def __init__(self, segments: list[str]):
        super().__init__(segments)
        device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model = SentenceTransformer('ai-forever/FRIDA', device=device)

        search_segments = [f"search_document: {seg}" for seg in self.segments]
        self.segments_embeddings = self.model.encode(search_segments, convert_to_tensor=True)

    def retrieve_relevant_segments(self, slides: list[dict], limit=2) -> list[str]:
        if len(self.segments) == 1:
            return [self.segments[0] for i in range(len(slides))]

        search_queries = []
        for i, slide in enumerate(slides):
            title = slide.get('title', '')
            description = slide.get('description', '')

            query_text = f"Назавние: {title}. Описание: {description}".strip()
            search_queries.append(f"Слайд номер {i + 1}: {query_text}")

        query_embeddings = self.model.encode(search_queries, convert_to_tensor=True)

        relevant_slide_segments = []

        for i, (slide, query_embedding) in enumerate(zip(slides, query_embeddings)):
            sim_scores = (query_embedding @ self.segments_embeddings.T).squeeze(0)
            _, topk_indices = torch.topk(sim_scores, k=limit)
            top_segments = " ".join([self.segments[idx] for idx in sorted(topk_indices.tolist())])
            
            relevant_slide_segments.append(top_segments)

        return relevant_slide_segments

    def clear(self):
        del self.model
        torch.cuda.empty_cache()