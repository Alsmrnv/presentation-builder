import nltk
from nltk.tokenize import sent_tokenize
from .segmenter import Segmenter

class PageSegmenter(Segmenter):
    def __init__(self, data: str):
        super().__init__(data)

    def split(self) -> list[str]:
        page_size_chars = 2100
        overlap = 90
        
        tables = self._extract_tables()
        
        chunks = []
        start = 0

        while start <= len(self.data):

            end = start + page_size_chars
            
            adjusted_end = self._adjust_cut_point(start, end, tables)
            
            if adjusted_end != end:
                end = adjusted_end
                window = self.data[start:end]
                start = end
            else:
                last_period = self.data[end:].find('.')
                if last_period != -1 and last_period < 1.5 * overlap:
                        end += last_period + 1
                
                window = self.data[start:end]

                start = end - overlap // 2
                first_period = self.data[:start].rfind('.')
                if first_period != -1 and (start - first_period) < overlap:
                    start = first_period + 1
                else:
                    start = end + 1

            chunks.append(window)
        
        if len(chunks) > 1 and len(chunks[-1]) <= 500:
            last_chunk = chunks.pop()
            chunks[-1] += last_chunk

        return chunks
    
    def _extract_tables(self) -> list[tuple[int, int]]:
        tables = []
        pos = 0
        
        while True:
            table_start = self.data.find('<table>', pos)
            if table_start == -1:
                break
                
            table_end = self.data.find('</table>', table_start)
            if table_end == -1:
                break
            
            table_end += len('</table>')

            image_start = self.data.find('[IMAGE_', table_end)

            if image_start == -1 or image_start - table_end > 18: # TODO mb not 18
                tables.append((table_start, table_end))
                pos = table_end
                continue
            
            image_end = self.data.find(']', image_start)

            if image_end == -1:
                tables.append((table_start, table_end))
                pos = table_end
                continue
            
            table_end = image_end + 1
            tables.append((table_start, table_end))
            pos = table_end
        
        return tables
    
    def _adjust_cut_point(self, start: int, proposed_end: int, tables: list[tuple[int, int]]) -> int:
        for table_start, table_end in tables:
            if table_start < proposed_end < table_end:
                return table_end
                
        return proposed_end