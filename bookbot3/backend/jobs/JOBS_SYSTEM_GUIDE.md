# BookBot Backend Jobs System: A Developer's Guide

This guide provides a comprehensive overview of the backend jobs system in BookBot. This system is responsible for handling long-running, asynchronous tasks like generating content with LLMs, creating book foundations, and exporting files. Understanding this system is crucial for adding new background features and debugging existing ones.

## Core Components

The jobs system is built around two main components:

1.  **`Job` and `JobLog` Models**: SQLAlchemy models (`backend/models/__init__.py`) that persist job information and their logs to the database.
2.  **`JobProcessor`**: A background thread (`backend/jobs/__init__.py`) that polls the database for new jobs, executes them, and manages their lifecycle.

---

## Job Lifecycle and States

A job progresses through several states, which are stored in the `Job.state` column:

-   **`waiting`**: The initial state of a job after it's created. The `JobProcessor` looks for jobs in this state to execute.
-   **`running`**: The state set by the `JobProcessor` just before it executes the job's main logic. The `started_at` timestamp is also set at this time.
-   **`completed`**: The job's `execute()` method finished successfully (returned `True`). This is a terminal state.
-   **`failed`**: The job's `execute()` method finished gracefully but reported a failure (returned `False`). This is a terminal state. An error message may be provided in `Job.error_message`.
-   **`error`**: The job's execution was aborted due to an unhandled exception. The exception details are stored in `Job.error_message`. This is a terminal state.
-   **`cancelled`**: The job was manually cancelled before it could be completed. This is a terminal state.

When a job reaches any terminal state (`completed`, `failed`, `error`, `cancelled`), its `completed_at` timestamp is set.

---

## The JobProcessor

The `JobProcessor` is the heart of the system.

### How it Works

1.  **Initialization**: The processor is started by `start_job_processor(app)` when the Flask application starts. It runs in a dedicated background thread.
2.  **Polling**: It periodically polls the database (every 1 second by default) for jobs in the `waiting` state.
3.  **Execution**: For each waiting job, it calls the internal `_process_job` method.
4.  **Lifecycle Management**: The `_process_job` method is responsible for the entire lifecycle of a single job run:
    -   It sets the job state to `running` and commits this change immediately.
    -   It instantiates the correct job class based on `job.job_type`.
    -   It calls the `execute()` method of the job instance within a `try...except...finally` block.
    -   Based on the return value (`True`/`False`) or any exceptions, it determines the final state (`completed`/`failed`/`error`).
    -   Crucially, it handles all database commits and rollbacks.

### Transaction Management: The Golden Rule

**Individual job logic (i.e., the `execute` method or any functions it calls) MUST NOT contain `db.session.commit()` or `db.session.rollback()`.**

All transaction management is centralized in the `JobProcessor._process_job`'s `finally` block. This ensures that the job's final state, logs, and `completed_at` timestamp are committed reliably and atomically, preventing partial updates or inconsistent states.

---

## Job Types and Classes

Jobs are implemented as classes that inherit from `BaseJob`.

-   **`BaseJob`**: The abstract base class for all jobs. It provides:
    -   `self.job`: The SQLAlchemy `Job` model instance.
    -   `self.log(message, level)`: A method to create `JobLog` entries associated with the job.
-   **`BookJob` / `ChunkJob`**: Convenience subclasses that automatically lock the associated book or chunk when the job starts.
-   **Function-based Jobs**: For simpler jobs like `create_foundation`, the "job class" is a thin wrapper (`CreateFoundationJob`) that calls a standalone function (`run_create_foundation_job`). This function receives a `log_callback` which is a reference to the `BaseJob.log` method.

---

## Creating a New Job Type

Follow these steps to add a new background job:

### 1. Create the Job Logic

Create a new Python file in `backend/jobs/` for your job's logic. Define a class that inherits from `BaseJob` (or a more specific subclass like `BookJob`).

```python
# backend/jobs/my_new_job.py
from . import BaseJob

class MyNewJob(BaseJob):
    def execute(self) -> bool:
        """
        Main logic for the job.
        Return True for success, False for failure.
        Raise an exception for a critical error.
        """
        try:
            self.log("Starting my new job!")
            
            # ... do work ...
            
            if some_condition_fails:
                self.log("Something went wrong, but we handled it.", level='ERROR')
                self.job.error_message = "A specific, user-friendly error message."
                return False

            self.log("My new job finished successfully.")
            return True

        except Exception as e:
            # This will be caught by the JobProcessor
            self.log(f"A critical error occurred: {e}", level='ERROR')
            raise # Re-raise the exception
```

### 2. Register the Job Type

In `backend/jobs/__init__.py`, find the `get_job_processor` function and register your new job class.

```python
# backend/jobs/__init__.py

def get_job_processor():
    """Get the global job processor instance."""
    global _job_processor
    if _job_processor is None:
        _job_processor = JobProcessor()
        # ... other registrations ...
        from backend.jobs.my_new_job import MyNewJob # <--- Import your class
        _job_processor.register('my_new_job', MyNewJob) # <--- Register it
    return _job_processor
```

### 3. Create the Job

From anywhere in the application (e.g., an API endpoint), use the `create_job` function to add a new job to the queue.

```python
from backend.jobs import create_job

# In an API endpoint or other service
def start_my_new_job_endpoint(book_id):
    # ...
    job_props = {'some_parameter': 'value'}
    new_job = create_job(
        book_id=book_id,
        job_type='my_new_job', # Must match the string used in register()
        props=job_props
    )
    return {'message': 'Job started', 'job_id': new_job.job_id}
```

The `JobProcessor` will automatically pick up and execute your job on its next polling cycle.
