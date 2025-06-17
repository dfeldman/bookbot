"""
Job processing system for BookBot.

This module provides the infrastructure for running background jobs
that can generate content, process books, and export files.
"""

import threading
import time
import traceback
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
        waiting_jobs = Job.query.filter_by(state='waiting').order_by(Job.created_at).all()
        
        for job in waiting_jobs:
            if not self.running:
                break
            
            try:
                self._process_job(job)
            except Exception as e:
                print(f"Error processing job {job.job_id}: {e}")
                self._log_job_error(job, str(e))
    
    def _process_job(self, job: Job):
        """Process a single job."""
        # Update job state to running
        job.state = 'running'
        job.started_at = datetime.utcnow()
        db.session.commit()
        
        # Create job instance
        job_class = self.job_types.get(job.job_type)
        if not job_class:
            raise ValueError(f"Unknown job type: {job.job_type}")
        
        job_instance = job_class(job)
        
        try:
            # Execute the job
            success = job_instance.execute()
            
            # Update job state
            job.state = 'complete' if success else 'error'
            job.completed_at = datetime.utcnow()
            
        except Exception as e:
            job.state = 'error'
            job.completed_at = datetime.utcnow()
            self._log_job_error(job, f"Job execution failed: {str(e)}")
            raise
        
        finally:
            # Unlock any locked resources
            self._unlock_job_resources(job)
            db.session.commit()
    
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
        model_mode = self.book.props.get('model_mode') if self.book else None
        llm_call = LLMCall(
            model="demo-model",
            api_key="demo-key",
            target_word_count=50,
            model_mode=model_mode,
            log_callback=self.log
        )
        
        if llm_call.execute():
            self.log(f"LLM call successful: {len(llm_call.output_text.split())} words generated")
            self.log(f"Cost: ${llm_call.cost}")
        else:
            self.log(f"LLM call failed: {llm_call.error_status}", 'ERROR')
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
