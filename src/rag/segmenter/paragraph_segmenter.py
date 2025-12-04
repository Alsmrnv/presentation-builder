from .segmenter import Segmenter
import nltk

class ParagraphSegmenter(Segmenter):
    def __init__(self, data: str, min_sentences: int = 5):
        super().__init__(data)
        self.min_sentences = min_sentences
    
    def split(self) -> list[str]:
        paragraphs = self.data.split('\n\n')
        
        cleaned_paragraphs = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph and not paragraph.isspace():
                cleaned_paragraphs.append(paragraph)
        
        merged_paragraphs = []
        for paragraph in cleaned_paragraphs:
            sentences = nltk.sent_tokenize(paragraph)
            
            if (len(merged_paragraphs) > 0 and 
                len(sentences) < self.min_sentences):
                merged_paragraphs[-1] += "\n" + paragraph
            else:
                merged_paragraphs.append(paragraph)
        
        return merged_paragraphs