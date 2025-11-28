import nltk
from nltk.tokenize import sent_tokenize
from .segmenter import Segmenter

class WindowSegmenter(Segmenter):
    def __init__(self, data: str):
        super().__init__(data)

    def split(self) -> list[str]:
        window_size_chars=15000
        overlap=1100

        chunks = []
        start = 0
        
        while start < len(text):
            end = start + window_size_chars
            window = text[start:end]
            
            last_period = window.rfind('.')
            if last_period > window_size_chars * 0.8: 
                window = window[:last_period + 1]
                end = start + len(window)
            
            chunks.append(window)
            start = end - overlap
            start = start + window[start:].rfind('.')
            # TODO if source document do not contain dots for some reason, use \n instead
        
        return chunks