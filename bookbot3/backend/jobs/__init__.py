"""
Job processing system for BookBot.

This module provides the infrastructure for running background jobs
that can generate content, process books, and export files.
"""

import threading
import time
import traceback
import json # Added json import
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from abc import ABC, abstractmethod

from backend.models import db, Job, JobLog, Book, Chunk
from backend.llm import LLMCall, get_api_token_status


# job processor implementation
class JobProcessor:
    """Main job processor that runs in a background thread."""

    def __init__(self, poll_interval: float = 1.0):
        """
        Initialize the job processor.
        
        Args:
            poll_interval: How often to check for new jobs (seconds)
        """
        self.poll_interval = poll_interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.app = None  # Flask app instance
        
        # Registry of job types
        self.job_types: Dict[str, type] = {}

    def register(self, job_type, job_cls):
        """Register a job type with the processor."""
        self.job_types[job_type] = job_cls

    def start(self, app=None):
        """Start the job processor in a background thread."""
        if self.running:
            return
        
        self.app = app
        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("Job processor started")

    def stop(self):
        """Stop the job processor."""
        if not self.running:
            return
        
        self.running = False
        self._stop_event.set()
        if self.thread:
            self.thread.join(timeout=5.0)
        print("Job processor stopped")

    def _run(self):
        """Main job processing loop."""
        while self.running and not self._stop_event.is_set():
            try:
                if self.app:
                    with self.app.app_context():
                        self._process_waiting_jobs()
                else:
                    print("Warning: Job processor running without Flask app context")
            except Exception as e:
                print(f"Error in job processor: {e}")
                traceback.print_exc()
            
            # Wait for next poll or stop signal
            self._stop_event.wait(self.poll_interval)

    def _process_waiting_jobs(self):
        """Process all waiting jobs."""
        # Get waiting jobs
        # Querying outside the loop means if a job fails and rolls back,
        # subsequent operations in the same app_context might be affected if not handled perfectly.
        # However, each _process_job is now designed to be more self-contained.
        waiting_jobs_query = Job.query.filter(Job.state.in_(['waiting', 'running_retry'])) # Added running_retry for potential future use
        waiting_jobs_query = waiting_jobs_query.order_by(Job.created_at)
        # Fetch all jobs upfront. If the list is huge, consider processing in batches.
        waiting_jobs = waiting_jobs_query.all()

        for job_from_query in waiting_jobs:
            if not self.running or self._stop_event.is_set(): # Check stop event
                break
            
            current_job_id = job_from_query.job_id # For logging if job_from_query becomes detached

            # Each job processing is wrapped in its own try/except.
            # _process_job is now designed to handle its own errors and commits/rollbacks robustly.
            # So, an exception escaping _process_job here would be highly unexpected and critical.
            try:
                self._process_job(job_from_query)
            except Exception as e:
                # This block is a "should never happen" safety net if _process_job itself has an unrecoverable error
                # that prevents it from managing the session or its own state.
                print(f"CRITICAL UNHANDLED ERROR: Exception escaped _process_job for job {current_job_id}: {e}. Trace: {traceback.format_exc()}")
                try:
                    db.session.rollback() # Ensure session is clean before trying to mark job as error.
                    # Attempt to fetch the job by ID and mark as error, as a last resort.
                    job_to_fail_critically = db.session.get(Job, current_job_id)
                    if job_to_fail_critically and job_to_fail_critically.state not in ['complete', 'error', 'cancelled']:
                        job_to_fail_critically.state = 'error'
                        job_to_fail_critically.completed_at = datetime.utcnow()
                        # Commit error state before logging
                        db.session.commit()
                        
                        # Simplified logging to avoid relying on job_instance methods
                        log_entry = JobLog(
                            job_id=current_job_id,
                            book_id=job_to_fail_critically.book_id if job_to_fail_critically.book_id else 'Unknown',
                            log_level='CRITICAL',
                            log_entry=f"Job failed in _process_waiting_jobs top-level safety net: {str(e)}. Trace: {traceback.format_exc()}"
                        )
                        db.session.add(log_entry)
                        db.session.commit()
                except Exception as final_error_handling_e:
                    print(f"ULTRA CRITICAL: Failed to update job {current_job_id} to error state in _process_waiting_jobs safety net after unhandled error. Final error: {final_error_handling_e}. Trace: {traceback.format_exc()}")
                    db.session.rollback() # Rollback this attempt too.

    def _process_job(self, job: Job):
        """Process a single job."""
        original_job_id = job.job_id
        job_instance = None # Define for broader scope in case of instantiation error logging

        try:
            # Ensure job is part of the current session for updates
            job = db.session.merge(job)

            job.state = 'running'
            job.started_at = datetime.utcnow()
            db.session.commit() # Commit 'running' state

            # Create job instance - this can fail
            job_class = self.job_types.get(job.job_type)
            if not job_class:
                raise ValueError(f"Unknown job type: {job.job_type} for job ID {original_job_id}")
            
            job_instance = job_class(job) # Instantiation can fail (e.g. ChunkJob init)
            
            # job_instance.execute() is expected to manage its own transaction
            # for final state (complete/error) if it doesn't raise an exception.
            # GenerateTextJob.execute now does this.
            job_instance.execute()
            # If execute() completes without error, it should have set and committed
            # the final job state. No explicit commit here by _process_job for that.

        except Exception as e:
            # An exception here means:
            # 1. 'running' state commit failed (unlikely to be caught here due to structure)
            # 2. Job instantiation (job_class or job_instance=job_class(job)) failed.
            # 3. job_instance.execute() failed critically and did not manage its own error state.
            # The session might be dirty.
            db.session.rollback()
            try:
                # Re-fetch the job to ensure it's attachable for state update
                job_to_fail = db.session.get(Job, original_job_id)
                if job_to_fail:
                    job_to_fail.state = 'error'
                    job_to_fail.completed_at = datetime.utcnow()
                    # Commit the error state BEFORE logging, as _log_job_error also commits.
                    db.session.commit() 
                    error_details = f"Job execution/instantiation failed: {str(e)}. Trace: {traceback.format_exc()}"
                    self._log_job_error(job_to_fail, error_details) # This will do its own commit.
                else:
                    # This case is severe, means we can't even mark the job as failed.
                    print(f"CRITICAL: Job {original_job_id} not found after rollback to set error state. Original error: {e}")
            except Exception as inner_e:
                # If updating state to 'error' itself fails.
                print(f"CRITICAL: Failed to set job {original_job_id} to error state after initial error '{e}'. Inner error: {inner_e}. Trace: {traceback.format_exc()}")
                # Session is already rolled back from outer exception.
                # Avoid further db operations here as state is unknown.
            # Do not re-raise here; allow finally to run. The job state (if updated) is our record of failure.
            # The _process_waiting_jobs loop should continue with the next job.
        
        finally:
            # Unlock resources regardless of outcome.
            try:
                # Fetch by ID to ensure we have a valid session-bound object
                job_for_unlock = db.session.get(Job, original_job_id)
                if job_for_unlock:
                    self._unlock_job_resources(job_for_unlock) # Does not commit
                    db.session.commit() # Commit changes from unlocking
                else:
                     print(f"Warning: Job {original_job_id} not found for unlocking resources in finally block. State may be inconsistent.")
            except Exception as unlock_e:
                print(f"CRITICAL: Error during resource unlock for job {original_job_id}: {unlock_e}. Trace: {traceback.format_exc()}")
                db.session.rollback() # Rollback unlock attempt if it fails

    def _log_job_error(self, job: Job, error_message: str):
        """Log an error for a job."""
        log_entry = JobLog(
            job_id=job.job_id,
            log_entry=error_message,
            log_level='ERROR'
        )
        db.session.add(log_entry)
        db.session.commit()

    def _unlock_job_resources(self, job: Job):
        """Unlock any resources locked by this job."""
        # Unlock book if it's a book job
        if job.job_type in ['book_job', 'export_job']:  # Add more book job types as needed
            book = db.session.get(Book, job.book_id)
            if book and book.job == job.job_id:
                book.is_locked = False
                book.job = None
        
        # Unlock chunks if it's a chunk job
        chunks = db.session.query(Chunk).filter_by(job=job.job_id).all()
        for chunk in chunks:
            chunk.is_locked = False
            chunk.job = None

    def create_job_instance(self, job):
        """Create a job instance from a Job model."""
        cls = self.job_types.get(job.job_type)
        return cls(job) if cls else None


