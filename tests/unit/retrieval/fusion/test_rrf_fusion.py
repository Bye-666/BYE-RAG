"""Tests for RRF Fusion."""

import pytest

from src.retrieval.fusion.rrf_fusion import RRFFusion


@pytest.fixture
def sample_dense_results():
    """Sample dense retrieval results."""
    return [
        {"id": "doc1", "text": "Result 1", "score": 0.95},
        {"id": "doc2", "text": "Result 2", "score": 0.85},
        {"id": "doc3", "text": "Result 3", "score": 0.75}
    ]


@pytest.fixture
def sample_sparse_results():
    """Sample sparse retrieval results."""
    return [
        {"id": "doc2", "text": "Result 2", "score": 2.5},
        {"id": "doc4", "text": "Result 4", "score": 2.0},
        {"id": "doc1", "text": "Result 1", "score": 1.5}
    ]


def test_rrf_fusion_instantiation():
    """RRFFusion can be instantiated."""
    fusion = RRFFusion()
    assert fusion.k == 60


def test_rrf_fusion_custom_k():
    """RRFFusion accepts custom k parameter."""
    fusion = RRFFusion(k=100)
    assert fusion.k == 100


def test_fuse_basic(sample_dense_results, sample_sparse_results):
    """Fuse dense and sparse results."""
    fusion = RRFFusion()

    fused = fusion.fuse(sample_dense_results, sample_sparse_results)

    # Should have unique documents
    assert len(fused) == 4
    assert all("rrf_score" in result for result in fused)


def test_fuse_combines_scores(sample_dense_results, sample_sparse_results):
    """RRF combines scores from both retrievers."""
    fusion = RRFFusion(k=60)

    fused = fusion.fuse(sample_dense_results, sample_sparse_results)

    # doc2 appears in both results (rank 2 in dense, rank 1 in sparse)
    # Should have higher combined score
    doc2_result = next(r for r in fused if r['id'] == 'doc2')

    # RRF score for doc2: 1/(60+2) + 1/(60+1) ≈ 0.0161 + 0.0164 = 0.0325
    assert doc2_result['rrf_score'] > 0.03


def test_fuse_orders_by_rrf_score(sample_dense_results, sample_sparse_results):
    """Fused results are ordered by RRF score."""
    fusion = RRFFusion()

    fused = fusion.fuse(sample_dense_results, sample_sparse_results)

    # Scores should be in descending order
    scores = [r['rrf_score'] for r in fused]
    assert scores == sorted(scores, reverse=True)


def test_fuse_with_overlapping_docs():
    """Fuse handles overlapping documents correctly."""
    dense = [
        {"id": "doc1", "text": "Text 1"},
        {"id": "doc2", "text": "Text 2"}
    ]
    sparse = [
        {"id": "doc2", "text": "Text 2"},
        {"id": "doc3", "text": "Text 3"}
    ]

    fusion = RRFFusion()
    fused = fusion.fuse(dense, sparse)

    # doc2 appears in both, should have highest score
    assert fused[0]['id'] == 'doc2'
    assert len(fused) == 3


def test_fuse_with_empty_dense():
    """Fuse with empty dense results."""
    sparse = [{"id": "doc1", "text": "Text 1"}]

    fusion = RRFFusion()
    fused = fusion.fuse([], sparse)

    assert len(fused) == 1
    assert fused[0]['id'] == 'doc1'


def test_fuse_with_empty_sparse():
    """Fuse with empty sparse results."""
    dense = [{"id": "doc1", "text": "Text 1"}]

    fusion = RRFFusion()
    fused = fusion.fuse(dense, [])

    assert len(fused) == 1
    assert fused[0]['id'] == 'doc1'


def test_fuse_with_both_empty():
    """Fuse with both empty."""
    fusion = RRFFusion()
    fused = fusion.fuse([], [])

    assert fused == []


def test_fuse_preserves_metadata():
    """Fuse preserves original hit information."""
    dense = [{"id": "doc1", "text": "Text 1", "metadata": {"key": "value"}}]
    sparse = [{"id": "doc2", "text": "Text 2", "extra": "data"}]

    fusion = RRFFusion()
    fused = fusion.fuse(dense, sparse)

    doc1 = next(r for r in fused if r['id'] == 'doc1')
    assert doc1['text'] == "Text 1"
    assert doc1['metadata'] == {"key": "value"}

    doc2 = next(r for r in fused if r['id'] == 'doc2')
    assert doc2['extra'] == "data"


def test_fuse_multiple_with_two_lists():
    """Fuse multiple with two lists."""
    list1 = [{"id": "doc1", "text": "Text 1"}]
    list2 = [{"id": "doc2", "text": "Text 2"}]

    fusion = RRFFusion()
    fused = fusion.fuse_multiple(list1, list2)

    assert len(fused) == 2


def test_fuse_multiple_with_three_lists():
    """Fuse multiple with three lists."""
    list1 = [{"id": "doc1", "text": "Text 1"}]
    list2 = [{"id": "doc2", "text": "Text 2"}]
    list3 = [{"id": "doc1", "text": "Text 1"}]  # Overlap with list1

    fusion = RRFFusion()
    fused = fusion.fuse_multiple(list1, list2, list3)

    # doc1 appears twice, should rank higher
    assert fused[0]['id'] == 'doc1'
    assert len(fused) == 2


def test_fuse_multiple_empty():
    """Fuse multiple with no lists."""
    fusion = RRFFusion()
    fused = fusion.fuse_multiple()

    assert fused == []


def test_fuse_multiple_single_list():
    """Fuse multiple with single list returns that list."""
    list1 = [{"id": "doc1", "text": "Text 1"}]

    fusion = RRFFusion()
    fused = fusion.fuse_multiple(list1)

    assert fused == list1


def test_rrf_formula_correctness():
    """RRF formula is calculated correctly."""
    fusion = RRFFusion(k=60)

    dense = [{"id": "doc1", "text": "Text"}]  # rank 1
    sparse = [{"id": "doc1", "text": "Text"}]  # rank 1

    fused = fusion.fuse(dense, sparse)

    # Expected: 1/(60+1) + 1/(60+1) = 2/61 ≈ 0.0328
    expected_score = 2 / 61
    assert abs(fused[0]['rrf_score'] - expected_score) < 0.0001
