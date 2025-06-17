"""
Demo script for job_utils functionality.

This script demonstrates how to use the get_chunk_context function
to extract relevant context for writing specific scenes.
"""

from app import create_app
from backend.jobs.job_utils import get_chunk_context
from backend.models import db, Book, Chunk


def demo_job_utils():
    """Demonstrate job_utils functionality."""
    app = create_app()
    
    with app.app_context():
        print("🚀 Job Utils Demo")
        print("=" * 50)
        
        # Create a demo book with foundation chunks
        book = Book(
            user_id="demo-user",
            props={'title': 'Demo Adventure', 'genre': 'Fantasy'}
        )
        db.session.add(book)
        db.session.commit()
        
        # Create outline chunk
        outline_text = """
## Chapter 1: The Journey Begins

### Hero leaves village #adventure #journey #village [[Scene 1]]
Our protagonist decides to leave their peaceful village to seek their destiny.
They pack their belongings and say goodbye to family.

### Hero meets mentor #adventure #mentor #magic [[Scene 2]]
Along the road, the hero encounters a wise old wizard.
The wizard offers guidance and magical training.

## Chapter 2: The First Challenge

### Hero faces bandits #adventure #combat #danger [[Scene 3]]
The hero is attacked by bandits on a lonely mountain pass.
This is their first real test of courage and skill.
        """
        
        outline_chunk = Chunk(
            book_id=book.book_id,
            text=outline_text.strip(),
            type="outline",
            chapter=0,
            order=1.0,
            props={},
            word_count=len(outline_text.split())
        )
        db.session.add(outline_chunk)
        
        # Create characters chunk
        characters_text = """
## Character: Hero #adventure #journey #combat
A young person destined for greatness.
Brave but inexperienced in the ways of the world.

## Character: Village Elder #village
The wise leader of the hero's home village.
Provides sage advice before the journey begins.

## Character: Wizard Mentor #adventure #mentor #magic
An ancient and powerful wizard who becomes the hero's guide.
Has extensive knowledge of magic and the world's dangers.

## Character: Bandit Leader #combat #danger
A ruthless criminal who preys on travelers.
Commands a small group of highway robbers.

## Character: Village Blacksmith #village
Creates weapons and tools for the villagers.
"""
        
        characters_chunk = Chunk(
            book_id=book.book_id,
            text=characters_text.strip(),
            type="characters",
            chapter=0,
            order=2.0,
            props={},
            word_count=len(characters_text.split())
        )
        db.session.add(characters_chunk)
        
        # Create settings chunk
        settings_text = """
## Settings: Peaceful Village #adventure #village #journey
A small, quiet farming community where the hero grew up.
Surrounded by rolling hills and peaceful meadows.

## Settings: Forest Road #adventure #journey #mentor
A winding path through ancient woods.
Where travelers often encounter unexpected meetings.

## Settings: Mountain Pass #adventure #combat #danger
A treacherous route through rocky peaks.
Known to be frequented by bandits and other dangers.

## Settings: Wizard's Tower #magic #mentor
A tall spire filled with magical artifacts.
The mentor's home and place of study.
        """
        
        settings_chunk = Chunk(
            book_id=book.book_id,
            text=settings_text.strip(),
            type="settings",
            chapter=0,
            order=3.0,
            props={},
            word_count=len(settings_text.split())
        )
        db.session.add(settings_chunk)
        
        db.session.commit()
        
        print(f"📚 Created demo book: {book.book_id}")
        print()
        
        # Demonstrate get_chunk_context for each scene
        scenes = ["Scene 1", "Scene 2", "Scene 3"]
        
        for scene_id in scenes:
            print(f"🎬 Getting context for {scene_id}")
            print("-" * 30)
            
            context = get_chunk_context(book.book_id, scene_id)
            
            print("📖 OUTLINE SECTION:")
            print(context['outline_section'])
            print()
            
            print(f"🏷️  TAGS: {', '.join(context['tags'])}")
            print()
            
            print("👥 RELEVANT CHARACTERS:")
            for i, char_section in enumerate(context['characters_sections'], 1):
                print(f"  {i}. {char_section.split(chr(10))[0]}")  # First line only
            print()
            
            print("🌍 RELEVANT SETTINGS:")
            for i, setting_section in enumerate(context['settings_sections'], 1):
                print(f"  {i}. {setting_section.split(chr(10))[0]}")  # First line only
            print()
            
            print("=" * 50)
            print()
        
        # Clean up
        db.session.delete(book)
        db.session.commit()
        
        print("✅ Demo completed successfully!")
        print()
        print("💡 Key Benefits:")
        print("   • Only relevant context is extracted for each scene")
        print("   • Characters and settings are filtered by shared tags")
        print("   • Prevents LLM from going off-track with irrelevant info")
        print("   • Supports both level 2 (##) and level 3 (###) headers")


if __name__ == "__main__":
    demo_job_utils()
