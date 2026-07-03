"""BM25 sparse vector encoding."""

import math
import pickle
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any


class BM25SparseEncoder:
    """BM25 sparse vector encoder.
    
    Converts traditional BM25 algorithm output into sparse vector format
    compatible with Milvus sparse vector index.
    
    BM25 formula: score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avgdl))
    where:
    - idf: inverse document frequency
    - tf: term frequency in document
    - dl: document length
    - avgdl: average document length
    - k1: term frequency saturation parameter (default: 1.5)
    - b: length normalization parameter (default: 0.75)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """Initialize BM25SparseEncoder.
        
        Args:
            k1: Term frequency saturation parameter (1.2-2.0)
            b: Length normalization parameter (0-1)
        """
        self.k1 = k1
        self.b = b
        self.vocab: Dict[str, int] = {}  # term -> term_id mapping
        self.idf: Dict[int, float] = {}  # term_id -> idf value
        self.avgdl: float = 0  # average document length
        self.doc_count: int = 0  # total number of documents

    def fit(self, documents: List[str]):
        """Train on document collection to build vocabulary and IDF.
        
        Args:
            documents: List of text documents
        """
        if not documents:
            raise ValueError("Cannot fit on empty document list")
        
        doc_lengths = []
        term_doc_freq = Counter()  # count documents containing each term
        
        # Count term frequencies and document lengths
        for doc in documents:
            terms = self._tokenize(doc)
            doc_lengths.append(len(terms))
            unique_terms = set(terms)
            
            # Assign ID to new terms
            for term in unique_terms:
                if term not in self.vocab:
                    self.vocab[term] = len(self.vocab)
                term_doc_freq[term] += 1
        
        self.doc_count = len(documents)
        self.avgdl = sum(doc_lengths) / self.doc_count if self.doc_count > 0 else 0
        
        # Calculate IDF: log((N - df + 0.5) / (df + 0.5) + 1)
        for term, term_id in self.vocab.items():
            df = term_doc_freq[term]
            idf_value = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)
            self.idf[term_id] = idf_value

    def encode(self, text: str) -> Dict[str, List]:
        """Encode text into sparse vector.
        
        Args:
            text: Text to encode
            
        Returns:
            Sparse vector in Milvus format: {"indices": [...], "values": [...]}
        """
        if not self.vocab:
            raise RuntimeError("Encoder not fitted. Call fit() first.")
        
        terms = self._tokenize(text)
        term_freq = Counter(terms)
        doc_len = len(terms)
        
        indices = []
        values = []
        
        for term, tf in term_freq.items():
            if term in self.vocab:
                term_id = self.vocab[term]
                idf_value = self.idf[term_id]
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                score = idf_value * (numerator / denominator)
                
                indices.append(term_id)
                values.append(score)
        
        # Return Milvus sparse vector format
        return {"indices": indices, "values": values}

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into terms.
        
        Simple whitespace splitting for prototype.
        Production should use jieba or other professional tokenizers.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of terms
        """
        return text.lower().split()

    def save(self, path: str | Path):
        """Persist vocabulary and IDF to disk.
        
        Args:
            path: Path to save file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'wb') as f:
            pickle.dump({
                'vocab': self.vocab,
                'idf': self.idf,
                'avgdl': self.avgdl,
                'doc_count': self.doc_count,
                'k1': self.k1,
                'b': self.b
            }, f)

    @classmethod
    def load(cls, path: str | Path) -> 'BM25SparseEncoder':
        """Load trained encoder from disk.
        
        Args:
            path: Path to saved encoder file
            
        Returns:
            Loaded encoder instance
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Encoder file not found: {path}")
        
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        encoder = cls(k1=data['k1'], b=data['b'])
        encoder.vocab = data['vocab']
        encoder.idf = data['idf']
        encoder.avgdl = data['avgdl']
        encoder.doc_count = data['doc_count']
        return encoder
