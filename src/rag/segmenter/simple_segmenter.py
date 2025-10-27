import nltk
from nltk.tokenize import sent_tokenize
from .segmenter import Segmenter

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')


class SimpleSegmenter(Segmenter):
    def __init__(self, data: str):
        super().__init__(data)

    def split(self) -> list[str]:
        return sent_tokenize(self.data)