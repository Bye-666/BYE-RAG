"""Image file storage and indexing."""

import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional


class ImageStorage:
    """Manage image file storage and metadata indexing.
    
    Uses SQLite to index image locations and metadata,
    while images themselves remain as files on disk.
    """

    def __init__(self, db_path: str = "data/db/image_index.db"):
        """Initialize ImageStorage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                image_id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                doc_id TEXT,
                page_num INTEGER,
                caption TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()

    def add_image(self, image_id: str, file_path: str, doc_id: str = None,
                  page_num: int = None, caption: str = None,
                  metadata: Dict[str, Any] = None) -> bool:
        """Add image to index.
        
        Args:
            image_id: Unique image identifier
            file_path: Path to image file
            doc_id: Associated document ID
            page_num: Page number in document
            caption: Image caption/description
            metadata: Additional metadata (stored as JSON string)
            
        Returns:
            True if successful
        """
        import json
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO images 
                (image_id, file_path, doc_id, page_num, caption, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (image_id, file_path, doc_id, page_num, caption, metadata_json))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Failed to add image {image_id}: {e}")
            return False

    def get_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve image metadata by ID.
        
        Args:
            image_id: Image identifier
            
        Returns:
            Image metadata dictionary, or None if not found
        """
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT image_id, file_path, doc_id, page_num, caption, metadata, created_at
            FROM images WHERE image_id = ?
        """, (image_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "image_id": row[0],
            "file_path": row[1],
            "doc_id": row[2],
            "page_num": row[3],
            "caption": row[4],
            "metadata": json.loads(row[5]) if row[5] else None,
            "created_at": row[6]
        }

    def get_images_by_doc(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get all images for a document.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            List of image metadata dictionaries
        """
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT image_id, file_path, doc_id, page_num, caption, metadata, created_at
            FROM images WHERE doc_id = ?
            ORDER BY page_num
        """, (doc_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "image_id": row[0],
                "file_path": row[1],
                "doc_id": row[2],
                "page_num": row[3],
                "caption": row[4],
                "metadata": json.loads(row[5]) if row[5] else None,
                "created_at": row[6]
            }
            for row in rows
        ]

    def delete_image(self, image_id: str) -> bool:
        """Delete image from index.
        
        Args:
            image_id: Image identifier
            
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM images WHERE image_id = ?", (image_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Failed to delete image {image_id}: {e}")
            return False

    def count(self) -> int:
        """Count total images in index.
        
        Returns:
            Number of images
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM images")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
