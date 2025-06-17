Please create the Python Flask backend for an AI-based book writing assistant called BookBot. Here are the specs:

User authentication and authorization: In the future we will redirect the user to a Google login before having them load the SPA, and for each API call call is_authorized_to_edit or is_authorized_to_read for every API call using a decorator. This is not needed yet and we can just return true for both in all cases, but leave room for adding it later. 

SPA endpoint: The API should be able to serve the JS and HTML SPA files, which will be copied in by a makefile. It should also have a config endpoint that tells the SPA where the backend is and a few other key config details. 

Database: We will start with SQLite, but move to Postgres in the future. So we need a good data model, BUT it shouldn't rely on any really advanced features. Most objects are just an ID and a props field, which is a JSON object that has most of the real data so it can be easily updated or downloaded by the client. In the future we will be adding many more fields since this is a growing application, and this keeps it flexible. We also want to support data import/export in the future and this will make that relatively easy.

Tables:

Users:
UserID, props 

Books:
UserID, BookID, props, isLocked, job

Chunks: 
Chunks are the heart of BookBot and store the actual book text. Each Chunk represents a "chunk" of text, which may be the outline, metadata, or actual words for the final book. 

The fields are:
BookID, ChunkID, version, isLatest, props, text, type, isLocked, isDeleted, job, order float, chapter, wordCount
Chunks are versioned. We never edit existing versions, we create a new version instead. This should be enforced in the API. To stop there from being too many copies, there is a "clean up old versions" call that deletes old versions of the chunk. This isn't a full version control system or anything, there's no branching, commit messages, etc. isDeleted is a soft delete and should apply to EVERY version of a chunk. 
Type is a short free text field. 
Props stores all the metadata about the chunk - tags, references to other chunks, etc. 
Text is the actual plaintext of the chunk in Markdown format. This may be up to a few KB so we don't always return it when listing lots of chunks.
There will be many types of chunks in the future, so we want to keep this super flexible. They may display differently in the UI but will all be the same to the backend.
The book is split into chapters, primarily so we don't have to download all the chunks for the entire book every time we want to edit it. The chapter number may be changed at any time. There is no guarantee chapters are linear. 
WordCount is a count of the words in the chunk. It should be recomputed every time the chunk text is updated. We FREQUENTLY display the whole word count of a chapter or a book so this is a separate column to be really easy.

OutputFiles: 
These are for exporting the final contents of the book in PDF, Markdown, Word format etc. We should have a directory for storing them, and the DB should just record the filename. Each OutputFile is associated with a BookID. 

Jobs:
The core goal of the app is to generate text with LLMs. This is done in the backend in backend threads because it can take a while. SO there will be a backend job processing thread, and the SPA will be able to create jobs by posting to an endpoint, get a list of all running jobs, check status, read job logs, etc. 
There are three main supertypes of jobs:
Chunk jobs take a chunk as input, and ultimately new text and props for that chunk, and put their ID in the job field and set the isLocked field on the chunk.
Book jobs make broader changes to the entire book. They lock the entire book while in use and set their ID in the job field for the book. 
Finally, export jobs do not lock anything while running. They just create output files. 
All jobs are associated with a book, not with a user. 

So we have a table like this:
Jobs
BookID, JobID, jobType, props, state
State can be waiting, running, or complete.
The job processor should wake every ~1 second and look for waiting jobs, and start them. 
There will be 5-10 different job types, each is a chunk job, book job, or export job. 

JobLogs
JobID, logEntry

So the basic API endpoints should be :
GET /auth (authenticaitonn redirect, for now just redirects to teh spa endpoint)
GET /config - returns the configuration for the SPA - right now, not much is needed here, but in the future it could contain the API URL or other important system config data

For books:
PUT, GET, UPDATE, DELETE
List all books for the current user
When a book is deleted, we should delete all its chunks, jobs, and job logs. 


