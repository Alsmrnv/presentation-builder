from dotenv import load_dotenv
import os

from rag.slide_gen.slide_generation import create_presentation_plan
from rag.segmenter.window_segmenter import WindowSegmenter

text = "your text"

def main():
    load_dotenv()

    OPENROUTER_API_KEY = os.getenv("API_KEY")

    segmenter = WindowSegmenter(text)

    chunks = segmenter.split()
    
    slides = create_presentation_plan(chunks, OPENROUTER_API_KEY)
    
    print(f"Number of slides: {len(slides)}")
    
    for i, slide in enumerate(slides):
        print(f"\n--- Slide {i+1} ---")
        print(f"Title: {slide.get('title', 'No title')}")
        print(f"Description: {slide.get('description', 'No description')}")


if __name__ == "__main__":
    main()