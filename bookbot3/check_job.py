from backend.models import db, Job, JobLog, Book
from flask import Flask
import json
import sys

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/bookbot.db'
db.init_app(app)

with app.app_context():
    # Get the last failed create_foundation job
    failed_job = Job.query.filter_by(state='failed', job_type='create_foundation').order_by(Job.created_at.desc()).first()
    
    if failed_job:
        print(f'==== Job ID: {failed_job.job_id}')
        print(f'Book ID: {failed_job.book_id}')
        print(f'Job Type: {failed_job.job_type}')
        print(f'Props: {json.dumps(failed_job.props)}')
        print(f'State: {failed_job.state}')
        print(f'Created: {failed_job.created_at}')
        
        # Check if the book actually exists
        book = Book.query.filter_by(book_id=failed_job.book_id).first() if failed_job.book_id else None
        print(f'Book exists: {book is not None}')
        
        print('===== Logs:')
        logs = JobLog.query.filter_by(job_id=failed_job.job_id).order_by(JobLog.created_at).all()
        for log in logs:
            print(f'{log.created_at}: [{log.log_level}] {log.log_entry}')
    else:
        print('No failed create_foundation jobs found.')
