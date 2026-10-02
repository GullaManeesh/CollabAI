from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Tuple, Dict

# Setup character splitter as per 05-AGENTS-AND-RAG.md Part 2
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=["\n\n", "\n", ". ", " ", ""],
)

def chunk_document_pages(pages_data: List[Tuple[int, str]]) -> List[Dict]:
    """
    Chunks document pages and returns a list of dictionaries with keys:
    'text', 'page', 'chunk_index'
    """
    chunks_out = []
    chunk_idx = 0
    
    for page_num, text in pages_data:
        # Split text of individual page
        split_texts = splitter.split_text(text)
        
        for segment in split_texts:
            clean_segment = segment.strip()
            if not clean_segment:
                continue
                
            chunks_out.append({
                "text": clean_segment,
                "page": page_num,
                "chunk_index": chunk_idx
            })
            chunk_idx += 1
            
    return chunks_out
