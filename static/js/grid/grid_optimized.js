// Grid JavaScript - Optimized Version
class GridManager {
    constructor() {
        // Only initialize on desktop - don't interfere with mobile
        if (window.innerWidth < 769) {
            return;
        }
        
        this.state = {
            currentCol: 0,
            dataColWidth: 0,
            totalDataColumns: 0,
            columnsToShow: 3,
            isDropdownOpen: false,
            currentTaskId: null,
            currentDeleteUrl: null,
            // Drag and drop state
            isDragging: false,
            draggedElement: null,
            dragStartY: 0,
            dragStartX: 0,
            originalOrder: [],
            dragPlaceholder: null,
            aboutToDrag: false,
            dragStartElement: null,
            targetTask: null,
            dropAfter: null,
            originalLeft: 0,
            originalTop: 0,
            originalWidth: 0,
            originalHeight: 0,
            dragClone: null,
            lastLiveReorder: null,
            // Scroll state
            isScrollingToEnd: false
        };
        
        this.elements = {};
        this.observers = new Map();
        this.eventListeners = new Map();

        
        this.init();
    }

    // Cache DOM elements to avoid repeated queries
    cacheElements() {
        const selectors = {
            // Project switcher
            switcherBtn: '#project-switcher-btn',
            switcherDropdown: '#project-switcher-dropdown',
            switcherChevron: '#switcher-chevron',
            switcherContainer: '#project-switcher-container',
            
            // Grid scrolling
            scrollable: '.grid-table-scrollable',
            leftBtn: '.left-scroll-btn',
            rightBtn: '.right-scroll-btn',
            gridTable: '.grid-table',
            dataCols: 'col.data-column',
            gridContent: '#grid-content',
            
            // Modals
            deleteModal: '#delete-task-modal',
            deleteModalContent: '#delete-modal-content',
            taskToDelete: '#task-to-delete',
            deleteTaskForm: '#delete-task-form',
            closeDeleteModal: '#close-delete-modal',
            cancelDeleteTask: '#cancel-delete-task',
            modal: '#modal',
            modalContent: '#modal-content',
            
            // Rows
            fixedRows: '.grid-table-fixed tr',
            scrollRows: '.grid-table-scrollable .grid-table tr',
            
            // Sticky headers
            fixedTable: '.grid-table-fixed',
            dataTable: '.grid-table',
            
            // Drag and drop
            draggableTasks: '[draggable="true"]',
            taskContainers: '[data-row][data-col]'
        };

        Object.keys(selectors).forEach(key => {
            const selector = selectors[key];
            if (selector.includes('All') || key.includes('Rows') || key === 'dataCols' || key === 'draggableTasks' || key === 'taskContainers') {
                this.elements[key] = document.querySelectorAll(selector);
            } else {
                this.elements[key] = document.querySelector(selector);
            }
        });
    }

    // Unified event listener management
    addEventListeners() {
        const listeners = [
            // Document level events
            ['document', 'click', this.handleDocumentClick.bind(this)],
                        ['document', 'keydown', this.handleKeydown.bind(this)],
            ['document', 'htmx:beforeRequest', this.handleHtmxBeforeRequest.bind(this)],
            ['document', 'htmx:afterRequest', this.handleHtmxAfterRequest.bind(this)],
            ['document', 'htmx:afterSwap', this.handleHtmxAfterSwap.bind(this)],
            ['document', 'htmx:afterSettle', this.handleHtmxAfterSettle.bind(this)],
            ['document', 'htmx:responseError', this.handleHtmxError.bind(this)],
            ['document', 'htmx:sendError', this.handleHtmxError.bind(this)],
            
            // Window level events
            ['window', 'resize', this.handleWindowResize.bind(this)],
            
            // Body level events
            ['body', 'openModal', this.showModal.bind(this)],
            ['body', 'closeModal', this.hideModal.bind(this)],
            ['body', 'refreshGrid', this.handleRefreshGrid.bind(this)],
            ['body', 'scrollToEnd', this.handleScrollToEnd.bind(this)],
            ['body', 'resetGridToInitial', this.handleResetGridToInitial.bind(this)]
        ];

        listeners.forEach(([target, event, handler]) => {
            const element = target === 'document' ? document : 
                           target === 'window' ? window : document.body;
            element.addEventListener(event, handler);
            
            // Store for cleanup
            if (!this.eventListeners.has(element)) {
                this.eventListeners.set(element, []);
            }
            this.eventListeners.get(element).push({ event, handler });
        });

        // Add explicit scrollToEnd listener for HTMX triggers
        document.addEventListener('scrollToEnd', (e) => {
            this.handleScrollToEnd();
        });

        // Also listen for HTMX trigger events (multiple ways HTMX can trigger events)
        document.addEventListener('htmx:trigger', (e) => {
            if (e.detail.trigger === 'scrollToEnd') {
                this.handleScrollToEnd();
            }
        });

        // Listen for HTMX header triggers (HX-Trigger header from server)
        document.body.addEventListener('htmx:afterRequest', (e) => {
            if (e.detail.xhr && e.detail.xhr.getResponseHeader('HX-Trigger')) {
                const triggers = e.detail.xhr.getResponseHeader('HX-Trigger');
                if (triggers && triggers.includes('scrollToEnd')) {
                    this.handleScrollToEnd();
                    return;
                }
                if (triggers && triggers.includes('refreshGrid')) {
                    this.handleRefreshGrid();
                    return;
                }
                if (triggers && triggers.includes('resetGridToInitial')) {
                    this.handleResetGridToInitial();
                    return;
                }
            }
        });

        // Add drag and drop event listeners
        this.setupDragAndDrop();
    }

    // Setup drag and drop functionality
    setupDragAndDrop() {
        // Only enable drag and drop on desktop
        if (window.innerWidth < 769) {
            return;
        }
        
        // Initialize SortableJS on all task containers
        this.initializeSortable();
    }

    // Initialize SortableJS on all task containers
    initializeSortable() {
        // Find all task containers
        const taskContainers = document.querySelectorAll('[data-row][data-col]');
        
        taskContainers.forEach(container => {
            // Initialize SortableJS for drag and drop
            new Sortable(container, {
                // Only allow dragging from the drag handle
                handle: '.drag-handle',
                
                // Enable drag and drop
                sort: true,
                
                // Animation duration
                animation: 150,
                
                // Drag class for the item being dragged
                dragClass: 'sortable-drag',
                
                // Allow dragging between all containers (rows and columns)
                group: 'tasks',
                
                // Callback when sorting ends
                onEnd: (evt) => {
                    // Get the new order across all containers
                    const newOrder = this.getTaskOrder();
                    
                    // Save to server
                    this.saveTaskOrder(newOrder);
                }
            });
        });
    }



    // handleDragEnd(e) {
    //     if (!this.state.isDragging) return;

    //     console.log('GridManager: Drag end event triggered');

    //     this.state.isDragging = false;
        
    //     if (this.state.draggedElement) {
    //         this.state.draggedElement.classList.remove('dragging');
    //         this.state.draggedElement.style.opacity = '';
    //         this.state.draggedElement.style.transform = '';
    //     }

    //     // Remove placeholder
    //     this.removeDragPlaceholder();

    //     // Clear drag state
    //     this.state.draggedElement = null;
    //     this.state.dragStartY = 0;
    //     this.state.aboutToDrag = false;
    //     this.state.dragStartElement = null;
        
    //     console.log('GridManager: Drag end completed');
    // }

    // handleDragOver(e) {
    //     if (!this.state.isDragging) return;

    //     console.log('GridManager: Drag over event triggered');

    //     e.preventDefault();
    //     e.dataTransfer.dropEffect = 'move';

    //     const taskContainer = e.target.closest('[data-row][data-col]');
    //     if (!taskContainer) {
    //         console.log('GridManager: No task container found');
    //         return;
    //     }

    //     const draggedElement = this.state.draggedElement;
    //     if (!draggedElement) {
    //         console.log('GridManager: No dragged element found');
    //         return;
    //     }

    //     // Check if we're in the same container
    //     const draggedRow = draggedElement.dataset.taskRow;
    //     const draggedCol = draggedElement.dataset.taskCol;
    //     const containerRow = taskContainer.dataset.row;
    //     const containerCol = taskContainer.dataset.col;

    //     if (draggedRow !== containerRow || draggedCol !== containerCol) {
    //         console.log('GridManager: Different container, ignoring');
    //         return;
    //     }

    //     // Find the target position - look for task elements, not drag handles
    //     const targetTask = e.target.closest('[data-task-id]');
        
    //     if (!targetTask || targetTask === draggedElement) {
    //         console.log('GridManager: No valid target task found');
    //         return;
    //     }

    //     // Calculate drop position
    //     const rect = targetTask.getBoundingClientRect();
    //     const dropAfter = e.clientY > rect.top + rect.height / 2;

    //     console.log('GridManager: Updating placeholder position');

    //     // Update placeholder position
    //     this.updateDragPlaceholder(targetTask, dropAfter);
    // }

    // handleDrop(e) {
    //     if (!this.state.isDragging) return;

    //     console.log('GridManager: Drop event triggered');

    //     e.preventDefault();

    //     const taskContainer = e.target.closest('[data-row][data-col]');
    //     if (!taskContainer) {
    //         console.log('GridManager: No task container found for drop');
    //         return;
    //     }

    //     const draggedElement = this.state.draggedElement;
    //     if (!draggedElement) {
    //         console.log('GridManager: No dragged element found for drop');
    //         return;
    //     }

    //     // Check if we're in the same container
    //     const draggedRow = draggedElement.dataset.taskRow;
    //     const draggedCol = draggedElement.dataset.taskCol;
    //     const containerRow = taskContainer.dataset.row;
    //     const containerCol = taskContainer.dataset.col;

    //     if (draggedRow !== containerRow || draggedCol !== containerCol) {
    //         console.log('GridManager: Different container for drop, ignoring');
    //         return;
    //     }

    //     // Find the target position - look for task elements, not drag handles
    //     const targetTask = e.target.closest('[data-task-id]');
        
    //     if (!targetTask || targetTask === draggedElement) {
    //         console.log('GridManager: No valid target task found for drop');
    //         return;
    //     }

    //     // Calculate drop position
    //     const rect = targetTask.getBoundingClientRect();
    //     const dropAfter = e.clientY > rect.top + rect.height / 2;

    //     console.log('GridManager: Reordering tasks');

    //     // Reorder tasks
    //     this.reorderTasks(draggedElement, targetTask, dropAfter);
    // }

    handleDragEnter(e) {
        if (!this.state.isDragging || this.state.isScrollingToEnd) return;

        const taskContainer = e.target.closest('[data-row][data-col]');
        if (taskContainer) {
            taskContainer.classList.add('drag-over');
        }
    }

    handleDragLeave(e) {
        if (!this.state.isDragging || this.state.isScrollingToEnd) return;

        const taskContainer = e.target.closest('[data-row][data-col]');
        if (taskContainer && !taskContainer.contains(e.relatedTarget)) {
            taskContainer.classList.remove('drag-over');
        }
    }

    // Create drag placeholder
    createDragPlaceholder(originalElement) {
        this.state.dragPlaceholder = originalElement.cloneNode(true);
        this.state.dragPlaceholder.classList.add('drag-placeholder');
        this.state.dragPlaceholder.style.opacity = '0.5';
        this.state.dragPlaceholder.style.border = '2px dashed var(--primary-action-bg)';
        this.state.dragPlaceholder.style.backgroundColor = 'var(--grid-header-bg)';
        this.state.dragPlaceholder.style.minHeight = '40px';
        this.state.dragPlaceholder.style.margin = '4px 0';
        this.state.dragPlaceholder.removeAttribute('draggable');
        
        // Remove interactive elements from placeholder
        const interactiveElements = this.state.dragPlaceholder.querySelectorAll('button, input, form, .drag-handle');
        interactiveElements.forEach(el => el.remove());

        originalElement.parentNode.insertBefore(this.state.dragPlaceholder, originalElement);
    }

    // Update drag placeholder position
    updateDragPlaceholder(targetTask, dropAfter) {
        if (!this.state.dragPlaceholder) return;

        if (dropAfter) {
            targetTask.parentNode.insertBefore(this.state.dragPlaceholder, targetTask.nextSibling);
        } else {
            targetTask.parentNode.insertBefore(this.state.dragPlaceholder, targetTask);
        }
    }

    // Remove drag placeholder
    removeDragPlaceholder() {
        if (this.state.dragPlaceholder) {
            this.state.dragPlaceholder.remove();
            this.state.dragPlaceholder = null;
        }

        // Remove drag-over classes
        document.querySelectorAll('.drag-over').forEach(el => {
            el.classList.remove('drag-over');
        });
    }



