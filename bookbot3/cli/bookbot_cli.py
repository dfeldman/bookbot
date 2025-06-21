#!/usr/bin/env python3
"""
BookBot CLI Tool

A comprehensive command-line interface for BookBot administration and debugging.
Supports all CRUD operations with admin API key authentication.
"""

import argparse
import json
import sys
import os
import requests
from typing import Dict, Any, Optional
from urllib.parse import urljoin


class BookBotCLI:
    """Command-line interface for BookBot operations."""
    
    def __init__(self, base_url: str = "http://localhost:5001", admin_key: Optional[str] = None, user_api_key: Optional[str] = None):
        """
        Initialize the CLI client.
        
        Args:
            base_url: Base URL of the BookBot server
            admin_key: Admin API key for authentication
            user_api_key: User API key for authentication (alternative to admin_key)
        """
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.admin_key = admin_key or os.environ.get('BOOKBOT_ADMIN_KEY')
        self.user_api_key = user_api_key or os.environ.get('BOOKBOT_USER_API_KEY')
        self.config_dir = os.path.expanduser('~/.bookbot')
        self.config_file = os.path.join(self.config_dir, 'config.json')
        
        # Load config if it exists
        self._load_config()
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json'
        })
        
        # Set authentication header based on available keys
        if self.admin_key:
            self.session.headers.update({'X-Admin-Key': self.admin_key})
        elif self.user_api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.user_api_key}'})
    
    def _load_config(self):
        """Load configuration from config file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                if not self.admin_key and 'admin_key' in config:
                    self.admin_key = config['admin_key']
                    
                if not self.user_api_key and 'user_api_key' in config:
                    self.user_api_key = config['user_api_key']
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
    
    def _save_config(self):
        """Save configuration to config file."""
        try:
            # Create config directory if it doesn't exist
            os.makedirs(self.config_dir, exist_ok=True)
            
            config = {}
            if self.admin_key:
                config['admin_key'] = self.admin_key
            if self.user_api_key:
                config['user_api_key'] = self.user_api_key
                
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            # Set secure permissions
            os.chmod(self.config_file, 0o600)
            print(f"✅ Saved configuration to {self.config_file}")
        except Exception as e:
            print(f"❌ Could not save config file: {e}")
            
    def set_api_key(self, api_key: str, is_admin: bool = False):
        """Set and save API key."""
        if is_admin:
            self.admin_key = api_key
            self.session.headers.update({'X-Admin-Key': api_key})
            if 'Authorization' in self.session.headers:
                del self.session.headers['Authorization']
        else:
            self.user_api_key = api_key
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
            if 'X-Admin-Key' in self.session.headers:
                del self.session.headers['X-Admin-Key']
        
        self._save_config()
        print(f"✅ {('Admin' if is_admin else 'User')} API key has been set")

    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an HTTP request to the API."""
        url = urljoin(self.api_url + '/', endpoint.lstrip('/'))
        
        # Set JSON headers only if we have JSON data
        if 'json' in kwargs or method in ['POST', 'PUT', 'PATCH']:
            kwargs.setdefault('headers', {})
            kwargs['headers']['Content-Type'] = 'application/json'
        
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            sys.exit(1)
    
    def _handle_response(self, response: requests.Response, success_message: str = None) -> Any:
        """Handle API response and return JSON data."""
        if response.status_code >= 400:
            try:
                error_data = response.json()
                print(f"❌ Error {response.status_code}: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"❌ Error {response.status_code}: {response.text}")
            sys.exit(1)
        
        if success_message:
            print(f"✅ {success_message}")
        
        try:
            return response.json()
        except:
            return None
    
    def health_check(self):
        """Check server health."""
        print("🏥 Checking server health...")
        response = self._make_request('GET', '/health')
        data = self._handle_response(response)
        
        print(f"Status: {data['status']}")
        print(f"Version: {data['version']}")
        print(f"Database: {data['database']}")
    
    def get_config(self):
        """Get server configuration."""
        print("⚙️ Getting server configuration...")
        response = self._make_request('GET', '/config')
        data = self._handle_response(response)
        
        for key, value in data.items():
            print(f"{key}: {value}")
    
    # Book operations
    def list_books(self):
        """List all books."""
        print("📚 Listing all books...")
        response = self._make_request('GET', '/books')
        data = self._handle_response(response)
        
        books = data.get('books', [])
        if not books:
            print("No books found.")
            return
        
        print(f"\nFound {len(books)} book(s):")
        for book in books:
            print(f"  📖 {book['book_id'][:8]}... - {book['props'].get('title', 'Untitled')}")
            print(f"     User: {book['user_id'][:8]}...")
            print(f"     Chunks: {book.get('chunk_count', 0)}, Words: {book.get('word_count', 0)}")
            print(f"     Created: {book['created_at']}")
            if book.get('is_locked'):
                print(f"     🔒 LOCKED (Job: {book.get('job', 'unknown')})")
            print()
    
    def get_book(self, book_id: str):
        """Get a specific book."""
        print(f"📖 Getting book {book_id}...")
        response = self._make_request('GET', f'/books/{book_id}')
        data = self._handle_response(response)
        
        print(f"Book ID: {data['book_id']}")
        print(f"User ID: {data['user_id']}")
        print(f"Title: {data['props'].get('title', 'Untitled')}")
        print(f"Genre: {data['props'].get('genre', 'Unknown')}")
        print(f"Chunks: {data.get('chunk_count', 0)}")
        print(f"Words: {data.get('word_count', 0)}")
        print(f"Locked: {data.get('is_locked', False)}")
        print(f"Created: {data['created_at']}")
        print(f"Updated: {data['updated_at']}")
        
        if data['props']:
            print("\nProperties:")
            for key, value in data['props'].items():
                if key not in ['title', 'genre']:
                    print(f"  {key}: {value}")
    
    def create_book(self, title: str, genre: str = None, **props):
        """Create a new book."""
        book_props = {'title': title}
        if genre:
            book_props['genre'] = genre
        book_props.update(props)
        
        print(f"📚 Creating book '{title}'...")
        response = self._make_request('POST', '/books', json={'props': book_props})
        data = self._handle_response(response, "Book created successfully!")
        
        print(f"Book ID: {data['book_id']}")
        return data['book_id']
    
    def update_book(self, book_id: str, **props):
        """Update a book's properties."""
        print(f"✏️ Updating book {book_id}...")
        response = self._make_request('PUT', f'/books/{book_id}', json={'props': props})
        self._handle_response(response, "Book updated successfully!")
    
    def delete_book(self, book_id: str):
        """Delete a book."""
        print(f"🗑️ Deleting book {book_id}...")
        response = self._make_request('DELETE', f'/books/{book_id}')
        self._handle_response(response, "Book deleted successfully!")
    
    def get_book_status(self, book_id: str):
        """Get comprehensive book status."""
        print(f"📊 Getting status for book {book_id}...")
        response = self._make_request('GET', f'/books/{book_id}/status')
        data = self._handle_response(response)
        
        print(f"Book ID: {data['book_id']}")
        print(f"Chunks: {data['chunk_count']}")
        print(f"Words: {data['word_count']}")
        print(f"Locked: {data['is_locked']}")
        
        if data.get('latest_job'):
            job = data['latest_job']
            print(f"Latest Job: {job['job_id'][:8]}... ({job['state']})")
        else:
            print("Latest Job: None")
        
        if data.get('api_token_balance') is not None:
            print(f"API Balance: ${data['api_token_balance']}")
    
    # Chunk operations
    def list_chunks(self, book_id: str, include_text: bool = False, include_deleted: bool = False, chapter: int = None):
        """List chunks for a book."""
        params = {}
        if include_text:
            params['include_text'] = 'true'
        if include_deleted:
            params['include_deleted'] = 'true'
        if chapter is not None:
            params['chapter'] = chapter
        
        print(f"📝 Listing chunks for book {book_id}...")
        response = self._make_request('GET', f'/books/{book_id}/chunks', params=params)
        data = self._handle_response(response)
        
        chunks = data.get('chunks', [])
        if not chunks:
            print("No chunks found.")
            return
        
        print(f"\nFound {len(chunks)} chunk(s):")
        for chunk in chunks:
            status_icons = []
            if chunk['is_deleted']:
                status_icons.append('🗑️')
            if chunk['is_locked']:
                status_icons.append('🔒')
            if not chunk['is_latest']:
                status_icons.append('📜')
            
            status = ' '.join(status_icons)
            print(f"  📄 {chunk['chunk_id'][:8]}... v{chunk['version']} {status}")
            print(f"     Type: {chunk['type'] or 'unknown'}, Chapter: {chunk['chapter'] or 'N/A'}")
            print(f"     Words: {chunk['word_count']}, Order: {chunk['order']}")
            
            if include_text and chunk.get('text'):
                preview = chunk['text'][:100].replace('\n', ' ')
                print(f"     Text: {preview}{'...' if len(chunk['text']) > 100 else ''}")
            print()
    
    def get_chunk(self, chunk_id: str, version: int = None):
        """Get a specific chunk."""
        params = {}
        if version is not None:
            params['version'] = version
        
        print(f"📄 Getting chunk {chunk_id}...")
        response = self._make_request('GET', f'/chunks/{chunk_id}', params=params)
        data = self._handle_response(response)
        
        print(f"Chunk ID: {data['chunk_id']}")
        print(f"Version: {data['version']} {'(latest)' if data['is_latest'] else '(old)'}")
        print(f"Book ID: {data['book_id']}")
        print(f"Type: {data['type'] or 'unknown'}")
        print(f"Chapter: {data['chapter'] or 'N/A'}")
        print(f"Order: {data['order']}")
        print(f"Words: {data['word_count']}")
        print(f"Deleted: {data['is_deleted']}")
        print(f"Locked: {data['is_locked']}")
        print(f"Created: {data['created_at']}")
        
        if data.get('text'):
            print(f"\nText ({len(data['text'])} characters):")
            print("-" * 50)
            print(data['text'])
            print("-" * 50)
    
    def create_chunk(self, book_id: str, text: str, chunk_type: str = None, chapter: int = None, order: float = None, **props):
        """Create a new chunk."""
        chunk_data = {'text': text, 'props': props}
        if chunk_type:
            chunk_data['type'] = chunk_type
        if chapter is not None:
            chunk_data['chapter'] = chapter
        if order is not None:
            chunk_data['order'] = order
        
        print(f"📝 Creating chunk in book {book_id}...")
        response = self._make_request('POST', f'/books/{book_id}/chunks', json=chunk_data)
        data = self._handle_response(response, "Chunk created successfully!")
        
        print(f"Chunk ID: {data['chunk_id']}")
        print(f"Words: {data['word_count']}")
        return data['chunk_id']
    
    def update_chunk(self, chunk_id: str, text: str = None, **props):
        """Update a chunk (creates new version)."""
        update_data = {'props': props}
        if text is not None:
            update_data['text'] = text
        
        print(f"✏️ Updating chunk {chunk_id}...")
        response = self._make_request('PUT', f'/chunks/{chunk_id}', json=update_data)
        data = self._handle_response(response, "Chunk updated successfully!")
        
        print(f"New version: {data['version']}")
        print(f"Words: {data['word_count']}")
    
    def delete_chunk(self, chunk_id: str):
        """Delete a chunk (soft delete)."""
        print(f"🗑️ Deleting chunk {chunk_id}...")
        response = self._make_request('DELETE', f'/chunks/{chunk_id}')
        self._handle_response(response, "Chunk deleted successfully!")
    
    def list_chunk_versions(self, chunk_id: str):
        """List all versions of a chunk."""
        print(f"📜 Listing versions for chunk {chunk_id}...")
        response = self._make_request('GET', f'/chunks/{chunk_id}/versions')
        data = self._handle_response(response)
        
        versions = data.get('versions', [])
        if not versions:
            print("No versions found.")
            return
        
        print(f"\nFound {len(versions)} version(s):")
        for version in versions:
            status = "LATEST" if version['is_latest'] else "old"
            print(f"  📄 Version {version['version']} ({status})")
            print(f"     ID: {version['id']}, Words: {version['word_count']}")
            print(f"     Created: {version['created_at']}")
            print()
    
    # Job operations
    def list_jobs(self, book_id: str = None, state: str = None):
        """List jobs."""
        if book_id:
            endpoint = f'/books/{book_id}/jobs'
            print(f"⚙️ Listing jobs for book {book_id}...")
        else:
            endpoint = '/jobs/running'
            print("⚙️ Listing running jobs...")
        
        params = {}
        if state:
            params['state'] = state
        
        response = self._make_request('GET', endpoint, params=params)
        data = self._handle_response(response)
        
        jobs = data.get('jobs', [])
        if not jobs:
            print("No jobs found.")
            return
        
        print(f"\nFound {len(jobs)} job(s):")
        for job in jobs:
            duration = ""
            if job.get('started_at') and job.get('completed_at'):
                # Could calculate duration here if needed
                duration = " (completed)"
            elif job.get('started_at'):
                duration = " (running)"
            
            print(f"  ⚙️ {job['job_id'][:8]}... - {job['job_type']} ({job['state']}){duration}")
            print(f"     Book: {job['book_id'][:8]}...")
            print(f"     Created: {job['created_at']}")
            if job['props']:
                print(f"     Props: {job['props']}")
            print()
    
    def get_job(self, job_id: str):
        """Get a specific job."""
        print(f"⚙️ Getting job {job_id}...")
        response = self._make_request('GET', f'/jobs/{job_id}')
        data = self._handle_response(response)
        
        print(f"Job ID: {data['job_id']}")
        print(f"Type: {data['job_type']}")
        print(f"State: {data['state']}")
        print(f"Book ID: {data['book_id']}")
        print(f"Created: {data['created_at']}")
        if data.get('started_at'):
            print(f"Started: {data['started_at']}")
        if data.get('completed_at'):
            print(f"Completed: {data['completed_at']}")
        
        if data['props']:
            print("\nProperties:")
            for key, value in data['props'].items():
                print(f"  {key}: {value}")
    
    def create_job(self, book_id: str, job_type: str, **props):
        """Create a new job."""
        job_data = {'job_type': job_type, 'props': props}
        
        print(f"⚙️ Creating {job_type} job for book {book_id}...")
        response = self._make_request('POST', f'/books/{book_id}/jobs', json=job_data)
        data = self._handle_response(response, "Job created successfully!")
        
        print(f"Job ID: {data['job_id']}")
        print(f"State: {data['state']}")
        return data['job_id']
    
    def cancel_job(self, job_id: str):
        """Cancel a job."""
        print(f"🛑 Cancelling job {job_id}...")
        response = self._make_request('DELETE', f'/jobs/{job_id}')
        self._handle_response(response, "Job cancelled successfully!")
    
    def get_job_logs(self, job_id: str, tail: int = None):
        """Get logs for a job."""
        print(f"📋 Getting logs for job {job_id}...")
        endpoint = f"/jobs/{job_id}/logs"
        params = {}
        
        if tail:
            params['tail'] = tail
            
        response = self._make_request('GET', endpoint, params=params)
        data = self._handle_response(response)
        
        logs = data.get('logs', [])
        if not logs:
            print("No logs found.")
            return logs
        
        for log in logs:
            created_at = log.get('created_at', '')
            log_level = log.get('log_level', 'INFO')
            log_entry = log.get('log_entry', '')
            
            level_color = {
                'DEBUG': '',
                'INFO': '',
                'WARNING': '\033[93m',  # Yellow
                'ERROR': '\033[91m',    # Red
                'LLM': '\033[96m'       # Cyan
            }.get(log_level, '')
            reset = '\033[0m'
            
            print(f"{created_at} {level_color}[{log_level}]{reset} {log_entry}")
            
        return logs
        
    def wait_for_job(self, job_id: str, timeout_seconds: int = 600, poll_interval_seconds: int = 5, verbose: bool = True):
        """Wait for a job to complete with timeout.
        
        Args:
            job_id: ID of the job to wait for
            timeout_seconds: Maximum time to wait in seconds
            poll_interval_seconds: How often to check job status
            verbose: Whether to print status updates
            
        Returns:
            The completed job data or None if timed out
        """
        import time
        
        start_time = time.time()
        last_log_id = 0
        
        if verbose:
            print(f"⏳ Waiting for job {job_id} to complete (timeout: {timeout_seconds}s)...")
            
        while True:
            # Check job status
            job = self.get_job(job_id)
            
            if not job:
                if verbose:
                    print(f"❌ Job {job_id} not found")
                return None
                
            # Get current state
            state = job.get('state', '').lower()
            
            # Print latest logs in verbose mode
            if verbose:
                logs = self.get_job_logs(job_id)
                if logs and len(logs) > 0:
                    latest_log_id = logs[-1]['id']
                    if latest_log_id > last_log_id:
                        last_log_id = latest_log_id
            
            # Check if job finished
            if state in ['complete', 'error', 'cancelled']:
                if verbose:
                    status_icon = {
                        'complete': '✅',
                        'error': '❌',
                        'cancelled': '🛑'
                    }.get(state, '⚪')
                    print(f"{status_icon} Job {job_id} finished with state: {state}")
                    
                    if state == 'error' and job.get('error_message'):
                        print(f"Error message: {job['error_message']}")
                return job
                
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                if verbose:
                    print(f"⏰ Timeout reached after {elapsed:.2f}s, job is still in state: {state}")
                return None
                
            # Wait for next poll
            time.sleep(poll_interval_seconds)
    
    def check_lock_status(self, book_id: str):
        """Check if a book is locked and by which job."""
        book = self.get_book(book_id)
        
        if not book:
            print(f"❌ Book {book_id} not found")
            return False, None
            
        is_locked = book.get('is_locked', False)
        job_id = book.get('job')
        
        if is_locked:
            print(f"🔒 Book {book_id} is locked by job: {job_id}")
            if job_id:
                # Get job details
                job = self.get_job(job_id)
                job_type = job.get('job_type', 'unknown') if job else 'unknown'
                state = job.get('state', 'unknown') if job else 'unknown'
                print(f"   Job type: {job_type}, State: {state}")
        else:
            print(f"🔓 Book {book_id} is unlocked")
            
        return is_locked, job_id
        
    def setup_book(self, title: str, genre: str, brief: str, style: str = "Contemporary", 
                   wait_for_completion: bool = True, timeout_seconds: int = 600):
        """Complete book setup workflow: create book and run create_foundation job.
        
        Args:
            title: Book title
            genre: Book genre
            brief: Brief description of the book
            style: Writing style
            wait_for_completion: Whether to wait for job completion
            timeout_seconds: Maximum time to wait for job completion
            
        Returns:
            Tuple of (book_id, job_id)
        """
        print(f"📚 Setting up new book: '{title}'")
        print(f"   Genre: {genre}")
        print(f"   Brief: {brief}")
        
        # Step 1: Create the book
        try:
            book_data = self.create_book(title, genre, model_mode="gpt-4")
            book_id = book_data['book_id']
            print(f"✅ Book created with ID: {book_id}")
        except Exception as e:
            print(f"❌ Failed to create book: {e}")
            return None, None
            
        # Step 2: Create foundation job
        try:
            job_data = self.create_job(book_id, "create_foundation", 
                                      title=title,
                                      genre=genre,
                                      brief=brief,
                                      style=style)
            job_id = job_data['job_id']
            print(f"✅ Foundation job created with ID: {job_id}")
        except Exception as e:
            print(f"❌ Failed to create foundation job: {e}")
            return book_id, None
            
        # Step 3: Wait for job completion if requested
        if wait_for_completion:
            print(f"⏳ Waiting for create_foundation job to complete...")
            completed_job = self.wait_for_job(job_id, timeout_seconds=timeout_seconds)
            
            if completed_job and completed_job.get('state') == 'complete':
                print(f"✅ Book foundation completed successfully")
                # Check book lock status after completion
                is_locked, _ = self.check_lock_status(book_id)
                if is_locked:
                    print("   Warning: Book is still locked after job completion")
            else:
                print(f"❌ Job did not complete successfully within timeout")
                
        return book_id, job_id
        
    def generate_chunk_text(self, book_id: str, chunk_id: str, wait_for_completion: bool = True, 
                         timeout_seconds: int = 300):
        """Generate text for a specific chunk using the 'GenerateChunk' job."""
        print(f"📝 Generating text for chunk {chunk_id} in book {book_id}...")
        
        # Create 'GenerateChunk' job
        try:
            job_data = self.create_job(book_id, "GenerateChunk", chunk_id=chunk_id)
            job_id = job_data['job_id']
            print(f"✅ Text generation job created with ID: {job_id}")
        except Exception as e:
            print(f"❌ Failed to create text generation job: {e}")
            return None
            
        # Wait for job completion if requested
        if wait_for_completion:
            completed_job = self.wait_for_job(job_id, timeout_seconds=timeout_seconds)
            if completed_job and completed_job.get('state') == 'complete':
                print(f"✅ Text generation completed successfully")
                
                # Fetch the updated chunk
                try:
                    chunk = self.get_chunk(chunk_id)
                    if chunk and chunk.get('text'):
                        text_preview = chunk['text'][:100] + '...' if len(chunk['text']) > 100 else chunk['text']
                        print(f"📄 Generated text: {text_preview}")
                except:
                    pass
            else:
                print(f"❌ Text generation did not complete successfully within timeout")
                
        return job_id
    
    def export_book_html(self, book_id: str, output_file: str = None):
        """Export a book as HTML with all chunks in order."""
        print(f"📄 Exporting book {book_id} as HTML...")
        
        # Get book details
        book_response = self._make_request('GET', f'/books/{book_id}')
        book_data = self._handle_response(book_response)
        
        # Get all chunks for the book
        chunks_response = self._make_request('GET', f'/books/{book_id}/chunks', params={'include_text': 'true'})
        chunks_data = self._handle_response(chunks_response)
        
        chunks = chunks_data.get('chunks', [])
        if not chunks:
            print("No chunks found to export.")
            return
        
        # Sort chunks by chapter and order
        chunks.sort(key=lambda x: (x.get('chapter') or 999, x.get('order') or 0))
        
        # Generate HTML
        html_content = self._generate_book_html(book_data, chunks)
        
        # Determine output filename
        if not output_file:
            safe_title = "".join(c for c in book_data['props'].get('title', 'Untitled') if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')
            output_file = f"{safe_title}_{book_id[:8]}.html"
        
        # Write to file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ Book exported to: {output_file}")
            print(f"📊 Exported {len(chunks)} chunks, {book_data.get('word_count', 0)} words total")
        except Exception as e:
            print(f"❌ Failed to write file: {e}")
            return
    
    def _generate_book_html(self, book_data: dict, chunks: list) -> str:
        """Generate HTML content for the book export."""
        title = book_data['props'].get('title', 'Untitled')
        genre = book_data['props'].get('genre', 'Unknown')
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fafafa;
        }}
        
        .book-header {{
            border-bottom: 3px solid #333;
            margin-bottom: 30px;
            padding-bottom: 20px;
        }}
        
        .book-title {{
            font-size: 2.5em;
            margin: 0;
            color: #333;
        }}
        
        .book-meta {{
            color: #666;
            font-style: italic;
            margin-top: 10px;
        }}
        
        .book-stats {{
            background: #e9e9e9;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        
        .chunk {{
            background: white;
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .chunk-header {{
            border-bottom: 1px solid #ddd;
            margin-bottom: 15px;
            padding-bottom: 10px;
            font-size: 0.9em;
            color: #666;
        }}
        
        .chunk-meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 10px;
        }}
        
        .chunk-meta-item {{
            background: #f5f5f5;
            padding: 5px 10px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 0.8em;
        }}
        
        .chunk-content {{
            white-space: pre-wrap;
            font-size: 1.1em;
            line-height: 1.7;
        }}
        
        .outline {{
            background: #f0f8ff;
        }}
        
        .chapter {{
            background: #fffef0;
        }}
        
        .deleted {{
            background: #ffe6e6;
            opacity: 0.7;
        }}
        
        .locked {{
            border-left: 4px solid #ff6b6b;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        
        .toc {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        
        .toc h3 {{
            margin-top: 0;
        }}
        
        .toc ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .toc li {{
            margin: 5px 0;
        }}
        
        .toc a {{
            text-decoration: none;
            color: #2c3e50;
        }}
        
        .toc a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="book-header">
        <h1 class="book-title">{title}</h1>
        <div class="book-meta">
            <strong>Genre:</strong> {genre} |
            <strong>Book ID:</strong> {book_data['book_id']} |
            <strong>Created:</strong> {book_data['created_at'][:10]}
        </div>
    </div>
    
    <div class="book-stats">
        <strong>📊 Book Statistics:</strong><br>
        Chunks: {len(chunks)} | 
        Words: {book_data.get('word_count', 0)} | 
        Locked: {'Yes' if book_data.get('is_locked') else 'No'}
"""
        
        # Add additional book properties
        if book_data.get('props'):
            extra_props = {k: v for k, v in book_data['props'].items() if k not in ['title', 'genre']}
            if extra_props:
                html += "<br><strong>Properties:</strong> "
                html += " | ".join([f"{k}: {v}" for k, v in extra_props.items()])
        
        html += """
    </div>
"""
        
        # Generate table of contents
        chapters = {}
        for chunk in chunks:
            if chunk.get('chapter') is not None:
                chapter_num = chunk['chapter']
                if chapter_num not in chapters:
                    chapters[chapter_num] = []
                chapters[chapter_num].append(chunk)
        
        if chapters:
            html += """
    <div class="toc">
        <h3>📚 Table of Contents</h3>
        <ul>
"""
            for chapter_num in sorted(chapters.keys()):
                if chapter_num == 0:
                    html += f'            <li><a href="#chapter-{chapter_num}">📝 Outline/Prologue</a></li>\n'
                else:
                    html += f'            <li><a href="#chapter-{chapter_num}">📖 Chapter {chapter_num}</a></li>\n'
            
            html += """        </ul>
    </div>
"""
        
        # Add chunks
        current_chapter = None
        for i, chunk in enumerate(chunks):
            chunk_classes = ['chunk']
            
            # Add type-based styling
            chunk_type = chunk.get('type', 'unknown')
            if chunk_type == 'outline':
                chunk_classes.append('outline')
            elif chunk_type == 'chapter':
                chunk_classes.append('chapter')
            
            # Add status-based styling
            if chunk.get('is_deleted'):
                chunk_classes.append('deleted')
            if chunk.get('is_locked'):
                chunk_classes.append('locked')
            
            # Add chapter header if needed
            if chunk.get('chapter') is not None and chunk['chapter'] != current_chapter:
                current_chapter = chunk['chapter']
                if current_chapter == 0:
                    html += f'\n    <h2 id="chapter-{current_chapter}">📝 Outline/Prologue</h2>\n'
                else:
                    html += f'\n    <h2 id="chapter-{current_chapter}">📖 Chapter {current_chapter}</h2>\n'
            
            html += f'''
    <div class="{' '.join(chunk_classes)}">
        <div class="chunk-header">
            <div class="chunk-meta">
                <div class="chunk-meta-item"><strong>ID:</strong> {chunk['chunk_id'][:8]}...</div>
                <div class="chunk-meta-item"><strong>Version:</strong> {chunk['version']}</div>
                <div class="chunk-meta-item"><strong>Type:</strong> {chunk_type}</div>
                <div class="chunk-meta-item"><strong>Chapter:</strong> {chunk.get('chapter', 'N/A')}</div>
                <div class="chunk-meta-item"><strong>Order:</strong> {chunk.get('order', 0)}</div>
                <div class="chunk-meta-item"><strong>Words:</strong> {chunk.get('word_count', 0)}</div>
'''
            
            # Add status indicators
            status_items = []
            if chunk.get('is_latest'):
                status_items.append('LATEST')
            else:
                status_items.append('OLD')
            
            if chunk.get('is_deleted'):
                status_items.append('DELETED')
            
            if chunk.get('is_locked'):
                status_items.append('LOCKED')
            
            html += f'                <div class="chunk-meta-item"><strong>Status:</strong> {" | ".join(status_items)}</div>\n'
            
            # Add chunk properties if any
            if chunk.get('props'):
                props_str = ", ".join([f"{k}: {v}" for k, v in chunk['props'].items()])
                html += f'                <div class="chunk-meta-item"><strong>Props:</strong> {props_str}</div>\n'
            
            html += f'''            </div>
            <div style="font-size: 0.8em; color: #999; margin-top: 5px;">
                Created: {chunk['created_at'][:19]} | Chunk {i+1} of {len(chunks)}
            </div>
        </div>
        <div class="chunk-content">{chunk.get('text', '(No content)')}</div>
    </div>
'''
        
        html += """
    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666; font-size: 0.9em;">
        Generated by BookBot CLI | """ + f"""Book ID: {book_data['book_id']} | Export Date: {book_data['created_at'][:10]}
    </div>

</body>
</html>"""
        
        return html


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='BookBot CLI Tool')
    parser.add_argument('--url', default='http://localhost:5001', help='Base URL for the BookBot server')
    parser.add_argument('--admin-key', help='Admin API key')
    parser.add_argument('--user-api-key', help='User API key')
    parser.add_argument('command', nargs='?', choices=['health', 'config', 'books', 'chunks', 'jobs', 'setup', 'auth'], help='Command to execute')
    
    # Subparsers for the primary commands
    subparsers = parser.add_subparsers(dest='command')
    
    # Health check commands
    health_parser = subparsers.add_parser('health', help='Check server health')
    
    # Config commands
    config_parser = subparsers.add_parser('config', help='Get server configuration')
    
    # Auth commands
    auth_parser = subparsers.add_parser('auth', help='Authentication management')
    auth_subparsers = auth_parser.add_subparsers(dest='auth_action')
    
    set_key_parser = auth_subparsers.add_parser('set-key', help='Set API key')
    set_key_parser.add_argument('api_key', help='API key to store')
    set_key_parser.add_argument('--admin', action='store_true', help='Set as admin key instead of user key')
    
    # Book commands
    book_parser = subparsers.add_parser('books', help='Book operations')
    book_subparsers = book_parser.add_subparsers(dest='book_action')
    
    list_books_parser = book_subparsers.add_parser('list', help='List all books')
    
    get_book_parser = book_subparsers.add_parser('get', help='Get a specific book')
    get_book_parser.add_argument('book_id', help='Book ID')
    
    create_book_parser = book_subparsers.add_parser('create', help='Create a new book')
    create_book_parser.add_argument('title', help='Book title')
    create_book_parser.add_argument('--genre', help='Book genre')
    create_book_parser.add_argument('--props', help='Additional properties as JSON')
    
    update_book_parser = book_subparsers.add_parser('update', help='Update a book')
    update_book_parser.add_argument('book_id', help='Book ID')
    update_book_parser.add_argument('--props', required=True, help='Properties as JSON')
    
    delete_book_parser = book_subparsers.add_parser('delete', help='Delete a book')
    delete_book_parser.add_argument('book_id', help='Book ID')
    
    status_book_parser = book_subparsers.add_parser('status', help='Get book status')
    status_book_parser.add_argument('book_id', help='Book ID')
    
    check_lock_parser = book_subparsers.add_parser('check-lock', help='Check book lock status')
    check_lock_parser.add_argument('book_id', help='Book ID')
    
    export_book_parser = book_subparsers.add_parser('export', help='Export a book as HTML')
    export_book_parser.add_argument('book_id', help='Book ID')
    export_book_parser.add_argument('--output', '-o', help='Output file')
    
    # Chunk commands
    chunk_parser = subparsers.add_parser('chunks', help='Chunk operations')
    chunk_subparsers = chunk_parser.add_subparsers(dest='chunk_action')
    
    list_chunks_parser = chunk_subparsers.add_parser('list', help='List chunks')
    list_chunks_parser.add_argument('book_id', help='Book ID')
    list_chunks_parser.add_argument('--text', action='store_true', help='Include text content')
    list_chunks_parser.add_argument('--deleted', action='store_true', help='Include deleted chunks')
    list_chunks_parser.add_argument('--chapter', type=int, help='Filter by chapter number')
    
    get_chunk_parser = chunk_subparsers.add_parser('get', help='Get a specific chunk')
    get_chunk_parser.add_argument('chunk_id', help='Chunk ID')
    get_chunk_parser.add_argument('--version', type=int, help='Specific version')
    
    create_chunk_parser = chunk_subparsers.add_parser('create', help='Create a new chunk')
    create_chunk_parser.add_argument('book_id', help='Book ID')
    create_chunk_parser.add_argument('text', help='Chunk text')
    create_chunk_parser.add_argument('--type', help='Chunk type')
    create_chunk_parser.add_argument('--chapter', type=int, help='Chapter number')
    create_chunk_parser.add_argument('--order', type=float, help='Order within chapter')
    create_chunk_parser.add_argument('--props', help='Additional properties as JSON')
    
    update_chunk_parser = chunk_subparsers.add_parser('update', help='Update a chunk')
    update_chunk_parser.add_argument('chunk_id', help='Chunk ID')
    update_chunk_parser.add_argument('--text', help='New text content')
    update_chunk_parser.add_argument('--props', help='Additional properties as JSON')
    
    delete_chunk_parser = chunk_subparsers.add_parser('delete', help='Delete a chunk')
    delete_chunk_parser.add_argument('chunk_id', help='Chunk ID')
    
    versions_chunk_parser = chunk_subparsers.add_parser('versions', help='List chunk versions')
    versions_chunk_parser.add_argument('chunk_id', help='Chunk ID')
    
    generate_chunk_parser = chunk_subparsers.add_parser('generate', help='Generate text for a chunk')
    generate_chunk_parser.add_argument('book_id', help='Book ID')
    generate_chunk_parser.add_argument('chunk_id', help='Chunk ID')
    generate_chunk_parser.add_argument('--no-wait', action='store_true', help='Do not wait for job completion')
    generate_chunk_parser.add_argument('--timeout', type=int, default=300, help='Timeout for waiting (seconds)')
    
    # Job commands
    job_parser = subparsers.add_parser('jobs', help='Job operations')
    job_subparsers = job_parser.add_subparsers(dest='job_action')
    
    list_jobs_parser = job_subparsers.add_parser('list', help='List jobs')
    list_jobs_parser.add_argument('--book-id', help='Book ID to filter by')
    list_jobs_parser.add_argument('--state', help='Job state to filter by')
    
    get_job_parser = job_subparsers.add_parser('get', help='Get a specific job')
    get_job_parser.add_argument('job_id', help='Job ID')
    
    create_job_parser = job_subparsers.add_parser('create', help='Create a new job')
    create_job_parser.add_argument('book_id', help='Book ID')
    create_job_parser.add_argument('job_type', help='Job type (e.g., demo, create_foundation, GenerateChunk)')
    create_job_parser.add_argument('--props', help='Job properties as JSON')
    
    cancel_job_parser = job_subparsers.add_parser('cancel', help='Cancel a job')
    cancel_job_parser.add_argument('job_id', help='Job ID')
    
    logs_job_parser = job_subparsers.add_parser('logs', help='Get job logs')
    logs_job_parser.add_argument('job_id', help='Job ID')
    logs_job_parser.add_argument('--tail', type=int, help='Show last N log entries')
    
    wait_job_parser = job_subparsers.add_parser('wait', help='Wait for job completion')
    wait_job_parser.add_argument('job_id', help='Job ID')
    wait_job_parser.add_argument('--timeout', type=int, default=600, help='Maximum wait time in seconds')
    wait_job_parser.add_argument('--poll', type=int, default=5, help='Poll interval in seconds')
    
    # Setup workflow commands
    setup_parser = subparsers.add_parser('setup', help='Book setup workflows')
    setup_subparsers = setup_parser.add_subparsers(dest='setup_action')
    
    new_book_parser = setup_subparsers.add_parser('new-book', help='Create a new book with foundation')
    new_book_parser.add_argument('title', help='Book title')
    new_book_parser.add_argument('genre', help='Book genre')
    new_book_parser.add_argument('brief', help='Brief description of the book')
    new_book_parser.add_argument('--style', default='Contemporary', help='Writing style')
    new_book_parser.add_argument('--no-wait', action='store_true', help='Do not wait for job completion')
    new_book_parser.add_argument('--timeout', type=int, default=600, help='Timeout for waiting (seconds)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI client
    cli = BookBotCLI(base_url=args.url, admin_key=args.admin_key, user_api_key=args.user_api_key)
    
    try:
        # Execute commands
        if args.command == 'health':
            cli.health_check()
        elif args.command == 'config':
            cli.get_config()
        elif args.command == 'auth':
            if args.auth_action == 'set-key':
                cli.set_api_key(args.api_key, args.admin)
            else:
                auth_parser.print_help()
        elif args.command == 'books':
            if args.book_action == 'list':
                cli.list_books()
            elif args.book_action == 'get':
                cli.get_book(args.book_id)
            elif args.book_action == 'create':
                props = json.loads(args.props) if args.props else {}
                cli.create_book(args.title, args.genre, **props)
            elif args.book_action == 'update':
                props = json.loads(args.props)
                cli.update_book(args.book_id, **props)
            elif args.book_action == 'delete':
                cli.delete_book(args.book_id)
            elif args.book_action == 'status':
                cli.get_book_status(args.book_id)
            elif args.book_action == 'check-lock':
                cli.check_lock_status(args.book_id)
            elif args.book_action == 'export':
                cli.export_book_html(args.book_id, args.output)
            else:
                book_parser.print_help()
        elif args.command == 'chunks':
            if args.chunk_action == 'list':
                cli.list_chunks(args.book_id, args.text, args.deleted, args.chapter)
            elif args.chunk_action == 'get':
                cli.get_chunk(args.chunk_id, args.version)
            elif args.chunk_action == 'create':
                props = json.loads(args.props) if args.props else {}
                cli.create_chunk(args.book_id, args.text, args.type, args.chapter, args.order, **props)
            elif args.chunk_action == 'update':
                props = json.loads(args.props) if args.props else {}
                cli.update_chunk(args.chunk_id, args.text, **props)
            elif args.chunk_action == 'delete':
                cli.delete_chunk(args.chunk_id)
            elif args.chunk_action == 'versions':
                cli.list_chunk_versions(args.chunk_id)
            elif args.chunk_action == 'generate':
                wait_for_completion = not args.no_wait
                cli.generate_chunk_text(args.book_id, args.chunk_id, wait_for_completion, args.timeout)
            else:
                chunk_parser.print_help()
        elif args.command == 'jobs':
            if args.job_action == 'list':
                cli.list_jobs(args.book_id, args.state)
            elif args.job_action == 'get':
                cli.get_job(args.job_id)
            elif args.job_action == 'create':
                props = json.loads(args.props) if args.props else {}
                cli.create_job(args.book_id, args.job_type, **props)
            elif args.job_action == 'cancel':
                cli.cancel_job(args.job_id)
            elif args.job_action == 'logs':
                cli.get_job_logs(args.job_id, args.tail)
            elif args.job_action == 'wait':
                cli.wait_for_job(args.job_id, args.timeout, args.poll)
            else:
                job_parser.print_help()
        elif args.command == 'setup':
            if args.setup_action == 'new-book':
                wait_for_completion = not args.no_wait
                cli.setup_book(args.title, args.genre, args.brief, args.style, 
                              wait_for_completion, args.timeout)
            else:
                setup_parser.print_help()
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
