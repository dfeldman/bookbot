"""
Database dump utility for BookBot.

This script dumps the entire contents of the BookBot database to a JSON file.
It includes all users, books, chunks, and jobs, with all their fields.
Stringified JSON in 'props' fields is converted to nested JSON objects.

The output is pretty-printed for readability.
"""

import json
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app
from backend.models import User, Book, Chunk, Job

def dump_database_to_json():
    """Connects to the database and dumps its contents to a JSON file.""" 
    app = create_app()
    
    with app.app_context():
        print("Starting database dump...")
        
        # Query all data
        users = User.query.all()
        books = Book.query.all()
        chunks = Chunk.query.all()
        jobs = Job.query.all()
        
        print(f"Found {len(users)} users, {len(books)} books, {len(chunks)} chunks, {len(jobs)} jobs.")
        
        # Serialize data
        data_dump = {
            'users': [user.to_dict() for user in users],
            'books': [book.to_dict() for book in books],
            'chunks': [chunk.to_dict(include_text=True) for chunk in chunks],
            'jobs': [job.to_dict() for job in jobs]
        }
        
        # Handle nested JSON in props fields
        for table in data_dump.values():
            for item in table:
                if 'props' in item and isinstance(item['props'], str):
                    try:
                        item['props'] = json.loads(item['props'])
                    except json.JSONDecodeError:
                        # If it's not valid JSON, leave it as a string
                        pass
        
        # Write to file
        output_filename = 'db_dump.json'
        with open(output_filename, 'w') as f:
            json.dump(data_dump, f, indent=4)
            
        print(f"Database dump completed. Data saved to {output_filename}")

if __name__ == '__main__':
    dump_database_to_json()