    // Get current task order
    getTaskOrder() {
        const order = [];
        
        // Query all task elements in their current DOM order. This order reflects
        // the result of the drag-and-drop action performed by SortableJS.
        const allTasks = document.querySelectorAll('[data-task-id]');
        
        // Filter to only include the main task container elements (not text, buttons, etc.)
        const mainTaskContainers = Array.from(allTasks).filter(task => {
            // Only include elements that are the main task container (have the main task classes)
            return task.classList.contains('group') && 
                   task.classList.contains('flex') && 
                   task.classList.contains('items-center') && 
                   task.classList.contains('justify-between') && 
                   task.classList.contains('w-full') && 
                   task.classList.contains('p-2') && 
                   task.classList.contains('rounded-lg');
        });
        
        // First pass: group tasks by container
        const tasksByContainer = {};
        mainTaskContainers.forEach(task => {
            const currentContainer = task.closest('[data-row][data-col]');
            if (!currentContainer) {
                return; 
            }

            const currentRow = currentContainer.dataset.row;
            const currentCol = currentContainer.dataset.col;
            const containerKey = `${currentRow}-${currentCol}`;
            
            if (!tasksByContainer[containerKey]) {
                tasksByContainer[containerKey] = [];
            }
            tasksByContainer[containerKey].push(task);
        });
        
        // Second pass: process each container separately to get correct order
        Object.keys(tasksByContainer).forEach(containerKey => {
            const [row, col] = containerKey.split('-');
            const containerTasks = tasksByContainer[containerKey];
            
            // Sort tasks by their actual DOM position within the container
            containerTasks.sort((a, b) => {
                const container = a.closest('[data-row][data-col]');
                const allTasksInContainer = Array.from(container.querySelectorAll('[data-task-id]')).filter(child => 
                    child.classList.contains('group') && 
                    child.classList.contains('flex') && 
                    child.classList.contains('items-center') && 
                    child.classList.contains('justify-between') &&
                    child.classList.contains('w-full') &&
                    child.classList.contains('p-2') &&
                    child.classList.contains('rounded-lg')
                );
                return allTasksInContainer.indexOf(a) - allTasksInContainer.indexOf(b);
            });
            
            // Add tasks with their correct order within the container
            containerTasks.forEach((task, containerIndex) => {
                const taskId = task.dataset.taskId;
                const actualOrder = containerIndex;
                
                order.push({
                    task_id: taskId,
                    row_header: row,
                    column_header: col,
                    order: actualOrder
                });
            });
        });
        
        return order;
    }

