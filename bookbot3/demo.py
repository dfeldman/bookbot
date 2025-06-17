#!/usr/bin/env python3
"""
BookBot Demo Script

This script demonstrates the complete BookBot system functionality including:
- Creating books and chunks
- Running background jobs
- LLM integration (fake)
- Job logging and monitoring
"""

import time
import requests
import threading
from app import create_app

def run_demo():
    """Run a complete demonstration of BookBot functionality."""
    print("🤖 BookBot System Demo")
    print("=" * 50)
    
    # Create the app
    app = create_app()
    
    def run_server():
        app.run(host='127.0.0.1', port=5002, debug=False, threaded=True, use_reloader=False)
    
    # Start server in background
    print("🚀 Starting BookBot server...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    
    BASE_URL = "http://127.0.0.1:5002/api"
    
    try:
        # Test 1: Health check
        print("\n1️⃣ Testing system health...")
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   Health: {response.json()['status']}")
        
        # Test 2: Create a book
        print("\n2️⃣ Creating a new book...")
        book_data = {
            'props': {
                'title': 'The AI Chronicles',
                'genre': 'Science Fiction',
                'author': 'BookBot Demo',
                'model_mode': 'fake'
            }
        }
        response = requests.post(f"{BASE_URL}/books", json=book_data, timeout=5)
        book = response.json()
        book_id = book['book_id']
        print(f"   📚 Created: {book['props']['title']} (ID: {book_id[:8]}...)")
        
        # Test 3: Add some chunks
        print("\n3️⃣ Adding book content...")
        chapters = [
            {
                'text': '# Chapter 1: The Beginning\n\nIn a world where artificial intelligence had become commonplace, a new kind of story was about to unfold.',
                'props': {'tags': ['opening', 'introduction']},
                'type': 'chapter',
                'chapter': 1,
                'order': 1.0
            },
            {
                'text': '# Chapter 2: The Discovery\n\nThe protagonist discovers something that will change everything they thought they knew about AI.',
                'props': {'tags': ['plot', 'discovery']},
                'type': 'chapter', 
                'chapter': 2,
                'order': 2.0
            },
            {
                'text': '# Outline\n\n- Introduction to the world\n- Character development\n- Rising action\n- Climax\n- Resolution',
                'props': {'tags': ['structure', 'planning']},
                'type': 'outline',
                'chapter': 0,
                'order': 0.5
            }
        ]
        
        chunk_ids = []
        for i, chapter_data in enumerate(chapters, 1):
            response = requests.post(f"{BASE_URL}/books/{book_id}/chunks", json=chapter_data, timeout=5)
            chunk = response.json()
            chunk_ids.append(chunk['chunk_id'])
            print(f"   📝 Added {chunk['type']}: {chunk['word_count']} words")
        
        # Test 4: Check book status
        print("\n4️⃣ Checking book status...")
        response = requests.get(f"{BASE_URL}/books/{book_id}/status", timeout=5)
        status = response.json()
        print(f"   📊 Total chunks: {status['chunk_count']}")
        print(f"   📊 Total words: {status['word_count']}")
        
        # Test 5: Create and monitor a job
        print("\n5️⃣ Creating AI generation job...")
        job_data = {
            'job_type': 'demo',
            'props': {
                'target_word_count': 100,
                'description': 'Generate additional content for Chapter 3'
            }
        }
        response = requests.post(f"{BASE_URL}/books/{book_id}/jobs", json=job_data, timeout=5)
        job = response.json()
        job_id = job['job_id']
        print(f"   ⚙️ Created job: {job_id[:8]}... (state: {job['state']})")
        
        # Test 6: Monitor job execution
        print("\n6️⃣ Monitoring job execution...")
        for i in range(10):  # Wait up to 10 seconds
            response = requests.get(f"{BASE_URL}/jobs/{job_id}", timeout=5)
            job_status = response.json()
            print(f"   ⏱️ Job state: {job_status['state']}")
            
            if job_status['state'] in ['complete', 'error']:
                break
            time.sleep(1)
        
        # Test 7: Get job logs
        print("\n7️⃣ Retrieving job logs...")
        response = requests.get(f"{BASE_URL}/jobs/{job_id}/logs", timeout=5)
        logs = response.json()['logs']
        print(f"   📄 Job produced {len(logs)} log entries:")
        for log in logs[:5]:  # Show first 5 logs
            print(f"      {log['log_level']}: {log['log_entry']}")
        if len(logs) > 5:
            print(f"      ... and {len(logs) - 5} more entries")
        
        # Test 8: Test chunk versioning
        print("\n8️⃣ Testing chunk versioning...")
        if chunk_ids:
            # Update the first chunk
            update_data = {
                'text': '# Chapter 1: The Beginning (Revised)\n\nIn a world where artificial intelligence had become commonplace, a new and extraordinary kind of story was about to unfold with unexpected consequences.',
                'props': {'tags': ['opening', 'introduction', 'revised']}
            }
            response = requests.put(f"{BASE_URL}/chunks/{chunk_ids[0]}", json=update_data, timeout=5)
            updated_chunk = response.json()
            print(f"   ✏️ Updated chunk to version {updated_chunk['version']}")
            print(f"   📝 New word count: {updated_chunk['word_count']}")
            
            # Get version history
            response = requests.get(f"{BASE_URL}/chunks/{chunk_ids[0]}/versions", timeout=5)
            versions = response.json()['versions']
            print(f"   📚 Chunk now has {len(versions)} versions")
        
        # Test 9: Final status check
        print("\n9️⃣ Final system status...")
        response = requests.get(f"{BASE_URL}/books/{book_id}/status", timeout=5)
        final_status = response.json()
        print(f"   📊 Final word count: {final_status['word_count']}")
        print(f"   🔄 Latest job: {final_status['latest_job']['state'] if final_status['latest_job'] else 'None'}")
        
        print("\n✅ Demo completed successfully!")
        print("\n🎉 BookBot is fully functional with:")
        print("   • Book and chunk management")
        print("   • Content versioning")
        print("   • Background job processing")
        print("   • AI integration (fake LLM)")
        print("   • Comprehensive logging")
        print("   • RESTful API")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_demo()
