"""Tests for ImageStorage."""

import pytest
from pathlib import Path

from src.ingestion.storage.image_storage import ImageStorage


@pytest.fixture
def storage(tmp_path):
    """Create ImageStorage with temporary database."""
    db_path = tmp_path / "test_images.db"
    return ImageStorage(str(db_path))


def test_image_storage_instantiation(tmp_path):
    """ImageStorage can be instantiated."""
    db_path = tmp_path / "images.db"
    storage = ImageStorage(str(db_path))
    assert storage.db_path == db_path
    assert db_path.exists()


def test_add_image(storage):
    """Add image to index."""
    result = storage.add_image(
        image_id="img-1",
        file_path="/path/to/image.jpg",
        doc_id="doc-1",
        page_num=5
    )
    
    assert result is True


def test_add_image_with_caption(storage):
    """Add image with caption."""
    result = storage.add_image(
        image_id="img-1",
        file_path="/path/to/image.jpg",
        caption="A test image"
    )
    
    assert result is True


def test_add_image_with_metadata(storage):
    """Add image with metadata."""
    metadata = {"width": 800, "height": 600, "format": "jpg"}
    
    result = storage.add_image(
        image_id="img-1",
        file_path="/path/to/image.jpg",
        metadata=metadata
    )
    
    assert result is True


def test_get_image(storage):
    """Retrieve image by ID."""
    storage.add_image(
        image_id="img-1",
        file_path="/path/to/image.jpg",
        doc_id="doc-1",
        page_num=3,
        caption="Test image"
    )
    
    image = storage.get_image("img-1")
    
    assert image is not None
    assert image["image_id"] == "img-1"
    assert image["file_path"] == "/path/to/image.jpg"
    assert image["doc_id"] == "doc-1"
    assert image["page_num"] == 3
    assert image["caption"] == "Test image"


def test_get_image_not_found(storage):
    """Return None for nonexistent image."""
    image = storage.get_image("nonexistent")
    assert image is None


def test_get_image_with_metadata(storage):
    """Retrieve image with metadata."""
    metadata = {"size": 1024}
    storage.add_image(
        image_id="img-1",
        file_path="/path/to/image.jpg",
        metadata=metadata
    )
    
    image = storage.get_image("img-1")
    
    assert image["metadata"] == metadata


def test_get_images_by_doc(storage):
    """Get all images for a document."""
    storage.add_image("img-1", "/path/1.jpg", doc_id="doc-1", page_num=1)
    storage.add_image("img-2", "/path/2.jpg", doc_id="doc-1", page_num=2)
    storage.add_image("img-3", "/path/3.jpg", doc_id="doc-2", page_num=1)
    
    images = storage.get_images_by_doc("doc-1")
    
    assert len(images) == 2
    assert images[0]["image_id"] == "img-1"
    assert images[1]["image_id"] == "img-2"


def test_get_images_by_doc_ordered_by_page(storage):
    """Images ordered by page number."""
    storage.add_image("img-1", "/path/1.jpg", doc_id="doc-1", page_num=3)
    storage.add_image("img-2", "/path/2.jpg", doc_id="doc-1", page_num=1)
    storage.add_image("img-3", "/path/3.jpg", doc_id="doc-1", page_num=2)
    
    images = storage.get_images_by_doc("doc-1")
    
    assert images[0]["page_num"] == 1
    assert images[1]["page_num"] == 2
    assert images[2]["page_num"] == 3


def test_get_images_by_doc_empty(storage):
    """Return empty list for document with no images."""
    images = storage.get_images_by_doc("nonexistent-doc")
    assert images == []


def test_delete_image(storage):
    """Delete image from index."""
    storage.add_image("img-1", "/path/to/image.jpg")
    
    result = storage.delete_image("img-1")
    
    assert result is True
    assert storage.get_image("img-1") is None


def test_delete_nonexistent_image(storage):
    """Delete nonexistent image succeeds."""
    result = storage.delete_image("nonexistent")
    assert result is True


def test_count_images(storage):
    """Count total images."""
    assert storage.count() == 0
    
    storage.add_image("img-1", "/path/1.jpg")
    storage.add_image("img-2", "/path/2.jpg")
    
    assert storage.count() == 2


def test_replace_existing_image(storage):
    """Replace existing image updates data."""
    storage.add_image("img-1", "/path/old.jpg", caption="Old caption")
    storage.add_image("img-1", "/path/new.jpg", caption="New caption")
    
    image = storage.get_image("img-1")
    
    assert image["file_path"] == "/path/new.jpg"
    assert image["caption"] == "New caption"
    assert storage.count() == 1  # Still only one image


def test_add_multiple_images_same_doc(storage):
    """Add multiple images for same document."""
    for i in range(5):
        storage.add_image(f"img-{i}", f"/path/{i}.jpg", doc_id="doc-1")
    
    images = storage.get_images_by_doc("doc-1")
    assert len(images) == 5


def test_image_created_at_timestamp(storage):
    """Image has created_at timestamp."""
    storage.add_image("img-1", "/path/to/image.jpg")
    
    image = storage.get_image("img-1")
    
    assert "created_at" in image
    assert image["created_at"] is not None