    // Save task order to server
    saveTaskOrder(newOrder) {
        const projectId = this.getProjectId();
        if (!projectId) return;

        // Create the request data
        const requestData = {
            task_order: newOrder
        };

        // Send request to server
        fetch(`/grids/${projectId}/tasks/reorder/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to save task order');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Update task order attributes and row/column data
                this.updateTaskOrderAttributes(newOrder);
            } else {
                // Revert to original order
                this.revertToOriginalOrder();
            }
        })
        .catch(error => {
            // Revert to original order
            this.revertToOriginalOrder();
        });
    }

    // Get project ID from URL
    getProjectId() {
        const urlParts = window.location.pathname.split('/');
        const gridsIndex = urlParts.indexOf('grids');
        if (gridsIndex >= 0 && gridsIndex + 1 < urlParts.length) {
            return urlParts[gridsIndex + 1];
        }
        return null;
    }

    // Get CSRF token
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    // Update task order attributes
    updateTaskOrderAttributes(newOrder) {
        newOrder.forEach((task, index) => {
            const taskElement = document.querySelector(`[data-task-id="${task.task_id}"]`);
            if (taskElement) {
                const oldOrder = taskElement.dataset.taskOrder;
                const oldRow = taskElement.dataset.taskRow;
                const oldCol = taskElement.dataset.taskCol;
                
                taskElement.dataset.taskOrder = task.order.toString();
                // Update row and column data attributes to reflect new position
                taskElement.dataset.taskRow = task.row_header;
                taskElement.dataset.taskCol = task.column_header;
            }
        });
    }

    // Update task order attributes in a specific container based on DOM position
    updateTaskOrderAttributesInContainer(container) {
        const tasks = Array.from(container.querySelectorAll('[data-task-id]'));
        tasks.forEach((task, index) => {
            task.dataset.taskOrder = index.toString();
        });
    }

    // Revert to original order
    revertToOriginalOrder() {
        if (!this.state.originalOrder.length) return;

        // This is a simplified revert - in a real implementation,
        // you might want to reload the page or implement a more sophisticated revert
        // For now, just show an error message
        this.showReorderError();
    }

    // Show reorder error
    showReorderError() {
        // Create a temporary error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        errorDiv.textContent = 'Failed to save task order. Please try again.';
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 3000);
    }

    // Verify that the DOM order matches the saved order
    verifyOrder(savedOrder, domOrder) {
        if (savedOrder.length !== domOrder.length) {
            console.error('GridManager: Order length mismatch:', savedOrder.length, 'vs', domOrder.length);
            return false;
        }
        
        for (let i = 0; i < savedOrder.length; i++) {
            const saved = savedOrder[i];
            const dom = domOrder[i];
            
            if (saved.task_id !== dom.task_id || saved.row_header !== dom.row_header || saved.column_header !== dom.column_header || saved.order !== dom.order) {
                console.error('GridManager: Order mismatch at index', i, ':', saved, 'vs', dom);
                return false;
            }
        }
        
        return true;
    }





    // Unified click handler to reduce event listeners
    handleDocumentClick(e) {
        // Modal triggers - clear content immediately before HTMX loads new content
        const modalTrigger = e.target.closest('[hx-target="#modal-content"]');
        if (modalTrigger) {
            this.clearModalContent();
            this.showModal();
        }

        // Project switcher
        if (e.target.closest('#project-switcher-btn')) {
            e.stopPropagation();
            this.toggleProjectSwitcher();
            return;
        }

        // Close project switcher if clicking outside
        if (!e.target.closest('#project-switcher-container')) {
            this.closeProjectSwitcher();
        }

        // Task deletion
        const taskDeleteBtn = e.target.closest('.delete-task-btn');
        if (taskDeleteBtn) {
            e.preventDefault();
            this.showDeleteModal(
                taskDeleteBtn.dataset.taskId,
                taskDeleteBtn.dataset.taskText,
                taskDeleteBtn.dataset.deleteUrl
            );
            return;
        }

        // Modal close buttons
        const closeModalBtn = e.target.closest('.close-modal, #close-delete-modal, #cancel-delete-task');
        if (closeModalBtn) {
            // Determine which modal to close based on the button
            if (closeModalBtn.id === 'close-delete-modal' || closeModalBtn.id === 'cancel-delete-task') {
                this.hideDeleteModal();
            } else if (closeModalBtn.classList.contains('close-modal')) {
                this.hideModal();
            }
            return;
        }

        // Close modals when clicking outside
        if (e.target === this.elements.deleteModal) {
            this.hideDeleteModal();
        }
        if (e.target === this.elements.modal) {
            this.hideModal();
        }

        // Task edit buttons - no longer need column tracking since we update in place

        // Add task forms
        const addTaskTrigger = e.target.closest('.add-task-trigger');
        if (addTaskTrigger) {
            e.preventDefault();
            this.expandAddTaskForm(addTaskTrigger.closest('.add-task-form'));
            return;
        }

        const addTaskCancel = e.target.closest('.add-task-cancel');
        if (addTaskCancel) {
            e.preventDefault();
            this.collapseAddTaskForm(addTaskCancel.closest('.add-task-form'));
            return;
        }

        // Close add task forms when clicking outside
        if (!e.target.closest('.add-task-form')) {
            this.collapseAllAddTaskForms();
        }

        // Handle task completion checkbox clicks (fallback for hyperscript issues)
        const checkbox = e.target.closest('input[type="checkbox"][name="completed"]');
        if (checkbox) {
            const form = checkbox.closest('form');
            if (form && form.hasAttribute('hx-post')) {
                // Let HTMX handle the request, but apply visual changes immediately
                const taskId = checkbox.id.replace('checkbox-', '');
                const taskText = document.getElementById(`task-text-${taskId}`);
                
                if (taskText) {
                    if (checkbox.checked) {
                        checkbox.classList.add('checkbox-completed');
                        taskText.classList.add('task-completed-strikethrough');
                    } else {
                        checkbox.classList.remove('checkbox-completed');
                        taskText.classList.remove('task-completed-strikethrough');
                    }
                }
            }
        }
    }

    // Unified keyboard handler
    handleKeydown(e) {
        if (e.key === 'Escape') {
            this.closeProjectSwitcher();
            this.hideDeleteModal();
            this.hideModal();
            this.collapseAllAddTaskForms();
        }
    }

    // Project switcher methods
    toggleProjectSwitcher() {
        if (!this.elements.switcherDropdown) return;
        
        this.state.isDropdownOpen = !this.state.isDropdownOpen;
        this.updateProjectSwitcherUI();
    }

    closeProjectSwitcher() {
        if (this.state.isDropdownOpen) {
            this.state.isDropdownOpen = false;
            this.updateProjectSwitcherUI();
        }
    }

    updateProjectSwitcherUI() {
        const { switcherDropdown, switcherChevron, switcherBtn } = this.elements;
        if (!switcherDropdown) return;

        const classes = this.state.isDropdownOpen 
            ? { remove: ['opacity-0', 'invisible', 'scale-95'], add: ['opacity-100', 'visible', 'scale-100'] }
            : { remove: ['opacity-100', 'visible', 'scale-100'], add: ['opacity-0', 'invisible', 'scale-95'] };

        switcherDropdown.classList.remove(...classes.remove);
        switcherDropdown.classList.add(...classes.add);
        
        if (switcherChevron) {
            switcherChevron.style.transform = this.state.isDropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)';
        }
        
        if (switcherBtn) {
            switcherBtn.classList.toggle('ring-2', this.state.isDropdownOpen);
            switcherBtn.classList.toggle('ring-[var(--primary-action-bg)]/20', this.state.isDropdownOpen);
        }
    }

    // Function to close all dropdowns - called from inline onclick handlers
    closeAllDropdowns() {
        this.closeProjectSwitcher();
    }

    // Modal methods
    showDeleteModal(taskId, taskText, deleteUrl) {
        this.state.currentTaskId = taskId;
        this.state.currentDeleteUrl = deleteUrl;
        
        if (this.elements.taskToDelete) {
            this.elements.taskToDelete.textContent = taskText;
        }
        if (this.elements.deleteTaskForm) {
            this.elements.deleteTaskForm.action = deleteUrl;
            // Set HTMX attribute for proper handling
            this.elements.deleteTaskForm.setAttribute('hx-post', deleteUrl);
            
            // Tell HTMX to process the form with the new attributes
            if (typeof htmx !== 'undefined') {
                htmx.process(this.elements.deleteTaskForm);
            }
        }
        
        this.setModalState(this.elements.deleteModal, this.elements.deleteModalContent, true);
        
        // Focus cancel button for accessibility
        setTimeout(() => this.elements.cancelDeleteTask?.focus(), 100);
    }

    hideDeleteModal() {
        this.setModalState(this.elements.deleteModal, this.elements.deleteModalContent, false);
        this.state.currentTaskId = null;
        this.state.currentDeleteUrl = null;
    }

    showModal() {
        this.setModalState(this.elements.modal, this.elements.modalContent, true);
    }

    hideModal() {
        this.setModalState(this.elements.modal, this.elements.modalContent, false);
    }

    clearModalContent() {
        if (this.elements.modalContent) {
            // Show loading state instead of previous content
            this.elements.modalContent.innerHTML = `
                <div class="flex items-center justify-center p-8">
                    <div class="flex items-center space-x-3">
                        <div class="animate-spin w-6 h-6 border-2 border-[var(--primary-action-bg)] border-t-transparent rounded-full"></div>
                        <span class="text-[var(--text-secondary)]">Loading...</span>
                    </div>
                </div>
            `;
        }
    }

    setModalState(modal, content, isOpen) {
        if (!modal || !content) return;

        if (isOpen) {
            modal.classList.remove('opacity-0', 'invisible');
            modal.classList.add('opacity-100', 'visible');
            content.classList.remove('scale-95');
            content.classList.add('scale-100');
        } else {
            modal.classList.add('opacity-0', 'invisible');
            modal.classList.remove('opacity-100', 'visible');
            content.classList.add('scale-95');
            content.classList.remove('scale-100');
        }
    }

    // Add task form methods
    expandAddTaskForm(form) {
        if (!form) return;
        
        // First, collapse all other add task forms
        this.collapseAllAddTaskForms();
        
        const collapsed = form.querySelector('.add-task-collapsed');
        const expanded = form.querySelector('.add-task-expanded');
        const input = form.querySelector('input[name="text"]');

        if (collapsed && expanded) {
            collapsed.style.display = 'none';
            expanded.classList.remove('hidden');
            
            setTimeout(() => input?.focus(), 100);
        }
    }

    collapseAddTaskForm(form) {
        if (!form) return;
        
        const collapsed = form.querySelector('.add-task-collapsed');
        const expanded = form.querySelector('.add-task-expanded');
        const input = form.querySelector('input[name="text"]');
        const errorDiv = form.querySelector('.error-message');

        if (collapsed && expanded) {
            collapsed.style.display = 'block';
            expanded.classList.add('hidden');
            
            if (input) {
                input.value = '';
                input.classList.remove('border-red-500');
                input.classList.add('border-[var(--inline-input-border)]');
            }
            if (errorDiv) {
                errorDiv.innerHTML = '';
            }
        }
    }

    collapseAllAddTaskForms() {
        document.querySelectorAll('.add-task-form').forEach(form => {
            this.collapseAddTaskForm(form);
        });
    }

    // Determine responsive column count based on screen size
    getResponsiveColumnCount() {
        const screenWidth = window.innerWidth;
        
        if (screenWidth <= 480) {
            return 1; // Mobile: 1 column
        } else if (screenWidth <= 768) {
            return 2; // Tablet: 2 columns  
        } else {
            return 3; // Desktop: Maximum 3 columns (never more than 3)
        }
    }

    // Grid scrolling methods
    setupGridScrolling(skipRestore = false) {
        const { scrollable, leftBtn, rightBtn, gridTable } = this.elements;
        if (!scrollable || !leftBtn || !rightBtn || !gridTable) {
            console.warn('Grid elements not found, retrying...');
            // Retry after a short delay
            setTimeout(() => {
                this.cacheElements();
                this.setupGridScrolling(skipRestore);
            }, 100);
            return;
        }

        // Always get fresh column count from DOM
        const dataCols = document.querySelectorAll('.data-column');
        this.elements.dataCols = dataCols;
        
        if (!dataCols.length) {
            console.warn('No data columns found');
            return;
        }

        const dataTotalColumns = parseInt(gridTable.dataset.totalDataColumns);
        const dataColsLength = dataCols.length;
        this.state.totalDataColumns = dataTotalColumns || dataColsLength;
        this.state.columnsToShow = Math.min(this.getResponsiveColumnCount(), this.state.totalDataColumns);

        // Setup scroll buttons (only if not already set)
        if (!leftBtn.onclick) {
            leftBtn.onclick = (e) => {
                e.preventDefault();
                // Use instant scrolling for button clicks for better responsiveness
                this.scrollToCol(this.state.currentCol - 1, 'auto');
            };
            rightBtn.onclick = (e) => {
                e.preventDefault();
                // Use instant scrolling for button clicks for better responsiveness
                this.scrollToCol(this.state.currentCol + 1, 'auto');
            };
            
            // Add touch support for mobile
            leftBtn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.scrollToCol(this.state.currentCol - 1, 'auto');
            });
            rightBtn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.scrollToCol(this.state.currentCol + 1, 'auto');
            });
        }

        // Setup resize observer (only once)
        if (!this.observers.has('resize')) {
            const resizeObserver = new ResizeObserver(() => {
                const currentScrollLeft = scrollable.scrollLeft;
                
                // Recalculate column count based on new screen size
                const newColumnCount = this.getResponsiveColumnCount();
                if (newColumnCount !== this.state.columnsToShow) {
                    this.state.columnsToShow = Math.min(newColumnCount, this.state.totalDataColumns);
                    // Adjust current column to stay within bounds
                    this.state.currentCol = Math.min(this.state.currentCol, 
                        Math.max(0, this.state.totalDataColumns - this.state.columnsToShow));
                }
                
                this.calculateAndApplyWidths();
                // Restore exact scroll position after resize
                scrollable.scrollLeft = currentScrollLeft;
                this.updateScrollButtons();
            });
            resizeObserver.observe(scrollable);
            this.observers.set('resize', resizeObserver);
        }

        // Add scroll event listener for mobile touch scrolling
        if (!this.observers.has('scroll')) {
            let scrollTimeout;
            let isScrolling = false;
            
            const scrollHandler = () => {
                // Don't update scroll state if we're programmatically scrolling to end
                if (this.state.isScrollingToEnd) return;
                
                // Set scrolling flag to prevent multiple updates
                if (!isScrolling) {
                    isScrolling = true;
                }
                
                // Debounce scroll events for better performance
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    if (this.state.dataColWidth > 0) {
                        const newCurrentCol = Math.round(scrollable.scrollLeft / this.state.dataColWidth);
                        if (newCurrentCol !== this.state.currentCol) {
                            this.state.currentCol = newCurrentCol;
                            this.updateScrollButtons();
                        }
                    }
                    isScrolling = false;
                }, 16); // ~60fps debouncing
            };
            
            // Use passive listeners for better performance on mobile
            scrollable.addEventListener('scroll', scrollHandler, { passive: true });
            this.observers.set('scroll', { 
                disconnect: () => {
                    clearTimeout(scrollTimeout);
                    scrollable.removeEventListener('scroll', scrollHandler);
                } 
            });
        }

        // Calculate widths and update UI without causing flash
        this.calculateAndApplyWidths();
        this.updateScrollButtons();
        
        // Only restore position on initial load or explicit requests
        if (!skipRestore) {
            this.restoreScrollPosition();
        }

        // Make table visible after setup to prevent FOUC
        if (this.elements.gridTable) {
            this.elements.gridTable.classList.add('initialized');
        }
    }

    calculateAndApplyWidths() {
        const { scrollable, gridTable, dataCols } = this.elements;
        if (!scrollable || !dataCols.length) return;

        if (this.state.columnsToShow > 0) {
            // Get the total grid container width (including category column)
            const gridContainer = scrollable.closest('.grid-container-wrapper');
            const totalGridWidth = gridContainer ? gridContainer.clientWidth : scrollable.clientWidth;
            
            // Get the category column width from CSS custom property
            const getCategoryColumnWidth = () => {
                // Try to get from grid container first, then fallback to document root
                const gridContainer = scrollable.closest('.grid-container-wrapper');
                let computedStyle, categoryColWidth;
                
                if (gridContainer) {
                    computedStyle = getComputedStyle(gridContainer);
                    categoryColWidth = computedStyle.getPropertyValue('--category-col-width');
                }
                
                // Fallback to document root if not found in grid container
                if (!categoryColWidth) {
                    computedStyle = getComputedStyle(document.documentElement);
                    categoryColWidth = computedStyle.getPropertyValue('--category-col-width');
                }
                
                // Parse the CSS value (e.g., "225px" -> 225)
                const parsedWidth = parseInt(categoryColWidth) || 225;
                return parsedWidth; // Fallback to 225 if parsing fails
            };
            
            const categoryColumnWidth = getCategoryColumnWidth();
            
            // Calculate available width for data columns (total width minus category column)
            const availableWidth = totalGridWidth - categoryColumnWidth;
            
            // Ensure we have the correct number of columns visible based on screen size
            const minColumnsToShow = this.getResponsiveColumnCount();
            this.state.columnsToShow = Math.min(minColumnsToShow, this.state.totalDataColumns);
            
            // If all columns are visible (no scrolling needed), distribute width evenly
            if (this.state.totalDataColumns <= this.state.columnsToShow) {
                // All columns are visible, distribute available width evenly
                this.state.dataColWidth = availableWidth / this.state.totalDataColumns;
            } else {
                // Only some columns are visible, calculate width for visible columns
                this.state.dataColWidth = availableWidth / this.state.columnsToShow;
            }
            
            // Apply the same width to all data columns to ensure they're equal
            dataCols.forEach((col, index) => {
                col.style.width = `${this.state.dataColWidth}px`;
                col.style.minWidth = `${this.state.dataColWidth}px`;
                col.style.maxWidth = `${this.state.dataColWidth}px`;
            });

            // Set the total table width to accommodate all columns
            const totalTableWidth = this.state.dataColWidth * this.state.totalDataColumns;
            gridTable.style.width = `${totalTableWidth}px`;
            gridTable.style.minWidth = `${totalTableWidth}px`;
        }
        
        this.syncRowHeights();
    }

    scrollToCol(colIdx, behavior = 'smooth') {
        const { scrollable } = this.elements;
        if (!scrollable) return;

        // Ensure we have valid column data
        if (this.state.totalDataColumns <= 0 || this.state.dataColWidth <= 0) {
            // Recalculate if needed
            this.calculateAndApplyWidths();
        }

        // Calculate the target column index, ensuring it's within bounds
        const maxCol = Math.max(0, this.state.totalDataColumns - 1);
        const targetCol = Math.max(0, Math.min(colIdx, maxCol));
        
        // Don't scroll if we're already at the target column
        if (targetCol === this.state.currentCol) return;
        
        // Update state immediately for responsive UI
        this.state.currentCol = targetCol;
        
        // Calculate scroll position
        const scrollLeft = targetCol * this.state.dataColWidth;
        
        // Perform the scroll with optimized behavior
        if (behavior === 'smooth') {
            // Use smooth scrolling for better UX
            scrollable.scrollTo({ left: scrollLeft, behavior: 'smooth' });
        } else {
            // Use instant scrolling for immediate response
            scrollable.scrollLeft = scrollLeft;
        }
        
        // Update scroll buttons immediately
        this.updateScrollButtons();
        
        // Only verify scroll position for smooth scrolling
        if (behavior === 'smooth') {
            setTimeout(() => {
                if (Math.abs(scrollable.scrollLeft - scrollLeft) > 5) {
                    // Force scroll if it didn't work properly
                    scrollable.scrollLeft = scrollLeft;
                }
            }, 100); // Increased timeout for smooth scrolling
        }
    }

    updateScrollButtons() {
        const { leftBtn, rightBtn } = this.elements;
        if (!leftBtn || !rightBtn) return;

        // Cache current state to avoid unnecessary updates
        const shouldHideButtons = this.state.totalDataColumns <= this.state.columnsToShow;
        const leftDisabled = this.state.currentCol === 0;
        const rightDisabled = this.state.currentCol >= this.state.totalDataColumns - this.state.columnsToShow;
        
        // Only update if there are actual changes
        if (shouldHideButtons) {
            if (leftBtn.style.display !== 'none') {
                leftBtn.style.display = rightBtn.style.display = 'none';
                leftBtn.disabled = rightBtn.disabled = true;
            }
        } else {
            if (leftBtn.style.display !== 'flex') {
                leftBtn.style.display = rightBtn.style.display = 'flex';
            }
            
            // Only update disabled state if it changed
            if (leftBtn.disabled !== leftDisabled) {
                leftBtn.disabled = leftDisabled;
            }
            if (rightBtn.disabled !== rightDisabled) {
                rightBtn.disabled = rightDisabled;
            }
        }
    }

    syncRowHeights() {
        const { fixedRows, scrollRows } = this.elements;
        if (fixedRows.length !== scrollRows.length) return;

        for (let i = 0; i < fixedRows.length; i++) {
            const fixedCell = fixedRows[i].querySelector('td, th');
            const scrollCell = scrollRows[i].querySelector('td, th');
            
            if (fixedCell && scrollCell) {
                fixedCell.style.height = scrollCell.style.height = 'auto';
                const maxH = Math.max(fixedCell.offsetHeight, scrollCell.offsetHeight);
                fixedCell.style.height = scrollCell.style.height = `${maxH}px`;
            }
        }
    }

    restoreScrollPosition() {
        const scrollToEnd = sessionStorage.getItem('scrollToEnd');
        const savedPosition = sessionStorage.getItem('grid-scroll-position');
        const resetToInitial = sessionStorage.getItem('resetToInitial');
        
        if (resetToInitial) {
            sessionStorage.removeItem('resetToInitial');
            // Force reset to column 0
            this.state.currentCol = 0;
            this.scrollToCol(0, 'auto');
            return;
        } else if (scrollToEnd) {
            sessionStorage.removeItem('scrollToEnd');
            // Set flag to prevent mouse interference
            this.state.isScrollingToEnd = true;
            
            // Use a more robust approach with multiple attempts
            this.performScrollToEnd();
        } else if (savedPosition) {
            sessionStorage.removeItem('grid-scroll-position');
            // Restore saved position immediately for smoother experience
            const savedScrollLeft = parseFloat(savedPosition);
            if (this.elements.scrollable && savedScrollLeft > 0) {
                // Ensure the grid is properly initialized before restoring position
                setTimeout(() => {
                    this.elements.scrollable.scrollLeft = savedScrollLeft;
                    // Update current column state to match restored position
                    this.state.currentCol = this.state.dataColWidth > 0 
                        ? Math.round(savedScrollLeft / this.state.dataColWidth) 
                        : 0;
                    this.updateScrollButtons();
                }, 50);
            }
        } else {
            // Default to start, ensure first column is fully visible
            this.state.currentCol = 0;
            if (this.elements.scrollable) {
                this.elements.scrollable.scrollLeft = 0;
                // Add a small delay to ensure the scroll position is properly set
                setTimeout(() => {
                    if (this.elements.scrollable.scrollLeft !== 0) {
                        this.elements.scrollable.scrollLeft = 0;
                    }
                    // Ensure the first column is fully visible by checking scroll position
                    if (this.elements.scrollable.scrollLeft > 0) {
                        this.elements.scrollable.scrollLeft = 0;
                    }
                }, 10);
            }
            this.updateScrollButtons();
        }
    }

    // Separate method for performing scroll to end with multiple attempts
    performScrollToEnd() {
        // Set a higher priority flag to ensure this takes precedence
        this.state.isScrollingToEnd = true;
        
        // Wait for DOM to be stable and recalculate
        setTimeout(() => {
            // Recalculate total columns from actual DOM
            const dataColumns = document.querySelectorAll('.data-column');
            const actualColumnCount = dataColumns.length;
            
            console.log('ScrollToEnd: Found', actualColumnCount, 'columns');
            
            if (actualColumnCount > 0) {
                this.state.totalDataColumns = actualColumnCount;
                // Update the grid table data attribute
                if (this.elements.gridTable) {
                    this.elements.gridTable.dataset.totalDataColumns = actualColumnCount;
                }
                
                // Recalculate widths to ensure proper column sizing
                this.calculateAndApplyWidths();
                
                // Force a small delay to ensure widths are properly applied
                setTimeout(() => {
                    // Scroll to show the very last column
                    const lastColIndex = Math.max(0, this.state.totalDataColumns - 1);
                    console.log('ScrollToEnd: Scrolling to column', lastColIndex, 'of', this.state.totalDataColumns);
                    
                    this.state.currentCol = lastColIndex;
                    
                    // Calculate exact scroll position to show the last column
                    const scrollLeft = lastColIndex * this.state.dataColWidth;
                    console.log('ScrollToEnd: Calculated scroll position:', scrollLeft, 'px (column width:', this.state.dataColWidth, 'px)');
                    
                    // Apply the scroll with multiple attempts to ensure it works
                    if (this.elements.scrollable) {
                        // First attempt: instant scroll
                        this.elements.scrollable.scrollLeft = scrollLeft;
                        
                        // Second attempt: force scroll after a short delay
                        setTimeout(() => {
                            if (this.elements.scrollable && this.state.isScrollingToEnd) {
                                this.elements.scrollable.scrollLeft = scrollLeft;
                                console.log('ScrollToEnd: Forced scroll position:', this.elements.scrollable.scrollLeft, 'px');
                            }
                        }, 50);
                        
                        // Third attempt: final verification and correction
                        setTimeout(() => {
                            if (this.elements.scrollable && this.state.isScrollingToEnd) {
                                const currentScroll = this.elements.scrollable.scrollLeft;
                                const expectedScroll = lastColIndex * this.state.dataColWidth;
                                
                                console.log('ScrollToEnd: Final verification - Current scroll:', currentScroll, 'px, Expected:', expectedScroll, 'px');
                                
                                // If scroll position is still off, force it one more time
                                if (Math.abs(currentScroll - expectedScroll) > 5) {
                                    console.log('ScrollToEnd: Final scroll position correction');
                                    this.elements.scrollable.scrollLeft = expectedScroll;
                                    
                                    // Update the current column state to match
                                    this.state.currentCol = lastColIndex;
                                }
                            }
                            
                            // Clear the scrolling flag only after all attempts
                            this.state.isScrollingToEnd = false;
                        }, 200);
                    }
                    
                    // Update scroll buttons
                    this.updateScrollButtons();
                }, 100);
            } else {
                this.scrollToCol(0, 'auto');
                // Clear the scrolling flag
                this.state.isScrollingToEnd = false;
            }
        }, 300); // Increased timeout to ensure DOM is fully ready
    }

    handleScrollToEnd() {
        // For new columns, we need to refresh to get the updated grid structure
        sessionStorage.setItem('scrollToEnd', 'true');
        
        // Force a reload to get the updated grid structure
        // This ensures we have the correct column count and can scroll properly
        window.location.reload();
    }

    handleRefreshGrid() {
        // Save current scroll position before refresh
        if (this.elements.scrollable) {
            sessionStorage.setItem('grid-scroll-position', this.elements.scrollable.scrollLeft.toString());
        }
        window.location.reload();
    }

    handleResetGridToInitial() {
        // Clear any stored scroll position to ensure we start fresh
        sessionStorage.removeItem('grid-scroll-position');
        sessionStorage.removeItem('scrollToEnd');
        
        // Set flag to explicitly reset to initial state
        sessionStorage.setItem('resetToInitial', 'true');
        
        // Reset the grid state to initial position
        this.state.currentCol = 0;
        
        // Also clear any scroll position on the scrollable element before refresh
        if (this.elements.scrollable) {
            this.elements.scrollLeft = 0;
        }
        
        // Refresh the grid to reflect the column deletion and reset position
        window.location.reload();
    }

    handleWindowResize() {
        // Debounce resize events
        if (this.resizeTimeout) {
            clearTimeout(this.resizeTimeout);
        }
        
        this.resizeTimeout = setTimeout(() => {
            const newColumnCount = this.getResponsiveColumnCount();
            if (newColumnCount !== this.state.columnsToShow) {
                this.state.columnsToShow = Math.min(newColumnCount, this.state.totalDataColumns);
                // Adjust current column to stay within bounds
                this.state.currentCol = Math.min(this.state.currentCol, 
                    Math.max(0, this.state.totalDataColumns - this.state.columnsToShow));
                
                // Recalculate and apply new widths
                this.calculateAndApplyWidths();
                this.updateScrollButtons();
            }
        }, 100);
    }

    // Handle column/row header updates
    updateColumnHeader(columnId, newName) {
        const columnHeaders = document.querySelectorAll(`[data-column-id="${columnId}"]`);
        columnHeaders.forEach(header => {
            const nameElement = header.querySelector('span.font-semibold');
            if (nameElement) {
                nameElement.textContent = newName;
            }
            
            // Also update any inline editable column headers
            const editableHeader = header.querySelector('.column-header-editable');
            if (editableHeader) {
                editableHeader.textContent = newName;
                editableHeader.setAttribute('data-original-text', newName);
            }
        });
    }

    updateRowHeader(rowId, newName) {
        const rowHeaders = document.querySelectorAll(`[data-row-id="${rowId}"]`);
        rowHeaders.forEach(header => {
            const nameElement = header.querySelector('span.font-semibold');
            if (nameElement) {
                nameElement.textContent = newName;
            }
            
            // Also update any inline editable row headers
            const editableHeader = header.querySelector('.row-header-editable');
            if (editableHeader) {
                editableHeader.textContent = newName;
                editableHeader.setAttribute('data-original-text', newName);
            }
        });
    }

    // No sticky header functionality

    // Task edit column tracking no longer needed since we update in place

    // HTMX event handlers
    handleHtmxBeforeRequest(e) {
        // Method for handling HTMX before request events if needed
    }

    handleHtmxAfterRequest(e) {
        const url = e.detail.requestConfig?.url || e.target?.getAttribute('hx-post') || e.target?.getAttribute('hx-get') || 'unknown';
        const method = e.detail.requestConfig?.verb || e.detail.requestConfig?.type || 
                      (e.target?.getAttribute('hx-post') ? 'post' : 
                       e.target?.getAttribute('hx-get') ? 'get' : 'unknown');
        
        // Check for HX-Trigger header first (for column creation and row creation)
        if (e.detail.successful && e.detail.xhr) {
            const triggerHeader = e.detail.xhr.getResponseHeader('HX-Trigger');
            if (triggerHeader) {
                if (triggerHeader.includes('scrollToEnd')) {
                    this.handleScrollToEnd();
                    return;
                }
                if (triggerHeader.includes('refreshGrid')) {
                    this.handleRefreshGrid();
                    return;
                }
                if (triggerHeader.includes('resetGridToInitial')) {
                    this.handleResetGridToInitial();
                    return;
                }
            }
        }
        
        // Check for column creation specifically
        if (e.detail.successful && method === 'post' && url.includes('/columns/create/')) {
            // When a new column is created, we need to scroll to the end
            // Temporarily disable interactions to prevent interruption
            this.disableInteractionsDuringScroll();
            
            // Use a small delay to ensure the DOM is updated
            setTimeout(() => {
                this.forceScrollToEnd();
            }, 100);
            return;
        }
        
        // Only handle POST requests for form submissions
        if (e.detail.successful && (method === 'post' || method === 'POST') && e.detail.xhr.responseText) {
            // Store scroll position for form submissions
            const gridScrollable = document.querySelector('.grid-table-scrollable');
            const currentScrollLeft = gridScrollable ? gridScrollable.scrollLeft : 0;
            
            try {
                const response = JSON.parse(e.detail.xhr.responseText);
                
                if (response.success) {
                    // Check if this is a column update
                    if ((url.includes('/columns/') && url.includes('/edit/')) || url.match(/\/columns\/\d+\/edit\//)) {
                        // Extract column ID from URL
                        let columnId = null;
                        const urlMatch = url.match(/\/columns\/(\d+)\//);
                        if (urlMatch) {
                            columnId = urlMatch[1];
                        } else {
                            const urlParts = url.split('/');
                            const columnIndex = urlParts.indexOf('columns');
                            if (columnIndex >= 0 && columnIndex + 1 < urlParts.length) {
                                columnId = urlParts[columnIndex + 1];
                            }
                        }
                        
                        if (columnId && response.col_name) {
                            // Update column headers in place
                            this.updateColumnHeader(columnId, response.col_name);
                            this.hideModal();
                            
                            // Restore scroll position
                            setTimeout(() => {
                                if (gridScrollable) {
                                    gridScrollable.scrollLeft = currentScrollLeft;
                                    // Update grid manager's internal state to match
                                    if (this.state.dataColWidth > 0) {
                                        this.state.currentCol = Math.round(currentScrollLeft / this.state.dataColWidth);
                                        this.updateScrollButtons();
                                    }
                                }
                            }, 50);
                            return;
                        }
                    }
                    
                    // Check if this is a row update
                    if ((url.includes('/rows/') && url.includes('/edit/')) || url.match(/\/rows\/\d+\/edit\//)) {
                        // Extract row ID from URL
                        let rowId = null;
                        const urlMatch = url.match(/\/rows\/(\d+)\//);
                        if (urlMatch) {
                            rowId = urlMatch[1];
                        } else {
                            const urlParts = url.split('/');
                            const rowIndex = urlParts.indexOf('rows');
                            if (rowIndex >= 0 && rowIndex + 1 < urlParts.length) {
                                rowId = urlParts[rowIndex + 1];
                            }
                        }
                        
                        if (rowId && response.row_name) {
                            // Update row headers in place
                            this.updateRowHeader(rowId, response.row_name);
                            this.hideModal();
                            
                            // Restore scroll position
                            setTimeout(() => {
                                if (gridScrollable) {
                                    gridScrollable.scrollLeft = currentScrollLeft;
                                    // Update grid manager's internal state to match
                                    if (this.state.dataColWidth > 0) {
                                        this.state.currentCol = Math.round(currentScrollLeft / this.state.dataColWidth);
                                        this.updateScrollButtons();
                                    }
                                }
                            }, 50);
                            return;
                        }
                    }
                }
            } catch (err) {
                // Not JSON or not a form response - this is normal for GET requests that return HTML
            }
        }

        // Handle task deletion from delete modal
        if (e.detail.successful &&
            e.target.id === 'delete-task-form' &&
            e.detail.requestConfig.verb === 'post') {

            // Get the task ID that was being deleted
            const taskId = this.state.currentTaskId;
            
            if (taskId) {
                // Remove the task element from DOM
                const taskElement = document.getElementById(`task-${taskId}`);
                if (taskElement) {
                    // Store current scroll position before removal
                    const gridScrollable = document.querySelector('.grid-table-scrollable');
                    const currentScrollLeft = gridScrollable ? gridScrollable.scrollLeft : 0;
                    
                    // Remove the task with animation
                    taskElement.style.transition = 'all 0.3s ease';
                    taskElement.style.opacity = '0';
                    taskElement.style.transform = 'scale(0.95)';
                    
                    setTimeout(() => {
                        taskElement.remove();
                        
                        // Restore scroll position
                        if (gridScrollable && currentScrollLeft > 0) {
                            gridScrollable.scrollLeft = currentScrollLeft;
                        }
                        
                        // Sync row heights after removal, preserving scroll position
                        setTimeout(() => {
                            this.syncRowHeights();
                            // Ensure scroll position is maintained after height sync
                            if (gridScrollable && currentScrollLeft > 0) {
                                gridScrollable.scrollLeft = currentScrollLeft;
                                // Update grid manager's internal state to match
                                if (this.state.dataColWidth > 0) {
                                    this.state.currentCol = Math.round(currentScrollLeft / this.state.dataColWidth);
                                    this.updateScrollButtons();
                                }
                            }
                        }, 10);
                    }, 300);
                }
            }
            
            // Close the delete modal
            this.hideDeleteModal();
            return;
        }

        // Handle task deletion errors
        if (!e.detail.successful &&
            e.target.id === 'delete-task-form' &&
            e.detail.requestConfig.verb === 'post') {
            
            alert('Failed to delete task. Please try again.');
            return;
        }

        // Handle task editing from edit modal
        if (e.detail.successful &&
            e.target.closest('#modal-content') &&
            e.detail.requestConfig.verb === 'post') {

            // Parse the response to get updated task data
            let updatedTaskData = null;
            try {
                updatedTaskData = JSON.parse(e.detail.xhr.response);
            } catch (e) {
                // If response isn't JSON, fall back to page reload for safety
                window.location.reload();
                return;
            }

            // Close modal with animation
            const modal = document.getElementById('modal');
            const modalContent = document.getElementById('modal-content');

            modal.classList.add('opacity-0', 'invisible');
            modalContent.classList.remove('scale-100');
            modalContent.classList.add('scale-95');

            // Update the task in place instead of reloading
            if (updatedTaskData && updatedTaskData.task_id && updatedTaskData.task_html) {
                setTimeout(() => {
                    const taskElement = document.getElementById(`task-${updatedTaskData.task_id}`);
                    
                    if (taskElement) {
                        // Store current scroll position before update
                        const gridScrollable = document.querySelector('.grid-table-scrollable');
                        const currentScrollLeft = gridScrollable ? gridScrollable.scrollLeft : 0;
                        
                        // Replace the task content with updated HTML
                        taskElement.outerHTML = updatedTaskData.task_html;
                        
                        // Re-process HTMX on the new element
                        const newTaskElement = document.getElementById(`task-${updatedTaskData.task_id}`);
                        if (newTaskElement && typeof htmx !== 'undefined') {
                            htmx.process(newTaskElement);
                        }
                        
                        // Restore scroll position immediately after update
                        if (gridScrollable && currentScrollLeft > 0) {
                            gridScrollable.scrollLeft = currentScrollLeft;
                        }
                        
                        // Sync row heights after content change, preserving scroll position
                        setTimeout(() => {
                            this.syncRowHeights();
                            // Ensure scroll position is maintained after height sync
                            if (gridScrollable && currentScrollLeft > 0) {
                                gridScrollable.scrollLeft = currentScrollLeft;
                                // Update grid manager's internal state to match
                                if (this.state.dataColWidth > 0) {
                                    this.state.currentCol = Math.round(currentScrollLeft / this.state.dataColWidth);
                                    this.updateScrollButtons();
                                }
                            }
                        }, 10);
                    } else {
                        // Task element not found, reload as fallback
                        window.location.reload();
                    }
                }, 300);
            } else {
                // No task data in response, reload as fallback
                setTimeout(() => window.location.reload(), 300);
            }
        }

        // Only save scroll position if this might cause a page reload
        const shouldReload = e.detail.requestConfig && 
            (e.detail.requestConfig.verb === 'post' && 
             e.target.closest('#modal-content')); // Only modals cause full reloads
        
        if (shouldReload && this.elements.scrollable) {
            sessionStorage.setItem('grid-scroll-position', this.elements.scrollable.scrollLeft.toString());
        }

        // Handle task completion toggle errors (revert visual changes)
        if (!e.detail.successful && e.target.closest('form[hx-post*="toggle"]')) {
            const form = e.target.closest('form');
            const checkbox = form.querySelector('input[type="checkbox"][name="completed"]');
            if (checkbox) {
                const taskId = checkbox.id.replace('checkbox-', '');
                const taskText = document.getElementById(`task-text-${taskId}`);
                
                // Revert checkbox state
                checkbox.checked = !checkbox.checked;
                
                // Revert visual changes
                if (taskText) {
                    if (checkbox.checked) {
                        checkbox.classList.add('checkbox-completed');
                        taskText.classList.add('task-completed-strikethrough');
                    } else {
                        checkbox.classList.remove('checkbox-completed');
                        taskText.classList.remove('task-completed-strikethrough');
                    }
                }
            }
        }

        // Handle task completion toggle success (ensure visual state is correct)
        if (e.detail.successful && e.target.closest('form[hx-post*="toggle"]')) {
            // Parse the response to ensure visual state matches server state
            try {
                const response = JSON.parse(e.detail.xhr.response);
                if (response.success && response.hasOwnProperty('completed')) {
                    const form = e.target.closest('form');
                    const checkbox = form.querySelector('input[type="checkbox"][name="completed"]');
                    if (checkbox) {
                        const taskId = checkbox.id.replace('checkbox-', '');
                        const taskText = document.getElementById(`task-text-${taskId}`);
                        
                        // Ensure checkbox state matches server response
                        checkbox.checked = response.completed;
                        
                        // Ensure visual state matches
                        if (taskText) {
                            if (response.completed) {
                                checkbox.classList.add('checkbox-completed');
                                taskText.classList.add('task-completed-strikethrough');
                            } else {
                                checkbox.classList.remove('checkbox-completed');
                                taskText.classList.remove('task-completed-strikethrough');
                            }
                        }
                    }
                }
            } catch (e) {
                // Response is not JSON, ignore
            }
        }

        // Handle successful form submissions
        if (e.detail.successful) {
            const form = e.target.closest('.task-form');
            if (form) {
                const input = form.querySelector('input[name="text"]');
                if (input) {
                    input.value = '';
                    if (form.classList.contains('add-task-form')) {
                        this.collapseAddTaskForm(form);
                    } else {
                        input.focus();
                    }
                }
                
                const errorDiv = form.querySelector('.error-message');
                if (errorDiv) errorDiv.innerHTML = '';
            }
        }
    }

    handleHtmxAfterSwap(e) {
        // Handle modal content updates
        if (e.detail.target.id === 'modal-content') {
            const modalContent = e.detail.target;
            
            // Modal content has loaded successfully, ensure modal is visible
            this.showModal();

            // Find the text field (input or textarea) within the newly swapped content
            const textField = modalContent.querySelector('textarea, input[name="text"]');

            if (textField) {
                // Define the keydown handler
                const handleKeyDown = (e) => {
                    if (e.key === 'Enter') {
                        // If it's a textarea and Shift is held, allow default behavior (new line)
                        if (textField.tagName.toLowerCase() === 'textarea' && e.shiftKey) {
                            return;
                        }

                        // Otherwise, prevent default and submit the form
                        e.preventDefault();
                        const form = textField.closest('form');
                        if (form) {
                            const submitButton = form.querySelector('button[type="submit"]');
                            if (submitButton) {
                                submitButton.click();
                            } else {
                                form.submit();
                            }
                        }
                    }
                };

                // Attach the event listener directly
                textField.addEventListener('keydown', handleKeyDown);

                // Focus the field and move cursor to the end
                setTimeout(() => {
                    textField.focus();
                    textField.setSelectionRange(textField.value.length, textField.value.length);
                }, 150);
            }
        }
        
        // Re-process hyperscript for new task content
        const isNewTaskContent = e.detail.target && e.detail.target.closest('[id^="tasks-"]');
        if (isNewTaskContent && typeof window._hyperscript !== 'undefined') {
            window._hyperscript.processNode(e.detail.target);
        }
        
        // Only reinitialize if this is a significant change (modal content or full grid updates)
        const isModalUpdate = e.detail.target && e.detail.target.id === 'modal-content';
        const isGridUpdate = e.detail.target && e.detail.target.closest('#grid-content');
        const isTaskUpdate = e.detail.target && e.detail.target.closest('[id^="task-"]');
        
        if (isModalUpdate) {
            // Ensure HTMX processes any new elements in the modal
            if (typeof htmx !== 'undefined') {
                htmx.process(e.detail.target);
            }
            // Modal updates need reinitialization
            this.reinitializeComponents();
        } else if (isGridUpdate && !isTaskUpdate) {
            // Grid updates just need height sync, not full reinit
            // But skip if it's a task update (handled separately)
            setTimeout(() => this.syncRowHeights(), 10);
        }
        // Task additions/updates and individual task edits don't need any reinitialization
    }

    handleHtmxAfterSettle(e) {
        // Only sync heights for grid changes, and do it faster
        const isGridRelated = e.detail.target && 
            (e.detail.target.closest('#grid-content') || e.detail.target.closest('.task-form'));
        const isTaskUpdate = e.detail.target && e.detail.target.closest('[id^="task-"]');
        
        if (isGridRelated && !isTaskUpdate) {
            // Use shorter timeout and preserve scroll position
            // But skip if it's a task update (handled separately in modal success handler)
            const currentScrollLeft = this.elements.scrollable ? this.elements.scrollable.scrollLeft : 0;
            setTimeout(() => {
                this.syncRowHeights();
                // Restore exact scroll position if it changed
                if (this.elements.scrollable && this.elements.scrollable.scrollLeft !== currentScrollLeft) {
                    this.elements.scrollable.scrollLeft = currentScrollLeft;
                }
            }, 10);
        }
    }

    handleHtmxError(e) {
        // Handle HTMX errors when loading modal content
        if (e.detail.target && e.detail.target.id === 'modal-content') {
            this.elements.modalContent.innerHTML = `
                <div class="flex items-center justify-center p-8">
                    <div class="flex flex-col items-center space-y-3 text-center">
                        <div class="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                            <i class="fas fa-exclamation-triangle text-red-500 text-xl"></i>
                        </div>
                        <div>
                            <h3 class="text-lg font-medium text-[var(--text-primary)]">Error Loading Content</h3>
                            <p class="text-sm text-[var(--text-secondary)] mt-1">Unable to load the requested content. Please try again.</p>
                        </div>
                        <button type="button" 
                                class="close-modal mt-4 px-4 py-2 bg-[var(--primary-action-bg)] hover:bg-[var(--primary-action-hover-bg)] text-white rounded-lg transition-colors">
                            Close
                        </button>
                    </div>
                </div>
            `;
        }
    }

    reinitializeComponents() {
        // Store current scroll position before reinitializing
        const currentScrollLeft = this.elements.scrollable ? this.elements.scrollable.scrollLeft : 0;
        
        this.cacheElements();
        // Skip restore during reinit to avoid double scroll position changes
        this.setupGridScrolling(true);
        
        // Reinitialize inline editing for headers
        this.addHeaderInlineEditingListeners();
        
        // Reinitialize inline editing for grid name
        this.addGridNameInlineEditingListeners();
        
        // Restore scroll position immediately, no timeout
        if (this.elements.scrollable && currentScrollLeft > 0) {
            this.elements.scrollable.scrollLeft = currentScrollLeft;
            // Update current column state to match scroll position
            this.state.currentCol = this.state.dataColWidth > 0 
                ? Math.round(currentScrollLeft / this.state.dataColWidth) 
                : 0;
            this.updateScrollButtons();
        }
    }

    // Cleanup method
    cleanup() {
        // Clear resize timeout
        if (this.resizeTimeout) {
            clearTimeout(this.resizeTimeout);
        }
        
        // Remove event listeners
        this.eventListeners.forEach((listeners, element) => {
            listeners.forEach(({ event, handler }) => {
                element.removeEventListener(event, handler);
            });
        });
        this.eventListeners.clear();

        // Disconnect observers
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();
        
        // Remove inline editing listeners
        this.removeInlineEditingListeners();
    }

    // Remove inline editing event listeners
    removeInlineEditingListeners() {
        const taskTextElements = document.querySelectorAll('.task-text-editable');
        const rowHeaders = document.querySelectorAll('.row-header-editable');
        const columnHeaders = document.querySelectorAll('.column-header-editable');
        const gridNameElement = document.querySelector('.grid-name-editable');
        
        taskTextElements.forEach(element => {
            element.removeEventListener('click', this.boundTaskTextClick);
            element.removeEventListener('blur', this.boundTaskTextBlur);
            element.removeEventListener('keydown', this.boundTaskTextKeydown);
        });
        
        rowHeaders.forEach(element => {
            element.removeEventListener('click', this.boundRowHeaderClick);
            element.removeEventListener('blur', this.boundRowHeaderBlur);
            element.removeEventListener('keydown', this.boundRowHeaderKeydown);
        });
        
        columnHeaders.forEach(element => {
            element.removeEventListener('click', this.boundColumnHeaderClick);
            element.removeEventListener('blur', this.boundColumnHeaderBlur);
            element.removeEventListener('keydown', this.boundColumnHeaderKeydown);
        });
        
        if (gridNameElement) {
            gridNameElement.removeEventListener('click', this.boundGridNameClick);
            gridNameElement.removeEventListener('blur', this.boundGridNameBlur);
            gridNameElement.removeEventListener('keydown', this.boundGridNameKeydown);
        }
    }

    // Initialize everything
    init() {
        this.cacheElements();
        
        // Set initial column visibility immediately to prevent flash
        this.setInitialColumnVisibility();
        
        // Ensure proper initialization - don't hide the table initially
        if (this.elements.gridTable) {
            this.elements.gridTable.classList.add('initialized');
        }
        this.addEventListeners();
        this.setupGridScrolling();
        this.setupInlineEditing();
        
        // Configure HTMX to not cache modal content
        if (typeof htmx !== 'undefined') {
            htmx.config.disableSelector = '[hx-disable]';
            htmx.config.useTemplateFragments = false;
        }
        
        // Force width calculation immediately and after a short delay to ensure proper sizing
        this.calculateAndApplyWidths();
        setTimeout(() => {
            this.calculateAndApplyWidths();
        }, 100);
        
        // Additional safety check for production environments
        setTimeout(() => {
            this.calculateAndApplyWidths();
            this.syncRowHeights();
            
            // Add grid-ready class to fade in the grid content
            if (this.elements.gridContent) {
                this.elements.gridContent.classList.add('grid-ready');
            }
        }, 500);
    }

    // Setup inline editing functionality
    setupInlineEditing() {
        // Only enable inline editing on desktop
        if (window.innerWidth < 769) {
            return;
        }
        
        // Store bound function references to avoid binding issues
        this.boundTaskTextClick = this.handleTaskTextClick.bind(this);
        this.boundTaskTextBlur = this.handleTaskTextBlur.bind(this);
        this.boundTaskTextKeydown = this.handleTaskTextKeydown.bind(this);
        
        // Row and column header inline editing
        this.boundRowHeaderClick = this.handleRowHeaderClick.bind(this);
        this.boundRowHeaderBlur = this.handleRowHeaderBlur.bind(this);
        this.boundRowHeaderKeydown = this.handleRowHeaderKeydown.bind(this);
        this.boundColumnHeaderClick = this.handleColumnHeaderClick.bind(this);
        this.boundColumnHeaderBlur = this.handleColumnHeaderBlur.bind(this);
        this.boundColumnHeaderKeydown = this.handleColumnHeaderKeydown.bind(this);
        
        // Grid name inline editing
        this.boundGridNameClick = this.handleGridNameClick.bind(this);
        this.boundGridNameBlur = this.handleGridNameBlur.bind(this);
        this.boundGridNameKeydown = this.handleGridNameKeydown.bind(this);
        
        // Add event listeners to all task text elements
        this.addInlineEditingListeners();
        
        // Add event listeners to row and column headers
        this.addHeaderInlineEditingListeners();
        
        // Add event listeners to grid name
        this.addGridNameInlineEditingListeners();
        
        // Listen for new tasks being added (HTMX updates)
        document.addEventListener('htmx:afterSwap', (e) => {
            if (e.detail.target && e.detail.target.closest('[id^="tasks-"]')) {
                this.addInlineEditingListeners();
            }
        });
        
        // Listen for grid structure updates (new rows/columns)
        document.addEventListener('htmx:afterSwap', (e) => {
            if (e.detail.target && e.detail.target.closest('#grid-content')) {
                this.addHeaderInlineEditingListeners();
            }
        });
    }

    // Add inline editing event listeners to task text elements
    addInlineEditingListeners() {
        const taskTextElements = document.querySelectorAll('.task-text-editable');
        
        taskTextElements.forEach(element => {
            // Remove existing listeners to prevent duplicates
            element.removeEventListener('click', this.boundTaskTextClick);
            element.removeEventListener('blur', this.boundTaskTextBlur);
            element.removeEventListener('keydown', this.boundTaskTextKeydown);
            
            // Add new listeners
            element.addEventListener('click', this.boundTaskTextClick);
            element.addEventListener('blur', this.boundTaskTextBlur);
            element.addEventListener('keydown', this.boundTaskTextKeydown);
        });
    }

    // Add inline editing event listeners to row and column headers
    addHeaderInlineEditingListeners() {
        const rowHeaders = document.querySelectorAll('.row-header-editable');
        const columnHeaders = document.querySelectorAll('.column-header-editable');
        
        rowHeaders.forEach(element => {
            // Remove existing listeners to prevent duplicates
            element.removeEventListener('click', this.boundRowHeaderClick);
            element.removeEventListener('blur', this.boundRowHeaderBlur);
            element.removeEventListener('keydown', this.boundRowHeaderKeydown);
            
            // Add new listeners
            element.addEventListener('click', this.boundRowHeaderClick);
            element.addEventListener('blur', this.boundRowHeaderBlur);
            element.addEventListener('keydown', this.boundRowHeaderKeydown);
        });
        
        columnHeaders.forEach(element => {
            // Remove existing listeners to prevent duplicates
            element.removeEventListener('click', this.boundColumnHeaderClick);
            element.removeEventListener('blur', this.boundColumnHeaderBlur);
            element.removeEventListener('keydown', this.boundColumnHeaderKeydown);
            
            // Add new listeners
            element.addEventListener('click', this.boundColumnHeaderClick);
            element.addEventListener('blur', this.boundColumnHeaderBlur);
            element.addEventListener('keydown', this.boundColumnHeaderKeydown);
        });
    }

    // Add inline editing event listeners to grid name
    addGridNameInlineEditingListeners() {
        const gridNameElement = document.querySelector('.grid-name-editable');
        
        if (gridNameElement) {
            // Remove existing listeners to prevent duplicates
            gridNameElement.removeEventListener('click', this.boundGridNameClick);
            gridNameElement.removeEventListener('blur', this.boundGridNameBlur);
            gridNameElement.removeEventListener('keydown', this.boundGridNameKeydown);
            
            // Add new listeners
            gridNameElement.addEventListener('click', this.boundGridNameClick);
            gridNameElement.addEventListener('blur', this.boundGridNameBlur);
            gridNameElement.addEventListener('keydown', this.boundGridNameKeydown);
        }
    }

    // Handle task text click for inline editing
    handleTaskTextClick(e) {
        if (window.innerWidth < 769) return; // Only on desktop
        
        const element = e.target;
        
        // If this element is already being edited, don't do anything
        if (element.classList.contains('editing')) {
            return;
        }
        
        // Close any other currently editing task first
        this.closeAllEditingTasks();
        
        // Now open this task for editing
        element.contentEditable = true;
        element.focus();
        element.classList.add('editing');
        
        // Store original text if not already stored
        if (!element.getAttribute('data-original-text')) {
            element.setAttribute('data-original-text', element.textContent);
        }
        
        // Add a one-time click handler to close this task when clicking elsewhere
        setTimeout(() => {
            document.addEventListener('click', this.handleOutsideClick.bind(this, element), { once: true });
        }, 0);
    }

    // Handle task text blur (save on blur)
    handleTaskTextBlur(e) {
        const element = e.target;
        
        // Use a small timeout to ensure the blur event is fully processed
        setTimeout(() => {
            // Check if we're in edit mode by looking at the editing class
            if (element.classList.contains('editing') && !element.classList.contains('saving')) {
                element.classList.add('saving'); // Prevent double saves
                element.contentEditable = false;
                element.classList.remove('editing');
                this.saveTaskEdit(element);
            } else if (element.contentEditable === 'true' && !element.classList.contains('saving')) {
                // Fallback: if contentEditable is still true but editing class is missing
                element.classList.add('saving'); // Prevent double saves
                element.contentEditable = false;
                this.saveTaskEdit(element);
            } else if (element.classList.contains('editing')) {
                // Another fallback: if we have the editing class but contentEditable was changed
                element.classList.add('saving'); // Prevent double saves
                element.contentEditable = false;
                element.classList.remove('editing');
                this.saveTaskEdit(element);
            }
        }, 10); // Small timeout to ensure proper event handling
    }

    // Handle clicking outside of a specific editing task
    handleOutsideClick(editingElement, e) {
        // If the click is not on the editing element or its children, close it
        if (!editingElement.contains(e.target)) {
            this.closeEditingTask(editingElement);
        }
    }

    // Close a specific editing task
    closeEditingTask(element) {
        if (!element.classList.contains('editing')) return;
        
        // If the element has changes, save them
        if (element.contentEditable === 'true' && !element.classList.contains('saving')) {
            const originalText = element.getAttribute('data-original-text') || element.textContent;
            const currentText = element.textContent.trim();
            
            if (currentText !== originalText && currentText !== '') {
                // Save the changes
                element.classList.add('saving');
                element.contentEditable = false;
                element.classList.remove('editing');
                this.saveTaskEdit(element);
            } else {
                // No changes, just close editing
                element.contentEditable = false;
                element.classList.remove('editing');
                element.classList.remove('saving');
            }
        }
    }

    // Close all currently editing tasks
    closeAllEditingTasks() {
        const editingElements = document.querySelectorAll('.task-text-editable.editing');
        editingElements.forEach(element => {
            this.closeEditingTask(element);
        });
    }

    // Handle task text keydown (Enter to save, Escape to cancel)
    handleTaskTextKeydown(e) {
        const element = e.target;
        
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            e.stopPropagation();
            // Force save and exit edit mode
            element.contentEditable = false;
            element.classList.remove('editing');
            this.saveTaskEdit(element);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            element.contentEditable = false;
            element.classList.remove('editing');
            const originalText = element.getAttribute('data-original-text') || element.textContent;
            element.textContent = originalText;
        }
    }

    // Save task edit to server
    saveTaskEdit(element) {
        let taskId = element.dataset.taskId;
        
        // If task ID is not found on the current element, try to get it from the parent
        if (!taskId) {
            const parentTaskElement = element.closest('[data-task-id]');
            if (parentTaskElement) {
                taskId = parentTaskElement.dataset.taskId;
            }
        }
        
        // If still no task ID, try to get it from the element's ID attribute
        if (!taskId && element.id) {
            const idMatch = element.id.match(/task-text-(\d+)/);
            if (idMatch) {
                taskId = idMatch[1];
            }
        }
        
        const newText = element.textContent.trim();
        const originalText = element.getAttribute('data-original-text') || element.textContent;
        
        // Check if we have a valid task ID
        if (!taskId) {
            element.classList.remove('saving');
            return;
        }
        
        // Don't save if text hasn't changed
        if (newText === originalText) {
            element.classList.remove('saving');
            return;
        }
        
        // Don't save if text is empty
        if (!newText) {
            element.textContent = originalText;
            element.classList.remove('saving');
            return;
        }
        
        // Store original text for comparison
        element.setAttribute('data-original-text', originalText);
        
        // Send update to server - use a relative URL that works from any project grid page
        fetch(`/tasks/${taskId}/edit/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                text: newText
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update was successful
                element.setAttribute('data-original-text', newText);
            } else {
                // Revert on error
                element.textContent = originalText;
            }
            element.classList.remove('saving');
        })
        .catch(error => {
            // Revert on error
            element.textContent = originalText;
            element.classList.remove('saving');
        });
    }

    // Row header inline editing methods
    handleRowHeaderClick(e) {
        if (window.innerWidth < 769) return; // Only on desktop
        
        const element = e.target;
        
        // If this element is already being edited, don't do anything
        if (element.classList.contains('editing')) {
            return;
        }
        
        // Close any other currently editing header first
        this.closeAllEditingHeaders();
        
        // Now open this header for editing
        element.contentEditable = true;
        element.focus();
        element.classList.add('editing');
        
        // Store original text if not already stored
        if (!element.getAttribute('data-original-text')) {
            element.setAttribute('data-original-text', element.textContent);
        }
        
        // Add a one-time click handler to close this header when clicking elsewhere
        setTimeout(() => {
            document.addEventListener('click', this.handleOutsideHeaderClick.bind(this, element), { once: true });
        }, 0);
    }

    handleRowHeaderBlur(e) {
        const element = e.target;
        
        // Use a small timeout to ensure the blur event is fully processed
        setTimeout(() => {
            if (element.classList.contains('editing') && !element.classList.contains('saving')) {
                element.classList.add('saving'); // Prevent double saves
                element.contentEditable = false;
                element.classList.remove('editing');
                this.saveRowHeaderEdit(element);
            }
        }, 10);
    }

    handleRowHeaderKeydown(e) {
        const element = e.target;
        
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            e.stopPropagation();
            // Force save and exit edit mode
            element.contentEditable = false;
            element.classList.remove('editing');
            this.saveRowHeaderEdit(element);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            element.contentEditable = false;
            element.classList.remove('editing');
            const originalText = element.getAttribute('data-original-text') || element.textContent;
            element.textContent = originalText;
        }
    }

    // Column header inline editing methods
    handleColumnHeaderClick(e) {
        if (window.innerWidth < 769) return; // Only on desktop
        
        const element = e.target;
        
        // If this element is already being edited, don't do anything
        if (element.classList.contains('editing')) {
            return;
        }
        
        // Close any other currently editing header first
        this.closeAllEditingHeaders();
        
        // Now open this header for editing
        element.contentEditable = true;
        element.focus();
        element.classList.add('editing');
        
        // Store original text if not already stored
        if (!element.getAttribute('data-original-text')) {
            element.setAttribute('data-original-text', element.textContent);
        }
        
        // Add a one-time click handler to close this header when clicking elsewhere
        setTimeout(() => {
            document.addEventListener('click', this.handleOutsideHeaderClick.bind(this, element), { once: true });
        }, 0);
        
        // Prevent the click from bubbling up to avoid conflicts
        e.stopPropagation();
    }

    handleColumnHeaderBlur(e) {
        const element = e.target;
        
        // Use a small timeout to ensure the blur event is fully processed
        setTimeout(() => {
            if (element.classList.contains('editing') && !element.classList.contains('saving')) {
                element.classList.add('saving'); // Prevent double saves
                element.contentEditable = false;
                element.classList.remove('editing');
                this.saveColumnHeaderEdit(element);
            }
        }, 10);
    }

    handleColumnHeaderKeydown(e) {
        const element = e.target;
        
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            e.stopPropagation();
            // Force save and exit edit mode
            element.contentEditable = false;
            element.classList.remove('editing');
            this.saveColumnHeaderEdit(element);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            element.contentEditable = false;
            element.classList.remove('editing');
            const originalText = element.getAttribute('data-original-text') || element.textContent;
            element.textContent = originalText;
        }
    }

    // Close all editing headers
    closeAllEditingHeaders() {
        const editingHeaders = document.querySelectorAll('.row-header-editable.editing, .column-header-editable.editing');
        editingHeaders.forEach(element => {
            this.closeEditingHeader(element);
        });
    }

    // Close a single editing header
    closeEditingHeader(element) {
        if (element.classList.contains('editing')) {
            element.classList.add('saving');
            element.contentEditable = false;
            element.classList.remove('editing');
            
            // Determine if it's a row or column header and save accordingly
            if (element.classList.contains('row-header-editable')) {
                this.saveRowHeaderEdit(element);
            } else if (element.classList.contains('column-header-editable')) {
                this.saveColumnHeaderEdit(element);
            }
        }
    }

    // Handle clicks outside editing headers
    handleOutsideHeaderClick(editingElement, e) {
        // Check if the click target is outside the editing element
        if (!editingElement.contains(e.target)) {
            this.closeEditingHeader(editingElement);
        }
    }

    // Save row header edit to server
    saveRowHeaderEdit(element) {
        const rowId = element.dataset.rowId;
        const newText = element.textContent.trim();
        const originalText = element.getAttribute('data-original-text') || element.textContent;
        
        // Check if we have a valid row ID
        if (!rowId) {
            element.classList.remove('saving');
            return;
        }
        
        // Don't save if text hasn't changed
        if (newText === originalText) {
            element.classList.remove('saving');
            return;
        }
        
        // Don't save if text is empty
        if (!newText) {
            element.textContent = originalText;
            element.classList.remove('saving');
            return;
        }
        
        // Store original text for comparison
        element.setAttribute('data-original-text', originalText);
        
        // Get project ID from current page
        const projectId = this.getProjectId();
        if (!projectId) {
            console.error('No project ID found');
            element.textContent = originalText;
            element.classList.remove('saving');
            return;
        }
        
        // Send update to server using correct URL format
        fetch(`/grids/${projectId}/rows/${rowId}/edit/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                row_name: newText
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update was successful
                element.setAttribute('data-original-text', newText);
                // Update all instances of this row header in the grid
                this.updateRowHeader(rowId, newText);
            } else {
                // Revert on error
                element.textContent = originalText;
            }
            element.classList.remove('saving');
        })
        .catch(error => {
            // Revert on error
            element.textContent = originalText;
            element.classList.remove('saving');
        });
    }

    // Save column header edit to server
    saveColumnHeaderEdit(element) {
        const columnId = element.dataset.columnId;
        const newText = element.textContent.trim();
        const originalText = element.getAttribute('data-original-text') || element.textContent;
        
        // Check if we have a valid column ID
        if (!columnId) {
            element.classList.remove('saving');
            return;
        }
        
        // Don't save if text hasn't changed
        if (newText === originalText) {
            element.classList.remove('saving');
            return;
        }
        
        // Don't save if text is empty
        if (!newText) {
            element.textContent = originalText;
            element.classList.remove('saving');
            return;
        }
        
        // Store original text for comparison
        element.setAttribute('data-original-text', originalText);
        
        // Get project ID from current page
        const projectId = this.getProjectId();
        if (!projectId) {
            console.error('No project ID found');
            element.textContent = originalText;
            element.classList.remove('saving');
            return;
        }
        
        // Send update to server using correct URL format
        fetch(`/grids/${projectId}/columns/${columnId}/edit/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                col_name: newText
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update was successful
                element.setAttribute('data-original-text', newText);
                // Update all instances of this column header in the grid
                this.updateColumnHeader(columnId, newText);
            } else {
                // Revert on error
                element.textContent = originalText;
            }
            element.classList.remove('saving');
        })
        .catch(error => {
            // Revert on error
            element.textContent = originalText;
            element.classList.remove('saving');
        });
    }

    // Set initial column visibility to prevent flash
    setInitialColumnVisibility() {
        const dataCols = document.querySelectorAll('.data-column');
        if (!dataCols.length) return;

        // Calculate initial column count based on screen size
        const initialColumnCount = this.getResponsiveColumnCount();
        
        // Set equal width for all visible columns to prevent text cutoff
        dataCols.forEach((col, index) => {
            if (index < initialColumnCount) {
                // Show only the initial number of columns with equal width
                const equalWidth = '300px'; // Use consistent width for all columns
                col.style.width = equalWidth;
                col.style.minWidth = equalWidth;
                col.style.maxWidth = equalWidth;
                col.style.overflow = 'visible';
            } else {
                // Hide remaining columns
                col.style.width = '0';
                col.style.minWidth = '0';
                col.style.maxWidth = '0';
                col.style.overflow = 'hidden';
            }
        });
        
        // Force a layout recalculation to ensure proper sizing
        if (this.elements.scrollable) {
            this.elements.scrollable.offsetHeight; // Force reflow
        }
    }

    // Force scroll to end even if interrupted
    forceScrollToEnd() {
        // Clear any existing scroll-to-end attempts
        if (this.state.isScrollingToEnd) {
            this.state.isScrollingToEnd = false;
        }
        
        // Set the flag and perform scroll to end
        this.state.isScrollingToEnd = true;
        this.performScrollToEnd();
    }

    // Temporarily disable interactions during scroll to end
    disableInteractionsDuringScroll() {
        // Store original state
        const originalDragging = this.state.isDragging;
        const originalScrollingToEnd = this.state.isScrollingToEnd;
        
        // Disable dragging and set scrolling flag
        this.state.isDragging = false;
        this.state.isScrollingToEnd = true;
        
        // Re-enable after scroll completes
        setTimeout(() => {
            this.state.isDragging = originalDragging;
            this.state.isScrollingToEnd = originalScrollingToEnd;
        }, 1000); // Give enough time for scroll to complete
    }

    // Grid name inline editing methods
    handleGridNameClick(e) {
        if (window.innerWidth < 769) return; // Only on desktop
        
        const element = e.target;
        
        // If this element is already being edited, don't do anything
        if (element.classList.contains('editing')) {
            return;
        }
        
        // Close any other currently editing elements first
        this.closeAllEditingElements();
        
        // Now open this grid name for editing
        element.contentEditable = true;
        element.focus();
        element.classList.add('editing');
        
        // Store original text if not already stored
        if (!element.getAttribute('data-original-text')) {
            element.setAttribute('data-original-text', element.textContent);
        }
        
        // Add a one-time click handler to close this grid name when clicking elsewhere
        setTimeout(() => {
            document.addEventListener('click', this.handleOutsideGridNameClick.bind(this, element), { once: true });
        }, 0);
    }

    handleGridNameBlur(e) {
        const element = e.target;
        
        // Use a small timeout to ensure the blur event is fully processed
        setTimeout(() => {
            if (element.classList.contains('editing') && !element.classList.contains('saving')) {
                element.classList.add('saving'); // Prevent double saves
                element.contentEditable = false;
                element.classList.remove('editing');
                this.saveGridNameEdit(element);
            }
        }, 10);
    }

    handleGridNameKeydown(e) {
        const element = e.target;
        
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            e.stopPropagation();
            // Force save and exit edit mode
            element.contentEditable = false;
            element.classList.remove('editing');
            this.saveGridNameEdit(element);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            element.contentEditable = false;
            element.classList.remove('editing');
            const originalText = element.getAttribute('data-original-text') || element.textContent;
            element.textContent = originalText;
        }
    }

    // Handle clicks outside editing grid name
    handleOutsideGridNameClick(editingElement, e) {
        // Check if the click target is outside the editing element
        if (!editingElement.contains(e.target)) {
            this.closeEditingGridName(editingElement);
        }
    }

    // Close a single editing grid name
    closeEditingGridName(element) {
        if (element.classList.contains('editing')) {
            element.classList.add('saving');
            element.contentEditable = false;
            element.classList.remove('editing');
            this.saveGridNameEdit(element);
        }
    }

    // Close all editing elements
    closeAllEditingElements() {
        this.closeAllEditingTasks();
        this.closeAllEditingHeaders();
        
        const editingGridName = document.querySelector('.grid-name-editable.editing');
        if (editingGridName) {
            this.closeEditingGridName(editingGridName);
        }
    }

    // Save grid name edit to server
    saveGridNameEdit(element) {
        const newText = element.textContent.trim();
        const originalText = element.getAttribute('data-original-text') || element.textContent;
        
        // Don't save if text hasn't changed
        if (newText === originalText) {
            element.classList.remove('saving');
            return;
        }
        
        // Don't save if text is empty
        if (!newText) {
            element.textContent = originalText;
            element.classList.remove('saving');
            return;
        }
        
        // Store original text for comparison
        element.setAttribute('data-original-text', originalText);
        
        // Get project ID from current page
        const projectId = this.getProjectId();
        if (!projectId) {
            console.error('No project ID found');
            element.textContent = originalText;
            element.classList.remove('saving');
            return;
        }
        
        // Send update to server using correct URL format
        fetch(`/grids/${projectId}/edit/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                name: newText
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update was successful
                element.setAttribute('data-original-text', newText);
                // Update the page title if it contains the project name
                const pageTitle = document.querySelector('title');
                if (pageTitle && pageTitle.textContent.includes(originalText)) {
                    pageTitle.textContent = pageTitle.textContent.replace(originalText, newText);
                }
            } else {
                // Revert on error
                element.textContent = originalText;
            }
            element.classList.remove('saving');
        })
        .catch(error => {
            // Revert on error
            element.textContent = originalText;
            element.classList.remove('saving');
        });
    }
}

// Task form validation function (kept separate as it's used inline)
function validateTaskForm(form) {
    const textInput = form.querySelector('input[name="text"]');
    const errorDiv = form.querySelector('.error-message');
    
    if (!textInput.value.trim()) {
        errorDiv.innerHTML = 'Please enter a task description';
        textInput.classList.remove('border-[var(--inline-input-border)]');
        textInput.classList.add('border-red-500');
        textInput.focus();
        return false;
    } else {
        errorDiv.innerHTML = '';
        textInput.classList.remove('border-red-500');
        textInput.classList.add('border-[var(--inline-input-border)]');
        return true;
    }
}

// Grid loading handler
function handleGridLoading() {
    // Wait for all resources to load
    window.addEventListener('load', function() {
        // Hide loading overlay
        const loadingOverlay = document.getElementById('grid-loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.opacity = '0';
            setTimeout(() => {
                loadingOverlay.style.display = 'none';
            }, 300);
        }
        
        // Show grid content
        const gridHeader = document.getElementById('grid-header');
        const gridContent = document.getElementById('grid-content-wrapper');
        
        if (gridHeader) {
            gridHeader.classList.remove('grid-content-hidden');
            gridHeader.classList.add('grid-content-visible');
        }
        
        if (gridContent) {
            gridContent.classList.remove('grid-content-hidden');
            gridContent.classList.add('grid-content-visible');
        }
    });
    
    // Fallback: if load event doesn't fire within 3 seconds, show content anyway
    setTimeout(function() {
        const loadingOverlay = document.getElementById('grid-loading-overlay');
        const gridHeader = document.getElementById('grid-header');
        const gridContent = document.getElementById('grid-content-wrapper');
        
        if (loadingOverlay && loadingOverlay.style.display !== 'none') {
            loadingOverlay.style.opacity = '0';
            setTimeout(() => {
                loadingOverlay.style.display = 'none';
            }, 300);
        }
        
        if (gridHeader && gridHeader.classList.contains('grid-content-hidden')) {
            gridHeader.classList.remove('grid-content-hidden');
            gridHeader.classList.add('grid-content-visible');
        }
        
        if (gridContent && gridContent.classList.contains('grid-content-hidden')) {
            gridContent.classList.remove('grid-content-hidden');
            gridContent.classList.add('grid-content-visible');
        }
    }, 3000);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Handle grid loading first
    handleGridLoading();
    
    // Then initialize the grid manager
    window.gridManager = new GridManager();
});

// Global function to close all dropdowns - called from inline onclick handlers
window.closeAllDropdowns = function() {
    if (window.gridManager) {
        window.gridManager.closeAllDropdowns();
    }
};

// Global function to manually clean up duplicate tasks
window.cleanupDuplicateTasks = function() {
    if (window.gridManager) {
        window.gridManager.cleanupDuplicateTasks();
    }
};

// Global function to inspect DOM structure for duplicates
window.inspectDuplicateTasks = function() {
    if (window.gridManager) {
        window.gridManager.inspectDuplicateTasks();
    }
};

// Task Note Panel functionality
window.showTaskNotePanel = function(taskId, taskText, hasNote) {
    const panel = document.getElementById('task-note-panel');
    const overlay = document.getElementById('task-note-overlay');
    const taskTextElement = document.getElementById('note-panel-task-text');
    const form = document.getElementById('task-note-form');
    const noteTextarea = document.getElementById('note-text');
    const notesDisplay = document.getElementById('notes-display');
    const notesList = document.getElementById('notes-list');
    const noteFormLabel = document.getElementById('note-form-label');
    
    if (panel && overlay && taskTextElement && form && noteTextarea) {
        // Set task text in panel header
        taskTextElement.textContent = taskText;
        
        // Set form action URL
        form.action = `/tasks/${taskId}/note/`;
        
        // Clear form
        noteTextarea.value = '';
        
        if (hasNote) {
            // Show notes display and load existing notes
            notesDisplay.classList.remove('hidden');
            noteFormLabel.textContent = 'Add Note';
            
            // Load all notes via fetch
            fetch(`/tasks/${taskId}/notes/`)
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.notes) {
                        notesList.innerHTML = '';
                        
                        // Notes are already ordered by most recent first from the backend
                        data.notes.forEach(note => {
                            const noteDiv = document.createElement('div');
                            noteDiv.className = 'border border-gray-200 rounded-lg p-4 relative mb-2';
                            
                            const date = new Date(note.created_at);
                            const day = date.getDate();
                            const month = date.toLocaleDateString('en-GB', { month: 'short' });
                            const year = date.getFullYear().toString().slice(-2);
                            const dayWithSuffix = day + (day === 1 || day === 21 || day === 31 ? 'st' : 
                                                       day === 2 || day === 22 ? 'nd' : 
                                                       day === 3 || day === 23 ? 'rd' : 'th');
                            
                            noteDiv.innerHTML = `
                                <button type="button" 
                                        class="delete-note-btn absolute top-2 right-2 text-gray-400 hover:text-red-500 transition-colors"
                                        data-note-id="${note.id}"
                                        title="Delete note">
                                    <i class="fas fa-trash text-xs"></i>
                                </button>
                                <p class="text-sm text-gray-900 whitespace-pre-wrap pr-6">${note.note}</p>
                                <p class="text-xs text-gray-700 mt-2">${dayWithSuffix} ${month} ${year}</p>
                            `;
                            
                            notesList.appendChild(noteDiv);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error loading notes:', error);
                });
        } else {
            // Hide notes display
            notesDisplay.classList.add('hidden');
            noteFormLabel.textContent = 'Add Note';
        }
        
        // Show panel and overlay
        overlay.style.pointerEvents = 'auto';
        overlay.classList.remove('opacity-0', 'invisible');
        panel.style.transform = 'translateX(0)';
        panel.style.transition = 'transform 0.3s ease-in-out';
        
        // Focus on textarea
        setTimeout(() => {
            noteTextarea.focus();
        }, 300);
    } else {
        console.error('Required elements not found:', { panel, taskTextElement, form, noteTextarea });
    }
};

window.hideTaskNotePanel = function() {
    const panel = document.getElementById('task-note-panel');
    const overlay = document.getElementById('task-note-overlay');
    if (panel && overlay) {
        overlay.style.pointerEvents = 'none';
        overlay.classList.add('opacity-0', 'invisible');
        panel.style.transform = 'translateX(100%)';
        panel.style.transition = 'transform 0.3s ease-in-out';
    }
};

// Handle task note button clicks - moved outside DOMContentLoaded to ensure it works
document.addEventListener('click', function(e) {
    const noteBtn = e.target.closest('.task-note-btn');
    if (noteBtn) {
        e.preventDefault();
        const taskId = noteBtn.dataset.taskId;
        const taskText = noteBtn.dataset.taskText;
        const hasNote = noteBtn.dataset.hasNote === 'true';
        showTaskNotePanel(taskId, taskText, hasNote);
        return false; // Prevent further event propagation
    }
});

// Task note event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Close note panel buttons
    const closeNotePanel = document.getElementById('close-note-panel');
    const cancelNoteBtn = document.getElementById('cancel-note-btn');
    const notePanel = document.getElementById('task-note-panel');
    
    if (closeNotePanel) {
        closeNotePanel.addEventListener('click', hideTaskNotePanel);
    }
    
    // Handle delete note buttons (dynamically created)
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.delete-note-btn');
        if (deleteBtn) {
            e.preventDefault();
            const noteId = deleteBtn.dataset.noteId;
            const form = document.getElementById('task-note-form');
            const taskId = form.action.split('/tasks/')[1].split('/note/')[0];
            
            // Delete note via fetch
            fetch(`/tasks/${taskId}/note/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Note-ID': noteId
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Update the task note display
                    updateTaskNoteDisplay(taskId, data.has_notes);
                    
                    // Reload notes in panel
                    if (data.has_notes) {
                        fetch(`/tasks/${taskId}/notes/`)
                            .then(response => response.json())
                            .then(notesData => {
                                if (notesData.success && notesData.notes) {
                                    const notesList = document.getElementById('notes-list');
                                    notesList.innerHTML = '';
                                    
                                    // Notes are already ordered by most recent first from the backend
                                    notesData.notes.forEach(note => {
                                        const noteDiv = document.createElement('div');
                                        noteDiv.className = 'border border-gray-200 rounded-lg p-4 relative mb-2';
                                        
                                        const date = new Date(note.created_at);
                                        const day = date.getDate();
                                        const month = date.toLocaleDateString('en-GB', { month: 'short' });
                                        const year = date.getFullYear().toString().slice(-2);
                                        const dayWithSuffix = day + (day === 1 || day === 21 || day === 31 ? 'st' : 
                                                                   day === 2 || day === 22 ? 'nd' : 
                                                                   day === 3 || day === 23 ? 'rd' : 'th');
                                        
                                        noteDiv.innerHTML = `
                                            <button type="button" 
                                                    class="delete-note-btn absolute top-2 right-2 text-gray-400 hover:text-red-500 transition-colors"
                                                    data-note-id="${note.id}"
                                                    title="Delete note">
                                                <i class="fas fa-trash text-xs"></i>
                                            </button>
                                            <p class="text-sm text-gray-900 whitespace-pre-wrap pr-6">${note.note}</p>
                                            <p class="text-xs text-gray-700 mt-2">${dayWithSuffix} ${month} ${year}</p>
                                        `;
                                        
                                        notesList.appendChild(noteDiv);
                                    });
                                }
                            });
                    } else {
                        // Hide notes display if no notes left
                        const notesDisplay = document.getElementById('notes-display');
                        notesDisplay.classList.add('hidden');
                    }
                    
                    // Show notification if available
                    if (window.showNotification) {
                        window.showNotification('Note deleted successfully!', 'success');
                    }
                } else {
                    // Show error
                    if (window.showNotification) {
                        window.showNotification('Failed to delete note', 'error');
                    }
                }
            })
            .catch(error => {
                console.error('Error deleting note:', error);
                if (window.showNotification) {
                    window.showNotification('Failed to delete note', 'error');
                }
            });
        }
    });
    
    // Close panel when clicking outside
    if (notePanel) {
        notePanel.addEventListener('click', function(e) {
            if (e.target === notePanel) {
                hideTaskNotePanel();
            }
        });
    }
    
    // Close panel when clicking on overlay
    const noteOverlay = document.getElementById('task-note-overlay');
    if (noteOverlay) {
        noteOverlay.addEventListener('click', function(e) {
            if (e.target === noteOverlay) {
                hideTaskNotePanel();
            }
        });
    }
    
    // Handle task note form submission
    const noteForm = document.getElementById('task-note-form');
    if (noteForm) {
        noteForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(noteForm);
            const taskId = noteForm.action.split('/tasks/')[1].split('/note/')[0];
            const noteText = formData.get('note');
            
            // Show loading state
            const submitBtn = noteForm.querySelector('#save-note-btn');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            
            // Submit form via fetch
            fetch(noteForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Update the task note button icon immediately
                    updateTaskNoteDisplay(taskId, true);
                    
                    // Close panel immediately
                    hideTaskNotePanel();
                    
                    // Show notification if available
                    if (window.showNotification) {
                        window.showNotification('Note saved successfully!', 'success');
                    }
                    
                    // Re-enable button
                    submitBtn.disabled = false;
                } else {
                    // Show error
                    submitBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                    submitBtn.classList.remove('text-gray-400', 'hover:text-[var(--primary-action-bg)]');
                    submitBtn.classList.add('text-red-500');
                    
                    setTimeout(() => {
                        submitBtn.innerHTML = originalText;
                        submitBtn.disabled = false;
                        submitBtn.classList.remove('text-red-500');
                        submitBtn.classList.add('text-gray-400', 'hover:text-[var(--primary-action-bg)]');
                    }, 2000);
                }
            })
            .catch(error => {
                console.error('Error saving note:', error);
                submitBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                submitBtn.classList.remove('text-gray-400', 'hover:text-[var(--primary-action-bg)]');
                submitBtn.classList.add('text-red-500');
                
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('text-red-500');
                    submitBtn.classList.add('text-gray-400', 'hover:text-[var(--primary-action-bg)]');
                }, 2000);
            });
        });
    }
});