class BaseJob(ABC):
    """Base class for all job types."""
    
    def __init__(self, job: Job):
        """
        Initialize the job.
        
        Args:
            job: The Job model instance
        """
        self.job = job
        self.book = db.session.get(Book, job.book_id)
        self._cancelled = False
    
    def log(self, message: str, level: str = 'INFO'):
        """
        Log a message for this job.
        
        Args:
            message: The message to log
            level: The log level (INFO, WARNING, ERROR)
        """
        print(f"[{self.job.job_type}:{self.job.job_id[:8]}] {message}")
        
        log_entry = JobLog(
            job_id=self.job.job_id,
            log_entry=message,
            log_level=level
        )
        db.session.add(log_entry)
        db.session.commit()
    
    def is_cancelled(self) -> bool:
        """
        Check if the job has been cancelled.
        
        Returns:
            bool: True if the job should stop execution
        """
        # Refresh job state from database
        db.session.refresh(self.job)
        return self.job.state == 'cancelled' or self._cancelled
    
    def cancel(self):
        """Mark the job as cancelled."""
        self._cancelled = True
        self.job.state = 'cancelled'
        self.job.completed_at = datetime.utcnow()
        db.session.commit()
    
    @abstractmethod
    def execute(self) -> bool:
        """
        Execute the job.
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass


class ChunkJob(BaseJob):
    """Base class for jobs that operate on a specific chunk."""
    
    def __init__(self, job: Job):
        super().__init__(job)
        chunk_id = self.job.props.get('chunk_id')
        if not chunk_id:
            raise ValueError("ChunkJob requires chunk_id in props")
        
        self.chunk = db.session.query(Chunk).filter_by(
            chunk_id=chunk_id,
            is_latest=True,
            is_deleted=False
        ).first()
        
        if not self.chunk:
            raise ValueError(f"Chunk not found: {chunk_id}")
        
        # Lock the chunk
        self.chunk.is_locked = True
        self.chunk.job = self.job.job_id
        db.session.commit()


class BookJob(BaseJob):
    """Base class for jobs that operate on an entire book."""
    
    def __init__(self, job: Job):
        super().__init__(job)
        
        # Lock the book
        self.book.is_locked = True
        self.book.job = self.job.job_id
        db.session.commit()


class ExportJob(BaseJob):
    """Base class for jobs that export book content."""
    
    def __init__(self, job: Job):
        super().__init__(job)
        # Export jobs don't lock anything


class DemoJob(BaseJob):
    """Demo job for testing the job system."""
    
    def execute(self) -> bool:
        """Execute the demo job."""
        self.log("Starting demo job")
        
        # Simulate some work
        for i in range(5):
            if self.is_cancelled():
                self.log("Demo job cancelled")
                return False
            
            self.log(f"Demo job step {i + 1}/5")
            time.sleep(1)
        
        # Test LLM call
        self.log("Attempting to use the LLM...")

        # --- Parameters for LLM ---
        model_name = "fake-gpt-4-turbo"
        api_key_to_use = "test-key"  # or some other key for testing
        prompt_text = "Write a short story about a brave robot who discovers a hidden garden."
        system_prompt_text = "You are a master storyteller, known for your whimsical and heartwarming tales."
        target_words = 150
        other_llm_params = {"temperature": 0.75, "max_tokens": 250, "top_p": 0.9}

        # --- Log LLM Call Details ---
        api_key_log_message = "test-key" if api_key_to_use == "test-key" else "API key present (not 'test-key')"

        log_details = (
            f"LLM Call Details:\n"
            f"  Model: {model_name}\n"
            f"  API Key: {api_key_log_message}\n"
            f"  System Prompt: {system_prompt_text}\n"
            f"  Prompt: {prompt_text}\n"
            f"  Target Word Count: {target_words}\n"
            f"  Other Params: {json.dumps(other_llm_params)}"
        )
        self.log(log_details, level='LLM')  # Log before the call

        # --- Instantiate and Execute LLMCall ---
        llm_call = LLMCall(
            model=model_name,
            api_key=api_key_to_use,
            target_word_count=target_words,
            prompt=prompt_text,
            system_prompt=system_prompt_text,
            llm_params=other_llm_params,
            log_callback=lambda msg: self.log(f"LLM Sub-log: {msg}", level='DEBUG')
        )

        if llm_call.execute():
            self.log(f"LLM Output: {llm_call.output_text}", level='LLM')
            self.log(f"LLM execution successful. Cost: ${llm_call.cost:.6f}, Output Tokens: {llm_call.output_tokens}")
        else:
            self.log(f"LLM execution failed. Error: {llm_call.error_status}", level='ERROR')
            return False
        
        self.log("Demo job completed successfully")
        return True


class CreateFoundationJob(BookJob):
    """Job that creates the foundation for a book (outline, characters, settings, etc.)."""
    
    def execute(self) -> bool:
        """Execute the create foundation job."""
        from .create_foundation import run_create_foundation_job
        
        return run_create_foundation_job(
            job_id=self.job.job_id,
            book_id=self.job.book_id,
            props=self.job.props,
            log_callback=self.log
        )


# Global job processor instance
_job_processor = None

def get_job_processor():
    """Get the global job processor instance."""
    global _job_processor
    if _job_processor is None:
        _job_processor = JobProcessor()
        # Register job types
        from backend.jobs.generate_text import GenerateTextJob
        _job_processor.register('generate_text', GenerateTextJob)
        _job_processor.register('demo', DemoJob)
        _job_processor.register('create_foundation', CreateFoundationJob)
    return _job_processor

def start_job_processor(app):
    """Start the global job processor."""
    processor = get_job_processor()
    processor.start(app)

def stop_job_processor():
    """Stop the global job processor."""
    processor = get_job_processor()
    processor.stop()


def create_job(book_id: str, job_type: str, props: Dict[str, Any]) -> Job:
    """
    Create a new job.
    
    Args:
        book_id: The ID of the book this job is for
        job_type: The type of job to create
        props: Job-specific properties
    
    Returns:
        Job: The created job
    """
    job = Job(
        book_id=book_id,
        job_type=job_type,
        props=props,
        state='waiting'
    )
    
    db.session.add(job)
    db.session.commit()
    
    return job


def cancel_job(job_id: str) -> bool:
    """
    Cancel a job.
    
    Args:
        job_id: The ID of the job to cancel
    
    Returns:
        bool: True if the job was cancelled, False otherwise
    """
    job = db.session.get(Job, job_id)
    if not job:
        return False
    
    if job.state in ['waiting', 'running']:
        job.state = 'cancelled'
        job.completed_at = datetime.utcnow()
        db.session.commit()
        return True
    
    return False
