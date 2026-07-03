"""Ingestion pipeline orchestration."""

from pathlib import Path
from typing import List, Callable, Optional
from .types import Document, Chunk
from .loaders.base import BaseLoader
from .batch_processor import BatchProcessor
from .storage.vector_upserter import VectorUpserter
from ..libs.splitter.base import BaseSplitter


class IngestionPipeline:
    """Orchestrate the complete ingestion process.
    
    Flow: Load → Split → Process → Upsert
    """

    def __init__(
        self,
        loader: BaseLoader,
        splitter: BaseSplitter,
        batch_processor: BatchProcessor,
        vector_upserter: VectorUpserter,
        batch_size: int = 32
    ):
        """Initialize IngestionPipeline.
        
        Args:
            loader: Document loader
            splitter: Text splitter
            batch_processor: Batch vector processor
            vector_upserter: Vector store upserter
            batch_size: Batch size for processing
        """
        self.loader = loader
        self.splitter = splitter
        self.batch_processor = batch_processor
        self.vector_upserter = vector_upserter
        self.batch_size = batch_size

    def ingest_file(
        self,
        file_path: str | Path,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> dict:
        """Ingest single file.
        
        Args:
            file_path: Path to file
            progress_callback: Optional callback(stage, current, total)
            
        Returns:
            Ingestion result summary
        """
        file_path = Path(file_path)
        
        try:
            # Step 1: Load document
            if progress_callback:
                progress_callback("loading", 0, 1)
            
            document = self.loader.load(file_path)
            
            if progress_callback:
                progress_callback("loading", 1, 1)
            
            # Step 2: Split into chunks
            if progress_callback:
                progress_callback("splitting", 0, 1)
            
            chunks = self._split_document(document)
            
            if progress_callback:
                progress_callback("splitting", 1, 1)
            
            # Step 3: Process in batches
            total_chunks = len(chunks)
            processed = 0
            
            for i in range(0, total_chunks, self.batch_size):
                batch = chunks[i:i + self.batch_size]
                
                if progress_callback:
                    progress_callback("processing", processed, total_chunks)
                
                # Generate vectors
                records = self.batch_processor.process_batch(batch)
                
                # Upload to vector store
                success_count = self.vector_upserter.upsert_batch(records)
                
                processed += len(batch)
                
                if progress_callback:
                    progress_callback("processing", processed, total_chunks)
            
            return {
                "success": True,
                "file": str(file_path),
                "chunks_processed": total_chunks,
                "chunks_uploaded": processed
            }
            
        except Exception as e:
            return {
                "success": False,
                "file": str(file_path),
                "error": str(e)
            }

    def ingest_files(
        self,
        file_paths: List[str | Path],
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> dict:
        """Ingest multiple files.
        
        Args:
            file_paths: List of file paths
            progress_callback: Optional callback(stage, current, total)
            
        Returns:
            Batch ingestion summary
        """
        total_files = len(file_paths)
        results = []
        
        for i, file_path in enumerate(file_paths):
            if progress_callback:
                progress_callback("file", i, total_files)
            
            result = self.ingest_file(file_path)
            results.append(result)
            
            if progress_callback:
                progress_callback("file", i + 1, total_files)
        
        # Summarize results
        successful = sum(1 for r in results if r["success"])
        total_chunks = sum(r.get("chunks_processed", 0) for r in results if r["success"])
        
        return {
            "total_files": total_files,
            "successful": successful,
            "failed": total_files - successful,
            "total_chunks": total_chunks,
            "results": results
        }

    def _split_document(self, document: Document) -> List[Chunk]:
        """Split document into chunks.
        
        Args:
            document: Document to split
            
        Returns:
            List of chunks
        """
        # Split text
        text_chunks = self.splitter.split(document.text)
        
        # Convert to Chunk objects
        chunks = []
        for i, text in enumerate(text_chunks):
            chunk = Chunk(
                id=f"{document.id}_chunk_{i}",
                text=text,
                doc_id=document.id,
                chunk_index=i,
                metadata={
                    **document.metadata,
                    "chunk_index": i,
                    "total_chunks": len(text_chunks)
                }
            )
            chunks.append(chunk)
        
        return chunks
