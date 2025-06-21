"""
Create Foundation Job class for BookBot.

This module provides a class wrapper for the create_foundation job functionality.
"""
from typing import Dict, Any, Optional, Callable
from backend.jobs.create_foundation import run_create_foundation_job


class CreateFoundationJob:
    """Class for creating foundation for a book."""
    
    # The allowed LLM group for this job type
    allowed_llm_group = "thinker"
    
    def __init__(self, job_id: str, props: Dict[str, Any], app_context=None):
        """
        Initialize the job.
        
        Args:
            job_id: The job ID
            props: Job properties
            app_context: Application context (if needed)
        """
        self.job_id = job_id
        self.props = props
        self.book_id = props.get('book_id')
        self.app_context = app_context
    
    def execute(self, callback: Optional[Callable] = None) -> bool:
        """
        Execute the job.
        
        Args:
            callback: Optional callback function for logging
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Default callback if none provided
        if callback is None:
            callback = lambda msg: None
        
        return run_create_foundation_job(
            job_id=self.job_id,
            book_id=self.book_id,
            props=self.props,
            log_callback=callback
        )
    
    # Alias for execute to maintain compatibility with job system
    run = execute
