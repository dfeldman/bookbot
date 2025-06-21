"""
LLM Picker module for BookBot.

This module provides utilities for selecting and managing LLMs for different job types.
It includes a catalog of available LLMs and their configuration, as well as utilities
for selecting the most appropriate LLM for a specific job based on book preferences.
"""

from .models import LLMInfo, LLMGroup
from .catalog import get_llm_by_id, get_llms_by_group, get_all_llms

from .api import llmpicker_api

__all__ = [
    'LLMInfo',
    'LLMGroup',
    'get_llm_by_id',
    'get_llms_by_group',
    'get_all_llms',
    'llmpicker_api',
]
