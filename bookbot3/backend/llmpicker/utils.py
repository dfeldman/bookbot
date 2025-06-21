"""
LLM picker utility functions.

This module provides utilities for integrating LLM selection with the job system.
"""
import inspect
import importlib
import logging
from typing import Dict, List, Optional, Any, Type

from backend.models import Book, Job


from .models import LLMDefaults, LLMGroup
from .catalog import get_llm_by_id, get_llms_by_group

logger = logging.getLogger(__name__)

# Mapping of job types to their implementation modules
JOB_TYPE_MODULES = {
    'generate_text': 'backend.jobs.generate_text',
    'create_foundation': 'backend.jobs.create_foundation',
    # Add other job types as needed
}


def get_job_class(job_type: str) -> Optional[Type]:
    """
    Get the class for a job type.
    
    Args:
        job_type: The job type to get the class for.
    
    Returns:
        The job class if found, None otherwise.
    """
    if job_type not in JOB_TYPE_MODULES:
        logger.warning(f"No module mapping for job type: {job_type}")
        return None
    
    module_path = JOB_TYPE_MODULES[job_type]
    
    try:
        module = importlib.import_module(module_path)
        
        # Look for a class that matches the job type in CamelCase
        job_class_name = ''.join(word.capitalize() for word in job_type.split('_')) + 'Job'
        job_class = getattr(module, job_class_name, None)
        
        if job_class is None:
            logger.warning(f"No job class found for job type: {job_type}")
            return None
        
        return job_class
    except ImportError:
        logger.error(f"Could not import module for job type: {job_type}")
        return None
    except Exception as e:
        logger.error(f"Error getting job class for job type {job_type}: {e}")
        return None


def get_fallback_llm_group(job_type: str) -> str:
    """
    Get the fallback LLM group for a job type if no explicit group is defined.
    
    Args:
        job_type: The job type to get the fallback group for.
    
    Returns:
        The fallback LLM group.
    """
    # Default mappings based on job type
    default_mappings = {
        'generate_text': LLMGroup.WRITER.value,
        'edit_text': LLMGroup.EDITOR.value,
        'review_text': LLMGroup.REVIEWER.value,
        'create_foundation': LLMGroup.THINKER.value,
    }
    
    return default_mappings.get(job_type, LLMGroup.THINKER.value)  # Default to thinker if unknown


def get_allowed_llm_group(job_type: str) -> Optional[str]:
    """
    Get the allowed LLM group for a job type.
    
    Args:
        job_type: The job type to get the allowed group for.
    
    Returns:
        The allowed LLM group if found, None otherwise.
    """
    job_class = get_job_class(job_type)
    if job_class is None:
        return None
    
    # Check if the job class has an allowed_llm_group class attribute
    allowed_group = getattr(job_class, 'allowed_llm_group', None)
    
    # Fallback to defaults based on job type if not defined
    if allowed_group is None:
        allowed_group = get_fallback_llm_group(job_type)
    
    return allowed_group


def select_llm_for_job(job: Job) -> Optional[str]:
    """
    Select the appropriate LLM for a job based on its type and book preferences.
    
    Args:
        job: The job to select an LLM for.
    
    Returns:
        The ID of the selected LLM if found, None otherwise.
    """
    book = Book.query.filter_by(book_id=job.book_id).first()
    if not book:
        logger.error(f"Book not found for job {job.job_id}")
        return None
    
    # Get book LLM preferences
    book_props = book.props or {}
    llm_defaults_dict = book_props.get('llm_defaults', {})
    llm_defaults = LLMDefaults.from_dict(llm_defaults_dict)
    
    # Check if there's an override LLM set
    if llm_defaults.override:
        logger.info(f"Using override LLM {llm_defaults.override} for job {job.job_id}")
        return llm_defaults.override
    
    # Get allowed LLM group for this job type
    allowed_group = get_allowed_llm_group(job.job_type)
    if not allowed_group:
        logger.warning(f"Could not determine allowed LLM group for job type: {job.job_type}")
        return None
    
    # Check if there's a job-specific LLM override in job props
    job_props = job.props or {}
    if job_props.get('llm_id'):
        llm_id = job_props.get('llm_id')
        llm = get_llm_by_id(llm_id)
        
        # Verify the LLM is valid for this group
        if llm and (allowed_group in llm.groups or 'all' in llm.groups):
            logger.info(f"Using job-specific LLM {llm_id} for job {job.job_id}")
            return llm_id
        else:
            logger.warning(f"Job-specific LLM {llm_id} is not valid for group {allowed_group}")
    
    # Get the book's default LLM for this group
    group_default = getattr(llm_defaults, allowed_group, None)
    if group_default:
        logger.info(f"Using book default LLM {group_default} for group {allowed_group}")
        return group_default
    
    # No default set, return the highest quality LLM for this group
    llms = get_llms_by_group(allowed_group)
    if llms:
        best_llm = max(llms, key=lambda llm: llm.quality_score)
        logger.info(f"No default set, using highest quality LLM {best_llm.id} for group {allowed_group}")
        return best_llm.id
    
    logger.warning(f"No suitable LLM found for job {job.job_id} with group {allowed_group}")
    return None
