"""
LLM catalog management for BookBot.

This module handles loading and querying the LLM catalog from a JSON file.
"""
import json
import os
import logging
from typing import List, Dict, Optional, Any, Union
from pathlib import Path

from .models import LLMInfo, LLMGroup

logger = logging.getLogger(__name__)

# Path to the LLM catalog JSON file
_CATALOG_PATH = Path(os.path.dirname(__file__)) / "llms.json"

# In-memory cache of LLM catalog
_llm_cache: Optional[List[LLMInfo]] = None


def _load_llm_catalog() -> List[LLMInfo]:
    """
    Load the LLM catalog from the JSON file.
    
    Returns:
        List of LLMInfo objects representing available LLMs.
    """
    global _llm_cache
    
    if _llm_cache is not None:
        return _llm_cache
    
    try:
        with open(_CATALOG_PATH, 'r') as f:
            llm_data = json.load(f)
        
        # Parse each LLM entry into an LLMInfo object
        _llm_cache = [LLMInfo(**item) for item in llm_data]
        logger.info(f"Loaded {len(_llm_cache)} LLM models from catalog")
        return _llm_cache
    except FileNotFoundError:
        logger.error(f"LLM catalog file not found at {_CATALOG_PATH}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing LLM catalog: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading LLM catalog: {e}")
        return []


def get_all_llms() -> List[LLMInfo]:
    """
    Get all LLMs in the catalog.
    
    Returns:
        List of LLMInfo objects representing all available LLMs.
    """
    return _load_llm_catalog()


def get_llms_by_group(group: Union[str, LLMGroup]) -> List[LLMInfo]:
    """
    Get LLMs that are valid for the specified group.
    
    Args:
        group: Group name or LLMGroup enum value.
    
    Returns:
        List of LLMInfo objects valid for the specified group.
    """
    if isinstance(group, LLMGroup):
        group = group.value
    
    llms = _load_llm_catalog()
    return [llm for llm in llms if group in llm.groups or "all" in llm.groups]


def get_llm_by_id(llm_id: str) -> Optional[LLMInfo]:
    """
    Get an LLM by its ID.
    
    Args:
        llm_id: The ID of the LLM to retrieve.
    
    Returns:
        LLMInfo object if found, None otherwise.
    """
    llms = _load_llm_catalog()
    for llm in llms:
        if llm.id == llm_id:
            return llm
    return None


# Re-export – canonical selector lives in utils
from backend.llmpicker.utils import select_llm_for_job  # noqa: F401
