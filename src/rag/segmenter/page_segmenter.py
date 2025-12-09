import nltk
from nltk.tokenize import sent_tokenize
from .segmenter import Segmenter

class PageSegmenter(Segmenter):
    def __init__(self, data: str):
        super().__init__(data)

    def split(self) -> list[str]:
        page_size_chars=2500
        overlap=100

        chunks = []
        start = 0
        
        while start < len(self.data):
            end = start + page_size_chars
            window = self.data[start:end]
            
            last_period = window.rfind('.')
            if last_period > page_size_chars * 0.8: 
                window = window[:last_period + 1]
                end = start + len(window)
            
            chunks.append(window)
            start = end - overlap

            offs = self.data[start:].find('.')
            if (offs < overlap):
                start += offs + 1
        
        return chunks