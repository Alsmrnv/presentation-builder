class Retriever:
    def __init__(self, segments: list[str]):
        self.segments = segments

    def retrieve_relevant_segments(self, segments) -> list[str]:
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()
