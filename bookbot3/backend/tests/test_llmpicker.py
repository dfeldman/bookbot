"""
Tests for the LLM picker module.

This module contains tests for the LLM picker module, including catalog loading,
filtering, and selection logic.
"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock

from backend.llmpicker.catalog import (
    get_all_llms,
    get_llms_by_group,
    get_llm_by_id,
    select_llm_for_job,
    _load_llm_catalog
)
from backend.llmpicker.models import LLMGroup
from backend.llmpicker.utils import get_allowed_llm_group


# Sample test data
SAMPLE_LLMS = [
    {
        "id": "test-llm-1",
        "input_cost_per_mtok": 0.5,
        "output_cost_per_mtok": 1.5,
        "seconds_per_output_mtok": 100,
        "router": "openrouter",
        "name": "Test LLM 1",
        "description": "A test LLM for writers",
        "company": "Test Company",
        "context_length": 8000,
        "groups": ["writer", "thinker"],
        "quality_score": 8
    },
    {
        "id": "test-llm-2",
        "input_cost_per_mtok": 0.3,
        "output_cost_per_mtok": 0.9,
        "seconds_per_output_mtok": 80,
        "router": "openrouter",
        "name": "Test LLM 2",
        "description": "A test LLM for editors",
        "company": "Test Company",
        "context_length": 16000,
        "groups": ["editor", "reviewer"],
        "quality_score": 7
    },
    {
        "id": "test-llm-3",
        "input_cost_per_mtok": 0.1,
        "output_cost_per_mtok": 0.3,
        "seconds_per_output_mtok": 50,
        "router": "openrouter",
        "name": "Test LLM 3",
        "description": "A test LLM for all uses",
        "company": "Test Company",
        "context_length": 32000,
        "groups": ["all"],
        "quality_score": 5
    }
]


@pytest.fixture
def mock_catalog():
    """Fixture to mock the LLM catalog."""
    from backend.llmpicker.models import LLMInfo
    # Convert sample dict data to LLMInfo objects
    llm_objects = [LLMInfo(**item) for item in SAMPLE_LLMS]
    with patch('backend.llmpicker.catalog._load_llm_catalog') as mock_load:
        mock_load.return_value = llm_objects
        yield


def test_get_all_llms(mock_catalog):
    """Test getting all LLMs from the catalog."""
    llms = get_all_llms()
    assert len(llms) == 3
    assert llms[0].id == "test-llm-1"
    assert llms[1].id == "test-llm-2"
    assert llms[2].id == "test-llm-3"


def test_get_llms_by_group(mock_catalog):
    """Test getting LLMs filtered by group."""
    writer_llms = get_llms_by_group("writer")
    assert len(writer_llms) == 2  # test-llm-1 and test-llm-3 (all)
    assert writer_llms[0].id == "test-llm-1"
    assert writer_llms[1].id == "test-llm-3"
    
    editor_llms = get_llms_by_group("editor")
    assert len(editor_llms) == 2  # test-llm-2 and test-llm-3 (all)
    assert editor_llms[0].id == "test-llm-2"
    assert editor_llms[1].id == "test-llm-3"
    
    tagger_llms = get_llms_by_group("tagger")
    assert len(tagger_llms) == 1  # Only test-llm-3 (all)
    assert tagger_llms[0].id == "test-llm-3"


def test_get_llm_by_id(mock_catalog):
    """Test getting an LLM by ID."""
    llm = get_llm_by_id("test-llm-2")
    assert llm is not None
    assert llm.id == "test-llm-2"
    assert llm.name == "Test LLM 2"
    
    # Test missing LLM
    llm = get_llm_by_id("nonexistent-llm")
    assert llm is None


def test_select_llm_for_job(app):
    """Test selecting the appropriate LLM for a job."""
    # Mock book and job
    book = MagicMock()
    job = MagicMock()
    job.job_type = "generate_text"
    job.book_id = "test-book-123"
    job.props = {}

    # Mock DB query and group resolution
    with patch('backend.llmpicker.utils.Book.query') as mock_query, \
         patch('backend.llmpicker.utils.get_allowed_llm_group', return_value="writer"), \
         patch('backend.llmpicker.utils.get_llm_by_id') as mock_get_llm_by_id, \
         patch('backend.llmpicker.utils.get_llms_by_group') as mock_get_llms_by_group:

        mock_query.filter_by.return_value.first.return_value = book

        # --- Test Case 1: Book-level group default ---
        book.props = {"llm_defaults": {"writer": "test-llm-1"}}
        job.props = {}
        result = select_llm_for_job(job)
        assert result == "test-llm-1"

        # --- Test Case 2: Job-specific override (valid) ---
        # This should be used since there is no book-level override
        book.props = {"llm_defaults": {"writer": "test-llm-1"}}
        job.props = {"llm_id": "test-llm-valid-for-writer"}
        # Mock the returned LLM to be valid for the group
        mock_llm = MagicMock()
        mock_llm.groups = ["writer"]
        mock_get_llm_by_id.return_value = mock_llm
        result = select_llm_for_job(job)
        assert result == "test-llm-valid-for-writer"
        mock_get_llm_by_id.assert_called_with("test-llm-valid-for-writer")

        # --- Test Case 3: Job-specific override (invalid group) ---
        # Should be ignored, fallback to book group default
        job.props = {"llm_id": "test-llm-invalid-for-writer"}
        mock_llm_invalid = MagicMock()
        mock_llm_invalid.groups = ["editor"]
        mock_get_llm_by_id.return_value = mock_llm_invalid
        result = select_llm_for_job(job)
        assert result == "test-llm-1" # Falls back to group default
        mock_get_llm_by_id.assert_called_with("test-llm-invalid-for-writer")

        # --- Test Case 4: Book-level override ---
        # This should take precedence over everything else
        book.props = {
            "llm_defaults": {
                "writer": "test-llm-1",
                "override": "test-llm-override"
            }
        }
        job.props = {"llm_id": "test-llm-valid-for-writer"}
        result = select_llm_for_job(job)
        assert result == "test-llm-override"

        # --- Test Case 5: Fallback to highest quality ---
        # No overrides, no defaults
        book.props = {"llm_defaults": {}}
        job.props = {}
        from backend.llmpicker.models import LLMInfo
        # test-llm-1 has quality 8, test-llm-3 has quality 5. Both are in 'writer' group (via 'all').
        writer_llms = [llm for llm in SAMPLE_LLMS if "writer" in llm["groups"] or "all" in llm["groups"]]
        mock_get_llms_by_group.return_value = [LLMInfo(**llm) for llm in writer_llms]
        result = select_llm_for_job(job)
        assert result == "test-llm-1"
        mock_get_llms_by_group.assert_called_with("writer")


def test_allowed_llm_group_resolution():
    """Test resolving allowed LLM group from job class."""
    # We need to mock the job_type as a string, not pass a MagicMock
    job_type = "generate_text"
    
    # Mock the job class to be returned
    mock_job_class = MagicMock()
    mock_job_class.allowed_llm_group = "writer"
    
    with patch('backend.llmpicker.utils.get_job_class') as mock_get_class, \
         patch('backend.llmpicker.utils.get_fallback_llm_group', return_value='thinker'):
        
        # Set up the mock to return our job class
        mock_get_class.return_value = mock_job_class
        
        # Call the function with a string job type
        from backend.llmpicker.utils import get_allowed_llm_group
        result = get_allowed_llm_group(job_type)
        
        # Verify the result
        assert result == "writer"
    
    # Test missing attribute fallback
    job_type = "create_foundation"  # Different job type
    mock_job_class2 = MagicMock()
    mock_job_class2.allowed_llm_group = None  # No specific group
    
    with patch('backend.llmpicker.utils.get_job_class') as mock_get_class, \
         patch('backend.llmpicker.utils.get_fallback_llm_group') as mock_fallback:
        
        # Set up the mock to return our second job class without an attribute
        mock_get_class.return_value = mock_job_class2
        mock_fallback.return_value = "thinker"
        
        # Call function with string job type
        result = get_allowed_llm_group(job_type)
        
        # Verify fallback logic worked
        assert result == "thinker"
