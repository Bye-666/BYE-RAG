"""BM25 sparse vector encoding."""

import math
import pickle
import hashlib
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
        self.term_doc_freq: Dict[str, int] = {}  # term -> document frequency (for incremental updates)
        self.total_doc_length: float = 0  # sum of all document lengths (for avgdl calculation)
        self.doc_hashes: set = set()  # document content hashes for deduplication
        self._incremental_stats_available: bool = True  # whether incremental stats are reliable

    def fit(self, documents: List[str]):
        """Train on document collection to build vocabulary and IDF.

        This method resets all state and trains from scratch.
        For incremental updates, use partial_fit() instead.

        Args:
            documents: List of text documents
        """
        if not documents:
            raise ValueError("Cannot fit on empty document list")

        # Reset all state
        self.vocab = {}
        self.idf = {}
        self.term_doc_freq = {}
        self.total_doc_length = 0
        self.doc_count = 0
        self.avgdl = 0
        self.doc_hashes = set()

        doc_lengths = []
        term_doc_freq = Counter()  # count documents containing each term

        # Count term frequencies and document lengths
        for doc in documents:
            # Compute document hash for deduplication
            doc_hash = hashlib.sha256(doc.encode('utf-8')).hexdigest()
            if doc_hash in self.doc_hashes:
                continue  # Skip duplicate document
            self.doc_hashes.add(doc_hash)

            terms = self._tokenize(doc)
            doc_lengths.append(len(terms))
            unique_terms = set(terms)

            # Assign ID to new terms
            for term in unique_terms:
                if term not in self.vocab:
                    self.vocab[term] = len(self.vocab)
                term_doc_freq[term] += 1

        self.doc_count = len(doc_lengths)
        self.avgdl = sum(doc_lengths) / self.doc_count if self.doc_count > 0 else 0
        self.total_doc_length = sum(doc_lengths)
        self.term_doc_freq = dict(term_doc_freq)

        # Calculate IDF: log((N - df + 0.5) / (df + 0.5) + 1)
        for term, term_id in self.vocab.items():
            df = term_doc_freq[term]
            idf_value = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)
            self.idf[term_id] = idf_value

    def partial_fit(self, documents: List[str]):
        """Incrementally update vocabulary and IDF with new documents.

        This method allows adding new documents without retraining from scratch.
        New terms are added to vocabulary, and IDF values are recalculated for all terms.
        Duplicate documents (by content hash) are automatically skipped.

        Args:
            documents: List of new text documents to add

        Returns:
            int: Number of new (non-duplicate) documents processed

        Raises:
            RuntimeError: If incremental stats are not available (loaded from old pickle format)
        """
        if not self._incremental_stats_available:
            raise RuntimeError(
                "Incremental update not available: this encoder was loaded from an old pickle format "
                "without term_doc_freq and doc_hashes. Please retrain from scratch using fit() with "
                "all documents, or delete the old encoder file and re-ingest all documents."
            )

        if not documents:
            return 0

        # Process new documents
        new_doc_lengths = []
        new_term_doc_freq = Counter()
        skipped_count = 0

        for doc in documents:
            # Compute document hash for deduplication
            doc_hash = hashlib.sha256(doc.encode('utf-8')).hexdigest()
            if doc_hash in self.doc_hashes:
                skipped_count += 1
                continue  # Skip duplicate document
            self.doc_hashes.add(doc_hash)

            terms = self._tokenize(doc)
            new_doc_lengths.append(len(terms))
            unique_terms = set(terms)

            # Add new terms to vocabulary and update document frequency
            for term in unique_terms:
                if term not in self.vocab:
                    self.vocab[term] = len(self.vocab)
                new_term_doc_freq[term] += 1

        if not new_doc_lengths:
            return 0  # All documents were duplicates

        # Update statistics
        self.doc_count += len(new_doc_lengths)
        self.total_doc_length += sum(new_doc_lengths)
        self.avgdl = self.total_doc_length / self.doc_count if self.doc_count > 0 else 0

        # Merge new term document frequencies with existing ones
        for term, df in new_term_doc_freq.items():
            self.term_doc_freq[term] = self.term_doc_freq.get(term, 0) + df

        # Recalculate IDF for all terms with updated document count
        for term, term_id in self.vocab.items():
            df = self.term_doc_freq.get(term, 0)
            idf_value = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)
            self.idf[term_id] = idf_value

        return len(new_doc_lengths)

    def encode(self, text: str) -> Dict[int, float]:
        """Encode text into sparse vector.

        Args:
            text: Text to encode

        Returns:
            Sparse vector in Milvus Lite format: {term_id: score, ...}
        """
        if not self.vocab:
            raise RuntimeError("Encoder not fitted. Call fit() first.")

        terms = self._tokenize(text)
        term_freq = Counter(terms)
        doc_len = len(terms)

        sparse_vector = {}

        for term, tf in term_freq.items():
            if term in self.vocab:
                term_id = self.vocab[term]
                idf_value = self.idf[term_id]

                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                score = idf_value * (numerator / denominator)

                # Milvus Lite 格式：dict[int, float]
                sparse_vector[int(term_id)] = float(score)

        return sparse_vector

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into terms.

        Uses jieba for Chinese text segmentation.
        Falls back to whitespace splitting for non-Chinese text.

        Args:
            text: Text to tokenize

        Returns:
            List of terms
        """
        # 尝试使用 jieba 进行中文分词
        try:
            import jieba
            # jieba 分词，返回词语列表
            terms = list(jieba.cut(text))
            # 过滤空字符串和单字符（保留多字词）
            terms = [term.strip() for term in terms if term.strip() and len(term.strip()) > 1]
            return terms
        except ImportError:
            # jieba 未安装，使用空格分词
            print("[WARNING] jieba not installed, using whitespace tokenization. Install with: pip install jieba")
            return text.split()

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
                'b': self.b,
                'term_doc_freq': self.term_doc_freq,
                'total_doc_length': self.total_doc_length,
                'doc_hashes': self.doc_hashes
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

        # Check if this is an old pickle format without incremental stats
        has_term_doc_freq = 'term_doc_freq' in data
        has_doc_hashes = 'doc_hashes' in data

        if has_term_doc_freq and has_doc_hashes:
            # New format: full incremental stats available
            encoder.term_doc_freq = data['term_doc_freq']
            encoder.total_doc_length = data['total_doc_length']
            encoder.doc_hashes = data['doc_hashes']
            encoder._incremental_stats_available = True
        else:
            # Old format: missing incremental stats
            encoder.term_doc_freq = {}
            encoder.total_doc_length = encoder.avgdl * encoder.doc_count
            encoder.doc_hashes = set()
            encoder._incremental_stats_available = False
            print("[WARNING] Loaded BM25 encoder from old format without incremental stats.")
            print("          Incremental updates (partial_fit) are disabled.")
            print("          To enable incremental updates, retrain from scratch:")
            print("          1. Delete data/db/bm25_encoder.pkl")
            print("          2. Re-run ingestion on all documents")

        return encoder

    def clone(self) -> 'BM25SparseEncoder':
        """Create a deep copy of this encoder.

        Returns:
            New encoder instance with copied state
        """
        cloned = BM25SparseEncoder(k1=self.k1, b=self.b)
        cloned.vocab = self.vocab.copy()
        cloned.idf = self.idf.copy()
        cloned.avgdl = self.avgdl
        cloned.doc_count = self.doc_count
        cloned.term_doc_freq = self.term_doc_freq.copy()
        cloned.total_doc_length = self.total_doc_length
        cloned.doc_hashes = self.doc_hashes.copy()
        cloned._incremental_stats_available = self._incremental_stats_available
        return cloned

        # Check if this is an old pickle format without incremental stats
        has_term_doc_freq = 'term_doc_freq' in data
        has_doc_hashes = 'doc_hashes' in data

        if has_term_doc_freq and has_doc_hashes:
            # New format: full incremental stats available
            encoder.term_doc_freq = data['term_doc_freq']
            encoder.total_doc_length = data['total_doc_length']
            encoder.doc_hashes = data['doc_hashes']
            encoder._incremental_stats_available = True
        else:
            # Old format: missing incremental stats
            encoder.term_doc_freq = {}
            encoder.total_doc_length = encoder.avgdl * encoder.doc_count
            encoder.doc_hashes = set()
            encoder._incremental_stats_available = False
            print("[WARNING] Loaded BM25 encoder from old format without incremental stats.")
            print("          Incremental updates (partial_fit) are disabled.")
            print("          To enable incremental updates, retrain from scratch:")
            print("          1. Delete data/db/bm25_encoder.pkl")
            print("          2. Re-run ingestion on all documents")

        return encoder