// Function to update task note display without page refresh
function updateTaskNoteDisplay(taskId, hasNote) {
    const taskElement = document.getElementById(`task-${taskId}`);
    if (!taskElement) return;
    
    // Update note button icons
    const noteButtons = taskElement.querySelectorAll('.task-note-btn');
    noteButtons.forEach(btn => {
        const icon = btn.querySelector('i');
        if (icon) {
            if (hasNote) {
                icon.className = 'fas fa-sticky-note text-[var(--primary-action-bg)] text-xs transition-colors';
                btn.title = 'Edit note';
                btn.setAttribute('data-has-note', 'true');
            } else {
                icon.className = 'fas fa-sticky-note text-gray-400 hover:text-[var(--primary-action-bg)] text-xs transition-colors';
                btn.title = 'Add note';
                btn.setAttribute('data-has-note', 'false');
            }
        }
    });
    
    // Update note display beneath task text
    const taskTextContainer = taskElement.querySelector('.flex-1.min-w-0');
    if (!taskTextContainer) return;
    
    let noteDisplay = taskTextContainer.querySelector('.note-display');
    
    if (hasNote) {
        // Fetch all notes for this task
        fetch(`/tasks/${taskId}/notes/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.notes && data.notes.length > 0) {
                    // Create or update note display (single note only)
                    if (!noteDisplay) {
                        noteDisplay = document.createElement('div');
                        noteDisplay.className = 'note-display flex items-center mt-1 text-xs text-[var(--text-secondary)] ml-1';
                        
                        // Insert after the task text div, before reminder if it exists
                        const taskTextDiv = taskTextContainer.querySelector('[id^="task-text-"]');
                        const reminderDisplay = taskTextContainer.querySelector('.reminder-display');
                        
                        if (reminderDisplay) {
                            taskTextContainer.insertBefore(noteDisplay, reminderDisplay);
                        } else {
                            taskTextDiv.parentNode.insertBefore(noteDisplay, taskTextDiv.nextSibling);
                        }
                    }
                    
                    // Show only the note icon (no date)
                    noteDisplay.innerHTML = `
                        <i class="fas fa-sticky-note text-[var(--primary-action-bg)]"></i>
                    `;
                }
            })
            .catch(error => {
                console.error('Error fetching notes:', error);
            });
    } else {
        // Remove note display
        if (noteDisplay) {
            noteDisplay.remove();
        }
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.gridManager) {
        window.gridManager.cleanup();
    }
}); 