"""
Job API endpoints for BookBot.
"""

from flask import Blueprint, request, jsonify, Response, stream_template
import json
import time
from typing import Dict, Any, Generator

from backend.models import db, Job, JobLog, Book
from backend.auth import require_auth, require_read_access, require_edit_access
from backend.jobs import create_job, cancel_job

job_api = Blueprint('job_api', __name__)


@job_api.route('/books/<book_id>/jobs', methods=['GET'])
@require_read_access()
def list_jobs(book_id: str):
    """List jobs for a book."""
    # Parse query parameters
    state = request.args.get('state')
    
    query = Job.query.filter_by(book_id=book_id)
    
    if state:
        query = query.filter_by(state=state)
    
    jobs = query.order_by(Job.created_at.desc()).all()
    
    return jsonify({
        'jobs': [job.to_dict() for job in jobs]
    })


@job_api.route('/books/<book_id>/jobs', methods=['POST'])
@require_edit_access()
def create_job_endpoint(book_id: str):
    """Create a new job."""
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    job_type = data.get('job_type')
    if not job_type:
        return jsonify({'error': 'job_type is required'}), 400
    
    props = data.get('props', {})
    
    # Validate job type exists
    from backend.jobs import get_job_processor
    processor = get_job_processor()
    if job_type not in processor.job_types:
        return jsonify({'error': f'Unknown job type: {job_type}'}), 400
    
    job = create_job(book_id, job_type, props)
    
    return jsonify(job.to_dict()), 201


@job_api.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id: str):
    """Get a specific job."""
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    # TODO: Add proper authorization check for the book
    
    return jsonify(job.to_dict())


@job_api.route('/jobs/<job_id>', methods=['DELETE'])
def cancel_job_endpoint(job_id: str):
    """Cancel a job."""
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    # TODO: Add proper authorization check for the book
    
    if cancel_job(job_id):
        return jsonify({'message': 'Job cancelled successfully'})
    else:
        return jsonify({'error': 'Job cannot be cancelled'}), 400


@job_api.route('/jobs/<job_id>/logs', methods=['GET'])
def get_job_logs(job_id: str):
    """Get logs for a job."""
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    # TODO: Add proper authorization check for the book
    
    logs = JobLog.query.filter_by(job_id=job_id).order_by(JobLog.created_at).all()
    
    return jsonify({
        'logs': [log.to_dict() for log in logs]
    })


@job_api.route('/books/<book_id>/jobs/stream', methods=['GET'])
@require_read_access()
def stream_job_updates(book_id: str):
    """Server-sent events stream for job updates."""
    
    def generate() -> Generator[str, None, None]:
        """Generate server-sent events for job updates."""
        last_check = time.time()
        
        while True:
            try:
                # Get recent jobs for this book
                jobs = Job.query.filter_by(book_id=book_id).order_by(Job.created_at.desc()).limit(10).all()
                
                # Check for updates since last check
                updated_jobs = [job for job in jobs if job.updated_at and job.updated_at.timestamp() > last_check]
                
                if updated_jobs:
                    for job in updated_jobs:
                        data = {
                            'type': 'job_update',
                            'job': job.to_dict()
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                
                last_check = time.time()
                
                # Send heartbeat
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
                
                time.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )


@job_api.route('/jobs/running', methods=['GET'])
@require_auth
def list_running_jobs():
    """List all currently running jobs."""
    # For now, return all running jobs. In the future, filter by user access.
    running_jobs = Job.query.filter_by(state='running').order_by(Job.started_at.desc()).all()
    
    return jsonify({
        'jobs': [job.to_dict() for job in running_jobs]
    })


@job_api.route('/jobs', methods=['GET'])
@require_auth
def list_all_jobs():
    """List all jobs with optional filtering."""
    # Parse query parameters
    state = request.args.get('state')
    job_type = request.args.get('job_type')
    limit = request.args.get('limit', 100, type=int)
    
    query = Job.query
    
    if state:
        query = query.filter_by(state=state)
    
    if job_type:
        query = query.filter_by(job_type=job_type)
    
    jobs = query.order_by(Job.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'jobs': [job.to_dict() for job in jobs]
    })


@job_api.route('/jobs/total_cost', methods=['GET'])
@require_auth
def get_total_job_cost():
    """Calculate and return the total cost of all jobs."""
    all_jobs = Job.query.all()
    grand_total_cost = 0.0
    for job in all_jobs:
        # The job.total_cost property handles summing costs from its JobLog entries
        grand_total_cost += job.total_cost
    
    return jsonify({'total_cost': round(grand_total_cost, 6)})
