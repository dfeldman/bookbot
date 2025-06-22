//drag and drop system from an older version of the app

document.addEventListener('DOMContentLoaded', function() {
    let draggedElement = null;
    let draggedChapter = null;
    let dragStartIndex = -1;
    
    console.log('Drag and drop initialized.');
    
    const sceneItems = document.querySelectorAll('.scene-item[draggable="true"]');
    const sceneContainers = document.querySelectorAll('.scenes-container');
    
    // Add event listeners to scene items
    sceneItems.forEach((item, index) => {
        item.addEventListener('dragstart', function(e) {
            // console.log(`DRAGSTART on scene ${index}:`, this.dataset.chunkId);
            handleDragStart.call(this, e);
        });
        
        item.addEventListener('dragend', function(e) {
            // console.log(`DRAGEND on scene ${index}:`, this.dataset.chunkId);
            handleDragEnd.call(this, e);
        });
        
        item.addEventListener('dragover', function(e) {
            e.preventDefault(); 
            // console.log('DRAGOVER on scene item:', this.dataset.chunkId);
        });
        
        item.addEventListener('dragenter', function(e) {
            e.preventDefault(); 
            // console.log('DRAGENTER on scene item:', this.dataset.chunkId);
        });
        
        item.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation(); 
            // console.log('DROP on scene item - delegating to container:', this.dataset.chunkId);
            const container = this.closest('.scenes-container');
            if (container) {
                handleDrop.call(container, e); 
            }
        });
        
    });
    
    // Add comprehensive event listeners to containers
    sceneContainers.forEach((container, index) => {
        container.addEventListener('dragenter', function(e) {
            e.preventDefault();
            // console.log('DRAGENTER on container:', this.dataset.chapter);
        });
        
        container.addEventListener('dragover', function(e) {
            // console.log('DRAGOVER on container:', this.dataset.chapter);
            handleDragOver.call(this, e);
        });
        
        container.addEventListener('drop', function(e) {
            // console.log(`DROP on container ${index}:`, this.dataset.chapter);
            handleDrop.call(this, e);
        });
        
        container.addEventListener('dragleave', function(e) {
            // console.log('DRAGLEAVE on container:', this.dataset.chapter);
            if (!this.contains(e.relatedTarget) || e.relatedTarget === null) {
                this.classList.remove('drag-valid', 'drag-invalid');
                const dragIndicator = this.querySelector('.drag-placeholder.visible');
                if (dragIndicator) {
                    dragIndicator.classList.remove('visible');
                }
                // console.log('Cleaned up container on dragleave:', this.dataset.chapter);
            }
        });
    });
    
    function handleDragStart(e) {
        console.log('Drag Start:', this.dataset.chunkId);
        
        draggedElement = this;
        draggedChapter = this.dataset.chapter;
        
        const container = this.closest('.scenes-container');
        const sceneItemsInContainer = container.querySelectorAll('.scene-item');
        dragStartIndex = Array.from(sceneItemsInContainer).indexOf(this);
        
        this.classList.add('dragging');
        document.body.classList.add('dragging');
        
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.dropEffect = 'move';
        e.dataTransfer.setData('text/plain', this.dataset.chunkId);
        e.dataTransfer.setData('text/html', this.outerHTML);
        
        // console.log('Drag data set:', { chunkId: this.dataset.chunkId, chapter: draggedChapter, startIndex: dragStartIndex });
        
        document.querySelectorAll('.chapter-section').forEach(section => {
            if (section.dataset.chapter === draggedChapter) {
                section.classList.add('drag-valid-target');
                const container = section.querySelector('.scenes-container');
                if (container) {
                    container.classList.add('drag-valid');
                }
            } else {
                section.classList.add('drag-invalid-target');
                const container = section.querySelector('.scenes-container');
                if (container) {
                    container.classList.add('drag-invalid');
                }
            }
        });
        
        // console.log('Visual feedback applied');
    }
    
    function handleDragOver(e) {
        e.preventDefault(); 
        e.stopPropagation(); 
        
        // console.log('DRAGOVER event on container:', this.dataset.chapter, 'dragged chapter:', draggedChapter);
        
        const dragIndicator = this.querySelector('.drag-placeholder');

        if (draggedElement && this.dataset.chapter === draggedChapter) {
            e.dataTransfer.dropEffect = 'move';
            this.classList.add('drag-valid');
            this.classList.remove('drag-invalid');
            
            const afterElement = getDragAfterElement(this, e.clientY);
            
            if (dragIndicator) {
                if (afterElement) {
                    this.insertBefore(dragIndicator, afterElement);
                } else {
                    this.appendChild(dragIndicator); 
                }
                dragIndicator.classList.add('visible');
            }
            // console.log('Drop allowed on container:', this.dataset.chapter);
        } else {
            e.dataTransfer.dropEffect = 'none';
            this.classList.add('drag-invalid');
            this.classList.remove('drag-valid');
            if (dragIndicator && dragIndicator.classList.contains('visible')) {
                dragIndicator.classList.remove('visible');
            }
            // console.log('Drop NOT allowed on container:', this.dataset.chapter);
        }
    }
    
    function handleDrop(e) {
        console.log('Drop Event on chapter:', this.dataset.chapter);
        e.preventDefault();
        e.stopPropagation();
        
        const targetContainer = this; // 'this' is the scenes-container

        // Capture the element and its data at the time of the drop,
        // as global draggedElement might be cleared by dragend before async operations complete.
        const elementToMove = draggedElement;
        const chapterOfDraggedElement = draggedChapter; // Capture chapter associated with the drag operation
        const startIndexForThisDrop = dragStartIndex; // Capture start index for this specific drop operation

        // Critical: Check if elementToMove is valid early on.
        if (!elementToMove) {
            console.error("DROP HANDLER: draggedElement (elementToMove) is null at the start of handleDrop.");
            const indicator = targetContainer.querySelector('.drag-placeholder.visible');
            if (indicator) indicator.classList.remove('visible');
            return false; 
        }
        const chunkIdToReorder = elementToMove.dataset.chunkId; 

        // console.log('Dragged chapter (captured):', chapterOfDraggedElement);
        // console.log('Element to move:', chunkIdToReorder);
        
        const dragIndicator = targetContainer.querySelector('.drag-placeholder');
        if (dragIndicator && dragIndicator.classList.contains('visible')) {
            dragIndicator.classList.remove('visible');
        }

        if (targetContainer.dataset.chapter === chapterOfDraggedElement) {
            const afterElement = getDragAfterElement(targetContainer, e.clientY);
            
            const sceneItemsInContainer = Array.from(targetContainer.querySelectorAll('.scene-item:not(.dragging)'));
            let newPosition;
            if (afterElement == null) {
                newPosition = sceneItemsInContainer.length;
            } else {
                newPosition = sceneItemsInContainer.indexOf(afterElement);
            }
            
            // console.log('Calculated positions:', {newPosition, originalPosition: startIndexForThisDrop});
            
            let effectivelySamePosition = false;
            if (elementToMove.parentElement && targetContainer === elementToMove.parentElement) { 
                 if (newPosition === startIndexForThisDrop) {
                    const originalNextSibling = elementToMove.nextElementSibling;
                    if (afterElement === originalNextSibling || (afterElement === null && originalNextSibling && originalNextSibling.classList.contains('drag-placeholder'))) {
                        effectivelySamePosition = true;
                    }
                 }
            }

            if (!effectivelySamePosition) {
                const bookId = targetContainer.dataset.bookId;

                if (!bookId) {
                    console.error("Book ID not found on container for reorder operation.");
                    return;
                }

                console.log(`API Call: Reorder chunk ${chunkIdToReorder} to position ${newPosition} in chapter ${chapterOfDraggedElement}`);
                reorderScene(chunkIdToReorder, bookId, newPosition, chapterOfDraggedElement)
                    .then(result => {
                        if (result.success) {
                            console.log('API Success: Reordered', chunkIdToReorder);

                            if (elementToMove.parentElement) {
                                elementToMove.parentElement.removeChild(elementToMove);
                            }

                            if (afterElement == null) {
                                targetContainer.insertBefore(elementToMove, targetContainer.querySelector('.drag-placeholder'));
                            } else {
                                targetContainer.insertBefore(elementToMove, afterElement);
                            }
                            // console.log('DOM element moved:', elementToMove, 'New parent:', elementToMove.parentElement);
                        } else {
                            console.error('API Failure:', result.error, `(Chunk ID: ${chunkIdToReorder})`);
                        }
                    })
                    .catch(error => {
                        console.error('API Call Exception:', error, `(Chunk ID: ${chunkIdToReorder})`);
                    });
            } else {
                console.log('No reorder needed (same position).');
                if (!elementToMove.parentElement) { 
                    // console.warn('Dragged element (elementToMove) was detached but drop was same position. Re-inserting.');
                    if (afterElement == null) {
                        targetContainer.insertBefore(elementToMove, targetContainer.querySelector('.drag-placeholder'));
                    } else {
                        targetContainer.insertBefore(elementToMove, afterElement);
                    }
                }
            }
        } else {
            console.log('Drop rejected (wrong chapter or invalid element).');
        }
        
        return false;
    }
    
    function handleDragEnd(e) {
        console.log('Drag End:', this.dataset.chunkId);
        
        if (this.classList.contains('dragging')) {
            this.classList.remove('dragging');
        }
        document.body.classList.remove('dragging');
        
        // Remove visual feedback classes
        document.querySelectorAll('.chapter-section').forEach(section => {
            section.classList.remove('drag-valid-target', 'drag-invalid-target');
        });
        
        document.querySelectorAll('.scenes-container').forEach(container => {
            container.classList.remove('drag-valid', 'drag-invalid');
        });
        
        // Hide all drag placeholders
        document.querySelectorAll('.drag-placeholder').forEach(placeholder => {
            placeholder.classList.remove('visible');
        });
        
        // Reset state
        draggedElement = null;
        draggedChapter = null;
        dragStartIndex = -1;
        
        // console.log('Drag state reset');
    }
    
    function getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.scene-item:not(.dragging)')];
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }
    
    async function reorderScene(chunkId, bookId, newPosition, chapter) {
        try {
            const response = await fetch('/api/reorder_scene', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Add CSRF token headers if your application uses them
                    // Example: 'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    chunk_id: chunkId,
                    book_id: bookId,
                    new_position: newPosition, // 0-based index
                    chapter: parseInt(chapter) // Ensure chapter is an integer
                })
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Failed to parse error response' }));
                console.error('Fetch Error in reorderScene:', response.status, errorData);
                throw new Error(errorData.error || `Failed to reorder scene (status ${response.status})`);
            }
            const result = await response.json();
            // console.log('Scene reordered successfully via API:', result);
            return result; 
        } catch (error) {
            console.error('Exception in reorderScene function:', error);
            throw error; 
        }
    }
    
    // console.log('=== INITIALIZATION COMPLETE ===');
    
    // Remove test function and its invocation
    // window.testDragSetup = function() { ... };
    // setTimeout(() => { ... }, 1000);
});
