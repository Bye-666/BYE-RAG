"""Ingestion pipeline orchestration."""

from pathlib import Path
from typing import List, Callable, Optional
from .types import Document, Chunk
from .loaders.base import BaseLoader
from .batch_processor import BatchProcessor
from .storage.vector_upserter import VectorUpserter
from ..libs.splitter.base import BaseSplitter
from .transformers import ChunkRefiner, MetadataEnricher, ImageCaptioner
from ..trace.trace_context import TraceContext, get_trace_recorder


class IngestionPipeline:
    """Orchestrate the complete ingestion process.

    Flow: Load → Split → Transform → Process → Upsert
    """

    def __init__(
        self,
        loader: BaseLoader,
        splitter: BaseSplitter,
        batch_processor: BatchProcessor,
        vector_upserter: VectorUpserter,
        batch_size: int = 32,
        chunk_refiner: Optional[ChunkRefiner] = None,
        metadata_enricher: Optional[MetadataEnricher] = None,
        image_captioner: Optional[ImageCaptioner] = None,
        enable_transform: bool = True
    ):
        """Initialize IngestionPipeline.

        Args:
            loader: Document loader
            splitter: Text splitter
            batch_processor: Batch vector processor
            vector_upserter: Vector store upserter
            batch_size: Batch size for processing
            chunk_refiner: Optional chunk refinement transformer
            metadata_enricher: Optional metadata enrichment transformer
            image_captioner: Optional image captioning transformer
            enable_transform: Enable transformation step (default: True)
        """
        self.loader = loader
        self.splitter = splitter
        self.batch_processor = batch_processor
        self.vector_upserter = vector_upserter
        self.batch_size = batch_size
        self.chunk_refiner = chunk_refiner
        self.metadata_enricher = metadata_enricher
        self.image_captioner = image_captioner
        self.enable_transform = enable_transform

    def ingest_file(
        self,
        file_path: str | Path,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        enable_trace: bool = True
    ) -> dict:
        """Ingest single file.

        Args:
            file_path: Path to file
            progress_callback: Optional callback(stage, current, total)
            enable_trace: Enable tracing (default: True)

        Returns:
            Ingestion result summary
        """
        file_path = Path(file_path)

        # Create trace context
        trace = TraceContext("ingestion", f"ingest_file:{file_path.name}") if enable_trace else None

        try:
            if trace:
                trace.start()
                trace.add_step("start", {"file_path": str(file_path)})

            # Step 1: Load document
            if progress_callback:
                progress_callback("loading", 0, 1)

            document = self.loader.load(file_path)

            if trace:
                trace.add_step("load", {
                    "doc_id": document.id,
                    "text_length": len(document.text)
                })

            if progress_callback:
                progress_callback("loading", 1, 1)

            # Step 2: Split into chunks
            if progress_callback:
                progress_callback("splitting", 0, 1)

            chunks = self._split_document(document)

            if trace:
                trace.add_step("split", {"chunk_count": len(chunks)})

            if progress_callback:
                progress_callback("splitting", 1, 1)

            # Step 3: Transform chunks (optional)
            if self.enable_transform:
                if progress_callback:
                    progress_callback("transforming", 0, len(chunks))

                chunks = self._transform_chunks(chunks, document)

                if trace:
                    trace.add_step("transform", {"chunk_count": len(chunks)})

                if progress_callback:
                    progress_callback("transforming", len(chunks), len(chunks))

            # Step 4: Process in batches
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

            if trace:
                trace.add_step("upsert", {
                    "chunks_processed": total_chunks,
                    "chunks_uploaded": processed
                })

            result = {
                "success": True,
                "file": str(file_path),
                "chunks_processed": total_chunks,
                "chunks_uploaded": processed
            }

            if trace:
                trace.finish(result)
                get_trace_recorder().record(trace)

            return result

        except Exception as e:
            if trace:
                trace.error = str(e)
                trace.finish({"success": False, "error": str(e)})
                get_trace_recorder().record(trace)

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

    def _transform_chunks(self, chunks: List[Chunk], document: Document) -> List[Chunk]:
        """Apply transformations to chunks.

        Args:
            chunks: Chunks to transform
            document: Original document (for context)

        Returns:
            Transformed chunks
        """
        # Step 1: Refine chunks (clean formatting, fix boundaries)
        if self.chunk_refiner:
            chunks = self.chunk_refiner.refine_batch(chunks)

        # Step 2: Enrich metadata (extract keywords, topics, summary)
        if self.metadata_enricher:
            chunks = self.metadata_enricher.enrich_batch(chunks)

        # Step 3: Caption images (if document contains images)
        if self.image_captioner and document.metadata.get("images"):
            chunks = self._caption_images(chunks, document.metadata["images"])

        return chunks

    def _caption_images(self, chunks: List[Chunk], images: List[dict]) -> List[Chunk]:
        """Add image captions to chunks.

        Args:
            chunks: Text chunks
            images: List of image metadata dicts with 'path' key

        Returns:
            Chunks with image captions added
        """
        if not images:
            return chunks

        # Generate captions for all images
        image_paths = [img.get("path") for img in images if img.get("path")]

        if not image_paths:
            return chunks

        try:
            captions = self.image_captioner.caption_batch(image_paths)

            # Add captions to chunk metadata
            for chunk in chunks:
                chunk.metadata["image_captions"] = [
                    cap["caption"] for cap in captions if cap.get("captioning_success")
                ]
        except Exception as e:
            # Log error but don't fail the pipeline
            for chunk in chunks:
                chunk.metadata["image_captioning_error"] = str(e)

        return chunks
