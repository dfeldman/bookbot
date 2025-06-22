Let's look at the "bot management" system. Right now, all the text for a book is stored in "chunks" of type "scene", and then bots (essentially just an LLM system prompt + selected type of LLM) are stored in "chunks" of type "bot". The nice thing about using chunks for both is that version history, search (future), export to json (future) will transparently apply to both of them. But the frontend interface for changing bots should look a bit different. 
1) System prompt should not be a property of the chunk, it should be in the Content portion. 
2) Remove the LLM Alias field from the bot. 
3) We should have a new Chunk Type called BotTask. Tasks should also show up on the Bots tab, under a separate section. BotTasks allow selecting the MAIN prompt. BotTask should have a Jobs field with a comma-separated list of the jobs that the task makes sense for. Tasks should have a field LLM Group which should contain one of Writer, Editor, Reviewer, Thinker, Explicit. There should be a nice editor screen for BotTasks too even though they are also stored as Chunks (and could be edited with the generic Chunk Editor). The content of a BotTask is a template for the main prompt that is used to execute that taks. 
NOTE - We forgot to add Explicit as one of the bot groups. 
4) The most common activity in the entire app is generating the text for a chunk. To do this, the user will use a StartJob vue component (not yet written). 
Select a job type - GenerateChunk . (This will be the default and by far the most common.)
Select a Bot. This dropdown should show all the avaiable bots. 
Select a Task. This dropdown should show all the BotTasks that are available for the GenerateChunk job type. (Most of them will be, but not all). 
Select an LLM. This should be a dropdown of all the LLMs from teh LLMPicker API, but the default should be the user's choice for that bot group from the book preferences. The LLMPicker API can return this as well.
Click Generate. This starts a new GenerateChunk Job with the user's chosen Bot, Task, and LLM, and the chunk ID of course as arguments. ANother argument it needs is the target word count, which should come from a chunk prop (or default to 500, a good default). It also needs a Temperature, which should come from the Bot.  
When executing, this job uses the Bot for the system prompt, the BotTask for the main prompt, and the Bot for the system prompt and temperature. 

Filling in the template for the BotTask:
The BotTask will have several template fields that can be filled in:
{{ PreviousChunk }} -- should come by resolving the preiovus chunk, if available
{{ NextChunk }} -- should come by resolving teh next chunk, if avaiable
{{ CurrentVersion }} -- Text from the current version of the chunk (makes sense for editing, where there is already a current version - of course when initially generating, this is likely empty)
{{ Review }} -- This shoudl come from a "review" prop on the chunk. These will be generated later, currently never set. 
{{ Brief }} -- from the global "brief" chunk
{{ OutlineSection }} -- from a field on the chunkc ontext in the chunk/id/context endpoint (already computed and avaiable to the frontend)
{{ SettingsSections }} -- from a field on the chunk context in the chunk/id/context endpoint (already computed and avaiable to the frontend)
{{ CharactersSections }} -- from a field on the chunk context in the chunk/id/context endpoint (already computed and avaiable to the frontend)
{{ Style }} -- from the global style chunk

Resolving the contents of these template variables will happen on the server side, as part of the GenerateChunk job. It will take a number of database queries and should probably be in a utility module called generate_chunk_utils.py. 

BotTasks will be preconfigured for the user from a config file at Create Foundation time like Bots currently are. 

The goal is that for most text generation, the user will have full control of the system prompt (bot), main prompt (task), and LLM that are used, as well as key properties like expected word count and temperature, and be able to save and reuse these choices. There will be some jobs that are not customizable because they use advanced functioanltiy that is tricker to customize, but this should apply for all the GenerateChunk jobs. 

All backend and frontend code should have passing tests. Backend tests are pytest and are in backend/tests, and frontend tests are in vitest and are in frontend/tests. There are no integration tests, and we'll only do that later after the core functionality is basically working (so don't do it now). Running make test will run all tests, or make frontend-test or make backend-test to only run frontend or backend. Note that your context space is very limited so you may want to run one test at a time to diagnose failures when there are many errors.

Please commit all changes to Git after there are major changes. That way we can backtrack. Do not worry about checking too much into Git, we can prune later. 

Try to generally use small files (<400 lines). When they are larger, editing using diffs gets much more complex. Don't worry about having too many files.

There is also a python cli api client in cli/ which eventually should have matching functionality to the Vue web frontend.

Longer term plans: add drag-and-drop reordering of chunks, adding and deleting chunks from index view, get the Read screen working where you can read the book chapter-by-chapter instead of chunk-by-chunk, add jobs to auto-generate the entire book instead of one chunk at a time and edit the entire book instead of one at a time, add a review system where any chunk can be reviewed by one task and applied by a separate tasks, add a user settings screen to set your API token and a few other global preferences, get the user authentication to actually work with Google login, add Postgres database support instead of just SQLite, add multiple job runner threads instead of one, and finally add export mode where you can export your finished book as an epub file. Don't do these yet, just keep them in mind as future projects. Oh and we'll eventually have a complete integration test with Playwright.






Next steps:
FoundationGenerate jobs and UI 
- run a task/bot/llm selection on just one SECTION of  these chunks
Fix word count
- Target word count is currently a prop on the chunk. The canonical copy should be stored in the outline like the text, and not editable in the chunk.
- Show word count in the index view




no, don't think about the cover designer yet. Instead, write bottask intialization that works exactly like bot initialization (from a yaml file). BotTasks have an LLMGroup, applicable jobs, and then the template content. After that, we need to improve generate_chunk.py to fully support template variables: 
{{ PreviousChunk }} -- should come by resolving the preiovus chunk, if available
{{ NextChunk }} -- should come by resolving teh next chunk, if avaiable
{{ CurrentVersion }} -- Text from the current version of the chunk (makes sense for editing, where there is already a current version - of course when initially generating, this is likely empty)
{{ Review }} -- This shoudl come from a "review" prop on the chunk. These will be generated later, currently never set. 
{{ Brief }} -- from the global "brief" chunk
{{ OutlineSection }} -- from a field on the chunkc ontext in the chunk/id/context endpoint (already computed and avaiable to the frontend)
{{ SettingsSections }} -- from a field on the chunk context in the chunk/id/context endpoint (already computed and avaiable to the frontend)
{{ CharactersSections }} -- from a field on the chunk context in the chunk/id/context endpoint (already computed and avaiable to the frontend)
{{ Style }} -- from the global style chunk


These will be in the bottask content, we just need to fill them in. 
As a special feature, can we add this: 
If the template contains {{ Text goes here | PreviousChunk }}, then if the previous chunk is empty, it should NOT inlcude "Text goes here." If it does, it should resovle to "Text goes here <previous chunk text>". This will help with properly formatting task prompt inputs (since often we want to include a sentence ONLY IF the previous text is available (maybe it doesn't exist at all, it would confuse the LLM to include). THank you.