For chunks 
PUT, GET, UPDATE, DELETE
List all chunks WITHOUT text
List all chunks WITH text
Both should support getting only non-deleted chunks, or also getting deleted chunks
GET should support getting any version of a chunk
PUT should update the version number, remove isLatest from all other versions of teh same chunk, and set it on the new version
DELETE should do the soft-delete on all versions of the chunk only. 
A CLEANUP_OLD_VERSIONS endpoint deletes all versions of a chunk that are N prior to the current version. 
A CLEANUP_DELETED deletes soft-deleted versions. 
If a book is deleted, all its chunks and jobs should be deleted immediately (not soft-deleted).

For jobs:
POST to start a job
GET, DELETE jobs
List all the jobs for a book
Server-sent event for job polling 

Job logs:
A key feature of the app is that for any job, we can see the entire LLM conversation. And chunks are linked to jobs, so we can click a chunk, view the assocaited job, and view teh LLM conversation that lead to it. 
An endpoint should list all the jobs for a book, or all that are currently running. Aspecial API call shoudl stop the job. 

Authentication:
There should be an API decorator that takes the bookID specified in teh API call and determines whether the user is allowed to view or edit it. For now, both should always be true. All authenticaiton is at the book level. In the future, multiple users may be able to view or edit the same book. 
CSRF: We should have CSRF, but keep it disabled in developer mode for now. 

Build system: 
The SPA will be in Vue 3. I'd like a single makefile that can build the SPA, run tests on the backend, and run the backend since both will be developed together. There will also be integration tests in the future to run. There should be a frontend/ folder but we don't need to populate it yet. 

Testing: Every API endpoint should have a corresponding unit test. 

Config: There should be a config file to specify the database connection string and a few other key global details like an admin API key (in the future, this will override the authentication and give the user access to everything). 

Job scaffolding: For now, we're not actually implementing any jobs. But we should have nice scaffolding that runs a job with the appropriate props depending on whether it's a book job, chunk job, or export job. And make it easy for the job to log things as it goes along, which should go both to the console and teh job log table.. Also if a job produces an exception, it should be logged. We should have a callback to check if the current job has been canceled, and return early. We should have a DemoJob to make sure this all works.

LLM module:
There should be an LLM.py module. This will be called by the jobs to actually execute the LLMs. 
LLM calls include as inputs
Model
API key
Target word count
Model mode - This is a prop on the book that may or may not exist. If it exists, it can override the model behavior, usually for the end user to run a cheaper model for testing. The fact that it is overridden is logged, but otherwise there is no change to the behavior. 
It should have a callback for logging as it goes along (since a single job might have many individual LLM calls)
And return 
Output text
Input tokens
Output tokens
Cost (dollars)
Stop reason
Execution time (seconds)
Error status 
So each LLM call should be an object, with an execute() call to actually run, since there are multple inputs and outputes. 

Second, llm.py should have a get_api_token_status which takes an API token, and returns the user's remaining balance in dollars for that API token, or an error if the API token does not work.

Fake model:
llm.py should, for now, call out to a fake_llm.py that generates lorem ipsum text. In the future it will support using OpenRouter to route LLM requests to many different models, btu that is not implemented. Using the fake_llm.py should always happen if the model mode is "fake". But for now it should ALWAYS happen since we haven't mplemnted the OpenRouter part.  

Status endpoint:
Nearly every screen in the final app will have a status bar that shows:
The user's currently-running or last completed job, with all details and its status
The user's current API token balance
Number of chunks in the current book
The current word count of the book - this is just the sum of the word counts of all chunks where isLatestVersion = true
Since this will be on almost every screen, we should have a nice endpoint to just return those values as a JSON structure given a book ID. 

Code structure: 
The code should be professionally-written with an easy-to-understand structure. We're just writing the Python for now. It should use docstrings, a makefile with venvs, types when appropriate, and have a nice documentation file for the API user. 

Tests: 
We will write unit tests in a subsequent step. The code should be completely unit-testable with places to put mocks as needed, e.g. to replace LLM calls. We will iterate until all unit tests pass.

THank you very much.
