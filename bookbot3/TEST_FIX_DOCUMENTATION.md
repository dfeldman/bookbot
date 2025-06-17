# Test Fix Documentation

This document tracks the systematic approach to fixing BookBot's test suite after the database schema changes.

## Schema Changes That Broke Tests

The BookBot application underwent significant database schema changes:

1. **Chunk Model Changes:**
   - `title` field → `props['title']` (JSON field)
   - `content` field → `text` field  
   - All properties now stored in `props` JSON field

2. **ID Field Changes:**
   - Primary keys remain as `id` (auto-increment integers)
   - But job system uses `chunk_id` (UUID strings) for referencing
   - Tests need to use correct ID type for each context

3. **Session Management:**
   - SQLAlchemy DetachedInstanceError when returning objects across sessions
   - Need to return IDs instead of objects from setup methods

## Current Progress: 45 tests passing! 🎉

### ✅ COMPLETED FILES:
1. **test_job_system_integration_simple.py** - ✅ 8/8 tests passing
2. **test_generate_text_job_simple.py** - ✅ 11/11 tests passing  
3. **test_basic.py** - ✅ 26/26 tests passing

### 🔄 NEXT PRIORITY:
4. **test_generate_text_job.py** - Model schema issues + missing imports
5. **test_job_system_integration.py** - Similar issues + missing os import

### ⏳ LOWER PRIORITY:
6. **test_bot_initialization.py** - Bot ordering logic
7. **test_job_utils.py** - Assertion issues

## Systematic Fix Approach

### Phase 1: High Success Rate Files ✅ COMPLETED
Fixed files using standardized patterns with excellent success rates (18-26/26 tests passing)

### Phase 2: API and Authentication Issues ✅ COMPLETED  
Fixed critical authentication and API integration issues in test_basic.py

### Phase 3: Complex Schema Files 🔄 NEXT
Files with model schema issues but also additional complexities

## Standard Fix Patterns

### Pattern 1: Model Schema Updates
```python
# OLD (broken):
chunk = Chunk(
    book_id=book_id,
    title='Test Scene',
    content='Some content',
    type='scene'
)

# NEW (working):
chunk = Chunk(
    book_id=book_id,
    props={'title': 'Test Scene'},
    text='Some content',
    type='scene'
)
```

### Pattern 2: Session Management 
```python
# OLD (broken):
def setup_test_data(self, app):
    # ... create objects ...
    return {
        'scene_chunk': scene_chunk,  # Returns object - causes DetachedInstanceError
        'bot_chunk': bot_chunk
    }

# NEW (working):
def setup_test_data(self, app):
    # ... create objects ...
    db.session.commit()  # Ensure objects are persisted
    return {
        'scene_chunk': scene_chunk,
        'bot_chunk': bot_chunk,
        'scene_chunk_id': scene_chunk.chunk_id,  # Return IDs for cross-session use
        'bot_chunk_id': bot_chunk.chunk_id
    }
```

### Pattern 3: ID Usage Corrections
```python
# OLD (broken):
job_props = {
    'chunk_id': scene_chunk.id,  # Wrong ID type - uses primary key
    'bot_id': bot_chunk.id
}

# NEW (working):
job_props = {
    'chunk_id': scene_chunk.chunk_id,  # Correct - uses UUID string
    'bot_id': bot_chunk.chunk_id
}
```

### Pattern 4: Job Method Updates
```python
# OLD (broken):
generate_job.run()

# NEW (working):
generate_job.execute()
```

### Pattern 5: Props Parsing for Complex Cases
When bot props are stored as JSON strings:
```python
def _get_props(self, chunk: Chunk) -> Dict[str, Any]:
    """Get chunk props as dictionary, handling both dict and JSON string formats."""
    if isinstance(chunk.props, dict):
        return chunk.props
    elif isinstance(chunk.props, str):
        try:
            return json.loads(chunk.props)
        except (json.JSONDecodeError, TypeError):
            return {}
    else:
        return {}
```

## Fix Statistics

- **Total Test Files:** 7
- **Files Fixed:** 2 ✅
- **Files In Progress:** 1 🔄  
- **Files Pending:** 4 ⏳
- **Tests Now Passing:** 19 (8 + 11)
- **Estimated Total Tests:** ~80-100

## Known Working Solutions

1. **SQLAlchemy DetachedInstanceError:** Return IDs from setup methods, use `filter_by()` to reload objects
2. **Model Schema:** Use `props={'title': value}` and `text=` instead of `title=` and `content=`
3. **Job Execution:** Use `execute()` method instead of `run()`
4. **Chunk Lookups:** Use `chunk_id` (UUID) for job system, `id` for direct DB queries
5. **Complex Props:** Handle both dict and JSON string formats with helper methods

## Next Steps

1. ✅ Complete `test_job_system_integration.py` 
2. ⏳ Fix `test_generate_text_job.py` (may need architectural changes)
3. ⏳ Address `test_basic.py` DetachedInstanceError issues
4. ⏳ Fix remaining logic and assertion issues
