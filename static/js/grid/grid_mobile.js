// Grid JavaScript - Mobile Version
class MobileGridManager {
    constructor() {
        console.log('MobileGridManager: Constructor called, window width:', window.innerWidth);
        
        // Only initialize on mobile - don't interfere with desktop
        if (window.innerWidth >= 769) {
            console.log('MobileGridManager: Skipping initialization on desktop device');
            return;
        }
        
        console.log('MobileGridManager: Initializing on mobile device');
        
        this.state = {
            currentCol: 0,
            totalColumns: 0,
            projectSwitcherOpen: false,
            actionsMenuOpen: false,
            currentTaskId: null,
            currentDeleteUrl: null,
            currentRowId: null,
            currentRowDeleteUrl: null,
            touchStartX: 0,
            touchEndX: 0,
            isSwiping: false,
        };
        
        this.elements = {};
        this.eventListeners = new Map();

        this.init();
    }

    // Cache DOM elements to avoid repeated queries
    cacheElements() {
        const selectors = {
            // Project switcher
            switcherBtn: '#project-switcher-btn',
            projectSwitcherDropdown: '#project-switcher-dropdown',
            projectSwitcherChevron: '#switcher-chevron',
            switcherContainer: '#project-switcher-container',

            // Actions menu
            actionsMenuBtn: '#actions-menu-btn',
            actionsMenuDropdown: '#actions-menu-dropdown',
            actionsMenuChevron: '#actions-chevron',
            actionsMenuContainer: '#actions-menu-container',
            
            // Mobile Grid
            gridContainer: '#mobile-grid-container',
            gridSlider: '#mobile-grid-slider',
            columns: '.mobile-column',
            leftBtn: '#mobile-scroll-left',
            rightBtn: '#mobile-scroll-right',
            columnHeader: '#mobile-column-header h2',
            columnIndicator: '#column-indicator',

            // Modals
            deleteModal: '#delete-task-modal',
            deleteModalContent: '#delete-modal-content',
            taskToDelete: '#task-to-delete',
            deleteTaskForm: '#delete-task-form',
            closeDeleteModal: '#close-delete-modal',
            cancelDeleteTask: '#cancel-delete-task',
            deleteRowModal: '#delete-row-modal',
            deleteRowModalContent: '#delete-row-modal-content',
            rowToDelete: '#row-to-delete',
            deleteRowForm: '#delete-row-form',
            closeDeleteRowModal: '#close-delete-row-modal',
            cancelDeleteRow: '#cancel-delete-row',
            modal: '#modal',
            modalContent: '#modal-content',
        };

        Object.keys(selectors).forEach(key => {
            const selector = selectors[key];
            if (key === 'columns') {
                this.elements[key] = document.querySelectorAll(selector);
            } else {
                this.elements[key] = document.querySelector(selector);
            }
        });
    }

    // Unified event listener management
    addEventListeners() {
        const listeners = [
            ['document', 'click', this.handleDocumentClick.bind(this)],
            ['document', 'keydown', this.handleKeydown.bind(this)],
            ['document', 'htmx:beforeRequest', this.handleHtmxBeforeRequest.bind(this)],
            ['document', 'htmx:afterRequest', this.handleHtmxAfterRequest.bind(this)],
            ['document', 'htmx:afterSwap', this.handleHtmxAfterSwap.bind(this)],
            ['document', 'htmx:responseError', this.handleHtmxError.bind(this)],
            ['document', 'htmx:sendError', this.handleHtmxError.bind(this)],
            ['window', 'resize', this.handleWindowResize.bind(this)],
            ['body', 'openModal', this.showModal.bind(this)],
            ['body', 'closeModal', this.hideModal.bind(this)],
            ['body', 'refreshGrid', this.handleRefreshGrid.bind(this)],
            ['body', 'scrollToEnd', this.handleScrollToEnd.bind(this)],
            ['body', 'resetGridToInitial', this.handleResetGridToInitial.bind(this)],
        ];

        listeners.forEach(([target, event, handler]) => {
            const element = target === 'document' ? document : 
                           target === 'window' ? window : document.body;
            element.addEventListener(event, handler);
            this.getEventListenersFor(element).push({ event, handler });
        });

        // Touch events for swiping
        if (this.elements.gridSlider) {
            this.elements.gridSlider.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
            this.elements.gridSlider.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: true });
            this.elements.gridSlider.addEventListener('touchend', this.handleTouchEnd.bind(this));
        }
    }
    
    getEventListenersFor(element) {
        if (!this.eventListeners.has(element)) {
            this.eventListeners.set(element, []);
        }
        return this.eventListeners.get(element);
    }

    // Unified click handler
    handleDocumentClick(e) {
        // Modal triggers - clear content immediately before HTMX loads new content
        const modalTrigger = e.target.closest('[hx-target="#modal-content"]');
        if (modalTrigger) {
            console.log('Modal trigger detected:', modalTrigger);
            this.clearModalContent(); // Always show loading spinner
            this.showModal();
            return;
        }

        if (e.target.closest('#project-switcher-btn')) {
            e.stopPropagation(); this.toggleDropdown('projectSwitcher'); return;
        }
        if (!e.target.closest('#project-switcher-container')) this.closeDropdown('projectSwitcher');

        if (e.target.closest('#actions-menu-btn')) {
            e.stopPropagation(); this.toggleDropdown('actionsMenu'); return;
        }
        if (!e.target.closest('#actions-menu-container')) this.closeDropdown('actionsMenu');

        const actionBtn = e.target.closest('.column-actions-btn, .row-actions-btn');
        if (actionBtn) {
            e.stopPropagation(); this.toggleActionDropdown(actionBtn); return;
        }
        if (!e.target.closest('.column-actions-dropdown, .row-actions-dropdown')) this.closeAllActionDropdowns();

        const deleteTaskBtn = e.target.closest('.delete-task-btn');
        if (deleteTaskBtn) {
            console.log('Delete task button clicked:', deleteTaskBtn.dataset);
            console.log('Mobile Grid: Task ID from dataset:', deleteTaskBtn.dataset.taskId);
            e.preventDefault();
            this.showDeleteModal(deleteTaskBtn.dataset.taskId, deleteTaskBtn.dataset.taskText, deleteTaskBtn.dataset.deleteUrl);
            return;
        }

        const deleteRowBtn = e.target.closest('.delete-row-btn');
        if (deleteRowBtn) {
            console.log('Delete row button clicked:', deleteRowBtn.dataset);
            console.log('Mobile Grid: Row ID from dataset:', deleteRowBtn.dataset.rowId);
            e.preventDefault();
            this.showDeleteRowModal(deleteRowBtn.dataset.rowId, deleteRowBtn.dataset.rowName, deleteRowBtn.dataset.deleteUrl);
            return;
        }

        const closeModalBtn = e.target.closest('.close-modal, #close-delete-modal, #cancel-delete-task, #close-delete-row-modal, #cancel-delete-row');
        if (closeModalBtn) {
            console.log('Close modal button clicked:', closeModalBtn.id);
            if (closeModalBtn.id === 'close-delete-modal' || closeModalBtn.id === 'cancel-delete-task') this.hideDeleteModal();
            else if (closeModalBtn.id === 'close-delete-row-modal' || closeModalBtn.id === 'cancel-delete-row') this.hideDeleteRowModal();
            else if (closeModalBtn.classList.contains('close-modal')) this.hideModal();
            return;
        }

        if (e.target === this.elements.deleteModal) this.hideDeleteModal();
        if (e.target === this.elements.deleteRowModal) this.hideDeleteRowModal();
        if (e.target === this.elements.modal) this.hideModal();

        const addTaskTrigger = e.target.closest('.add-task-trigger');
        if (addTaskTrigger) { e.preventDefault(); this.expandAddTaskForm(addTaskTrigger.closest('.add-task-form')); return; }
        const addTaskCancel = e.target.closest('.add-task-cancel');
        if (addTaskCancel) { e.preventDefault(); this.collapseAddTaskForm(addTaskCancel.closest('.add-task-form')); return; }
        if (!e.target.closest('.add-task-form')) this.collapseAllAddTaskForms();
    }

    // Function to close all dropdowns - called from inline onclick handlers
    closeAllDropdowns() {
        this.closeDropdown('projectSwitcher');
        this.closeDropdown('actionsMenu');
        this.closeAllActionDropdowns();
    }
    
    // Mobile Grid setup
    setupMobileGrid() {
        if (!this.elements.gridSlider || !this.elements.columns.length) return;

        this.state.totalColumns = this.elements.columns.length;

        if (this.elements.leftBtn) this.elements.leftBtn.onclick = () => this.scrollToCol(this.state.currentCol - 1);
        if (this.elements.rightBtn) this.elements.rightBtn.onclick = () => this.scrollToCol(this.state.currentCol + 1);

        // Initialize the first column as active
        this.elements.columns.forEach((col, index) => {
            if (index === 0) {
                col.classList.add('active');
                col.style.transform = 'translateX(0)';
                col.style.zIndex = '10';
            } else {
                col.classList.remove('active');
                col.style.transform = 'translateX(100%)';
                col.style.zIndex = '1';
            }
        });

        this.scrollToCol(this.state.currentCol, 'auto');
    }

    scrollToCol(colIdx, behavior = 'smooth') {
        this.state.currentCol = Math.max(0, Math.min(colIdx, this.state.totalColumns - 1));
        
        // Update column visibility and active states
        this.elements.columns.forEach((col, index) => {
            if (index === this.state.currentCol) {
                col.style.transform = 'translateX(0)';
                col.style.zIndex = '10';
                col.classList.add('active');
                col.classList.add('relative');
                col.classList.remove('absolute');
                // Make active column relative and auto height
                col.style.position = 'relative';
                col.style.height = 'auto';
            } else {
                col.style.transform = 'translateX(100%)';
                col.style.zIndex = '1';
                col.classList.remove('active');
                col.classList.remove('relative');
                col.classList.add('absolute');
                // Make inactive columns absolute and 100% height
                col.style.position = 'absolute';
                col.style.height = '100%';
            }
        });
        
        this.updateUI();
        this.setContainerHeightToActiveColumn();
    }

    updateUI() {
        if (this.elements.leftBtn) this.elements.leftBtn.disabled = this.state.currentCol === 0;
        if (this.elements.rightBtn) this.elements.rightBtn.disabled = this.state.currentCol === this.state.totalColumns - 1;

        const currentColumnEl = this.elements.columns[this.state.currentCol];
        if (currentColumnEl && this.elements.columnHeader) {
            this.elements.columnHeader.textContent = currentColumnEl.dataset.columnName;
            this.elements.columnHeader.dataset.columnName = currentColumnEl.dataset.columnName;
        }
        
        if (this.elements.columnIndicator) {
            this.elements.columnIndicator.textContent = `${this.state.currentCol + 1} / ${this.state.totalColumns}`;
        }
    }

    // Touch handlers
    handleTouchStart(e) {
        this.state.touchStartX = e.touches[0].clientX;
        this.state.isSwiping = false;
    }

    handleTouchMove(e) {
        if (!this.state.touchStartX) return;
        this.state.touchEndX = e.touches[0].clientX;
        if (Math.abs(this.state.touchStartX - this.state.touchEndX) > 10) { // Threshold to start swipe
            this.state.isSwiping = true;
        }
    }

    handleTouchEnd() {
        if (!this.state.isSwiping) return;

        const deltaX = this.state.touchEndX - this.state.touchStartX;
        const swipeThreshold = 50; // Min distance for a swipe

        if (deltaX > swipeThreshold) {
            this.scrollToCol(this.state.currentCol - 1); // Swipe right
        } else if (deltaX < -swipeThreshold) {
            this.scrollToCol(this.state.currentCol + 1); // Swipe left
        }

        // Reset touch state
        this.state.touchStartX = 0;
        this.state.touchEndX = 0;
        this.state.isSwiping = false;
    }


    // Keyboard handler
    handleKeydown(e) {
        if (e.key === 'Escape') {
            this.closeDropdown('projectSwitcher');
            this.closeDropdown('actionsMenu');
            this.closeAllActionDropdowns();
            this.hideDeleteModal();
            this.hideDeleteRowModal();
            this.hideModal();
            this.collapseAllAddTaskForms();
        } else if (e.key === 'ArrowLeft') {
            this.scrollToCol(this.state.currentCol - 1);
        } else if (e.key === 'ArrowRight') {
            this.scrollToCol(this.state.currentCol + 1);
        }
    }
    
    // Generic dropdown methods
    toggleDropdown(type) {
        const otherType = type === 'projectSwitcher' ? 'actionsMenu' : 'projectSwitcher';
        this.closeDropdown(otherType); // Close other dropdown first

        const stateKey = `${type}Open`;
        this.state[stateKey] = !this.state[stateKey];
        this.updateDropdownUI(type);
    }

    closeDropdown(type) {
        const stateKey = `${type}Open`;
        if (this.state[stateKey]) {
            this.state[stateKey] = false;
            this.updateDropdownUI(type);
        }
    }

    updateDropdownUI(type) {
        const dropdown = this.elements[`${type}Dropdown`];
        const chevron = this.elements[`${type}Chevron`];
        if (!dropdown) return;

        const isOpen = this.state[`${type}Open`];
        const classes = isOpen 
            ? { remove: ['opacity-0', 'invisible', 'scale-95'], add: ['opacity-100', 'visible', 'scale-100'] }
            : { remove: ['opacity-100', 'visible', 'scale-100'], add: ['opacity-0', 'invisible', 'scale-95'] };
        
        dropdown.classList.remove(...classes.remove);
        dropdown.classList.add(...classes.add);
        if (chevron) chevron.style.transform = isOpen ? 'rotate(180deg)' : 'rotate(0deg)';
    }

    // Action dropdowns for rows/columns
    toggleActionDropdown(btn) {
        const dropdown = btn.nextElementSibling;
        if (!dropdown) return;
        this.closeAllActionDropdowns(dropdown);
        const isOpen = !dropdown.classList.contains('opacity-0');
        this.setDropdownState(dropdown, !isOpen);
    }

    closeAllActionDropdowns(except = null) {
        document.querySelectorAll('.column-actions-dropdown, .row-actions-dropdown').forEach(dropdown => {
            if (dropdown !== except) this.setDropdownState(dropdown, false);
        });
    }

    setDropdownState(dropdown, isOpen) {
        const classes = isOpen 
            ? { remove: ['opacity-0', 'invisible', 'scale-95'], add: ['opacity-100', 'visible', 'scale-100'] }
            : { remove: ['opacity-100', 'visible', 'scale-100'], add: ['opacity-0', 'invisible', 'scale-95'] };
        dropdown.classList.remove(...classes.remove);
        dropdown.classList.add(...classes.add);
    }

    // Modal methods
    showDeleteModal(taskId, taskText, deleteUrl) {
        console.log('Showing delete modal:', { taskId, taskText, deleteUrl });
        console.log('Mobile Grid: Storing task ID in state:', taskId);
        this.state.currentTaskId = taskId;
        this.state.currentDeleteUrl = deleteUrl;
        if (this.elements.taskToDelete) this.elements.taskToDelete.textContent = taskText;
        if (this.elements.deleteTaskForm) {
            this.elements.deleteTaskForm.action = deleteUrl;
            this.elements.deleteTaskForm.setAttribute('hx-post', deleteUrl);
            this.elements.deleteTaskForm.setAttribute('hx-swap', 'none');
            this.elements.deleteTaskForm.setAttribute('hx-trigger', 'submit');
            this.elements.deleteTaskForm.setAttribute('hx-disabled-elt', 'this');
            if (typeof htmx !== 'undefined') htmx.process(this.elements.deleteTaskForm);
        }
        this.setModalState(this.elements.deleteModal, this.elements.deleteModalContent, true);
        setTimeout(() => this.elements.cancelDeleteTask?.focus(), 100);
    }

    hideDeleteModal() {
        console.log('Hiding delete modal');
        this.setModalState(this.elements.deleteModal, this.elements.deleteModalContent, false);
        this.state.currentTaskId = null;
        this.state.currentDeleteUrl = null;
    }

    showDeleteRowModal(rowId, rowName, deleteUrl) {
        console.log('Showing delete row modal:', { rowId, rowName, deleteUrl });
        console.log('Mobile Grid: Storing row ID in state:', rowId);
        this.state.currentRowId = rowId;
        this.state.currentRowDeleteUrl = deleteUrl;
        if (this.elements.rowToDelete) this.elements.rowToDelete.textContent = rowName;
        if (this.elements.deleteRowForm) {
            this.elements.deleteRowForm.action = deleteUrl;
            this.elements.deleteRowForm.setAttribute('hx-post', deleteUrl);
            this.elements.deleteRowForm.setAttribute('hx-swap', 'none');
            this.elements.deleteRowForm.setAttribute('hx-trigger', 'submit');
            this.elements.deleteRowForm.setAttribute('hx-disabled-elt', 'this');
            if (typeof htmx !== 'undefined') htmx.process(this.elements.deleteRowForm);
        }
        this.setModalState(this.elements.deleteRowModal, this.elements.deleteRowModalContent, true);
        setTimeout(() => this.elements.cancelDeleteRow?.focus(), 100);
    }

    hideDeleteRowModal() {
        console.log('Hiding delete row modal');
        this.setModalState(this.elements.deleteRowModal, this.elements.deleteRowModalContent, false);
        this.state.currentRowId = null;
        this.state.currentRowDeleteUrl = null;
    }

    showModal() { 
        console.log('Showing modal');
        this.setModalState(this.elements.modal, this.elements.modalContent, true); 
    }
    hideModal() { 
        console.log('Hiding modal');
        this.setModalState(this.elements.modal, this.elements.modalContent, false); 
    }
    
    clearModalContent() {
        if (this.elements.modalContent) {
            // Show loading indicator
            this.elements.modalContent.innerHTML = `
                <div class="htmx-indicator flex items-center justify-center p-8">
                    <div class="flex items-center space-x-3">
                        <div class="animate-spin w-6 h-6 border-2 border-[var(--primary-action-bg)] border-t-transparent rounded-full"></div>
                        <span class="text-[var(--text-secondary)]">Loading...</span>
                    </div>
                </div>
            `;
        }
    }

    setModalState(modal, content, isOpen) {
        if (!modal || !content) {
            console.warn('Modal or content element not found:', { modal, content });
            return;
        }
        
        if (isOpen) {
            modal.classList.remove('opacity-0', 'invisible');
            modal.classList.add('opacity-100', 'visible');
            content.classList.remove('scale-95');
            content.classList.add('scale-100');
            
            // Prevent body scroll
            document.body.style.overflow = 'hidden';
        } else {
            modal.classList.add('opacity-0', 'invisible');
            modal.classList.remove('opacity-100', 'visible');
            content.classList.remove('scale-100');
            content.classList.add('scale-95');
            
            // Restore body scroll
            document.body.style.overflow = '';
        }
    }

    // Add task form methods
    expandAddTaskForm(form) {
        if (!form) return;
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
            if (errorDiv) errorDiv.innerHTML = '';
        }
    }

    collapseAllAddTaskForms() {
        document.querySelectorAll('.add-task-form').forEach(form => this.collapseAddTaskForm(form));
    }

    // HTMX handlers...
    handleHtmxBeforeRequest(e) {
        // Show loading indicator for task forms
        if (e.target.classList.contains('task-form')) {
            const submitBtn = e.target.querySelector('button[type="submit"]');
            if (submitBtn) {
                const spinner = submitBtn.querySelector('.htmx-indicator-spinner');
                if (spinner) {
                    spinner.style.opacity = '1';
                }
            }
        }
    }

    handleHtmxAfterRequest(e) {
        console.log('Mobile Grid: HTMX afterRequest event:', e.detail);
        
        // Hide loading indicator when request completes
        if (e.target.id === 'modal-content') {
            const loadingIndicator = e.target.querySelector('.htmx-indicator');
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
        }
        
        // Handle task form submission
        if (e.target.classList.contains('task-form')) {
            console.log('Mobile Grid: Task form submission detected');
            const submitBtn = e.target.querySelector('button[type="submit"]');
            if (submitBtn) {
                const spinner = submitBtn.querySelector('.htmx-indicator-spinner');
                if (spinner) {
                    spinner.style.opacity = '0';
                }
            }
            
            // If successful, clear the form and collapse it
            if (e.detail.successful) {
                const input = e.target.querySelector('input[name="text"]');
                if (input) {
                    input.value = '';
                }
                this.collapseAddTaskForm(e.target);
            } else {
                // Show error message if there was an error
                const errorDiv = e.target.querySelector('.error-message');
                if (errorDiv) {
                    if (e.detail.xhr && e.detail.xhr.status === 0) {
                        // Connection refused or network error
                        errorDiv.innerHTML = 'Network error: Unable to connect to server. Please check your connection and try again.';
                    } else if (e.detail.xhr && e.detail.xhr.responseText) {
                        try {
                            const response = JSON.parse(e.detail.xhr.responseText);
                            if (response.errors && response.errors.text) {
                                errorDiv.innerHTML = response.errors.text.join(', ');
                            } else {
                                errorDiv.innerHTML = 'An error occurred. Please try again.';
                            }
                        } catch (e) {
                            errorDiv.innerHTML = 'An error occurred. Please try again.';
                        }
                    } else {
                        errorDiv.innerHTML = 'An error occurred. Please try again.';
                    }
                    errorDiv.style.display = 'block';
                }
            }
        }
        
        // Handle task toggle completion
        if (e.target.matches('input[type="checkbox"]') && e.target.closest('form')) {
            console.log('Mobile Grid: Task toggle completion detected');
            if (e.detail.successful && e.detail.xhr && e.detail.xhr.responseText) {
                try {
                    const response = JSON.parse(e.detail.xhr.responseText);
                    if (response.success !== undefined) {
                        // The visual changes are already applied by the hyperscript in the template
                        // This just ensures the server response is handled properly
                        console.log('Mobile Grid: Task toggle response:', response);
                    }
                } catch (e) {
                    // Not a JSON response, continue with normal handling
                }
            }
        }
        
        // Handle delete task form submission
        if (e.target.id === 'delete-task-form') {
            console.log('Mobile Grid: Delete task form submitted:', e.detail);
            if (e.detail.successful) {
                console.log('Mobile Grid: Delete task successful, hiding modal and removing task');
                
                // Store the task ID before hiding the modal (which clears it)
                const taskId = this.state.currentTaskId;
                console.log('Mobile Grid: Stored task ID before hiding modal:', taskId);
                
                // Hide the delete modal
                this.hideDeleteModal();
                
                // Remove the task from the DOM
                console.log('Mobile Grid: Attempting to remove task with ID:', taskId);
                if (taskId) {
                    // Try multiple selectors to find the task element
                    let taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
                    if (!taskElement) {
                        taskElement = document.getElementById(`task-${taskId}`);
                    }
                    if (!taskElement) {
                        // Try finding by task ID in any attribute
                        taskElement = document.querySelector(`[data-task-id*="${taskId}"], [id*="${taskId}"]`);
                    }
                    
                    if (taskElement) {
                        console.log('Mobile Grid: Found task element:', taskElement);
                        taskElement.remove();
                        console.log('Mobile Grid: Task element removed from DOM');
                    } else {
                        console.warn('Mobile Grid: Task element not found in DOM:', taskId);
                        // Log all task elements to debug
                        const allTaskElements = document.querySelectorAll('[data-task-id], [id^="task-"]');
                        console.log('Mobile Grid: All task elements found:', allTaskElements);
                        allTaskElements.forEach(el => {
                            console.log('Mobile Grid: Task element:', {
                                dataTaskId: el.getAttribute('data-task-id'),
                                id: el.id,
                                text: el.textContent?.substring(0, 50)
                            });
                        });
                    }
                } else {
                    console.error('Mobile Grid: No task ID stored in state');
                }
            } else {
                console.error('Mobile Grid: Delete task failed:', e.detail);
            }
        }
        
        // Handle edit task form submission response
        if (e.target.id === 'modal-content' && e.detail.successful && e.detail.xhr && e.detail.xhr.responseText) {
            console.log('Mobile Grid: Edit task form submitted (modal-content):', e.detail);
            try {
                const response = JSON.parse(e.detail.xhr.responseText);
                console.log('Mobile Grid: Edit task response:', response);
                
                if (response.success && response.task_id && response.task_html) {
                    console.log('Mobile Grid: Updating task in place:', response.task_id);
                    
                    // Try multiple selectors to find the task element
                    let taskElement = document.querySelector(`[data-task-id="${response.task_id}"]`);
                    if (!taskElement) {
                        taskElement = document.getElementById(`task-${response.task_id}`);
                    }
                    if (!taskElement) {
                        // Try finding by task ID in any attribute
                        taskElement = document.querySelector(`[data-task-id*="${response.task_id}"], [id*="${response.task_id}"]`);
                    }
                    
                    if (taskElement) {
                        console.log('Mobile Grid: Found task element for edit, replacing with new HTML');
                        // Create a temporary container to parse the HTML
                        const tempContainer = document.createElement('div');
                        tempContainer.innerHTML = response.task_html;
                        const newTaskElement = tempContainer.firstElementChild;
                        
                        if (newTaskElement) {
                            // Replace the old task with the new one
                            taskElement.replaceWith(newTaskElement);
                            console.log('Mobile Grid: Task element successfully replaced');
                            // Re-process HTMX for the new element so edit button works
                            if (typeof htmx !== 'undefined') {
                                htmx.process(newTaskElement);
                                console.log('Mobile Grid: HTMX reprocessed for new task element');
                            }
                        } else {
                            console.warn('Mobile Grid: No new task element found in response HTML');
                        }
                    } else {
                        console.warn('Mobile Grid: Task element not found in DOM for edit:', response.task_id);
                        // Log all task elements to debug
                        const allTaskElements = document.querySelectorAll('[data-task-id], [id^="task-"]');
                        console.log('Mobile Grid: All task elements found for edit:', allTaskElements);
                        allTaskElements.forEach(el => {
                            console.log('Mobile Grid: Task element for edit:', {
                                dataTaskId: el.getAttribute('data-task-id'),
                                id: el.id,
                                text: el.textContent?.substring(0, 50)
                            });
                        });
                    }
                    
                    // Hide the modal
                    this.hideModal();
                } else {
                    console.log('Mobile Grid: Edit response does not contain task update data');
                }
            } catch (e) {
                console.log('Mobile Grid: Edit response is not JSON, continuing with normal modal handling');
                // Not a JSON response, continue with normal modal handling
            }
        }
        
        // Handle edit task form submission response (alternative detection)
        if (e.target.tagName === 'FORM' && e.detail.successful && e.detail.xhr && e.detail.xhr.responseText) {
            console.log('Mobile Grid: Form submission detected:', e.target);
            console.log('Mobile Grid: Form action:', e.target.action);
            console.log('Mobile Grid: Form method:', e.target.method);
            
            // Check if this is an edit form (task or row)
            if (e.target.action && e.target.action.includes('/edit/')) {
                try {
                    const response = JSON.parse(e.detail.xhr.responseText);
                    console.log('Mobile Grid: Edit form response:', response);
                    
                    // Check if this is a task edit
                    if (response.success && response.task_id && response.task_html) {
                        console.log('Mobile Grid: Edit task form detected');
                        console.log('Mobile Grid: Updating task in place (form):', response.task_id);
                        
                        // Try multiple selectors to find the task element
                        let taskElement = document.querySelector(`[data-task-id="${response.task_id}"]`);
                        if (!taskElement) {
                            taskElement = document.getElementById(`task-${response.task_id}`);
                        }
                        if (!taskElement) {
                            // Try finding by task ID in any attribute
                            taskElement = document.querySelector(`[data-task-id*="${response.task_id}"], [id*="${response.task_id}"]`);
                        }
                        
                        if (taskElement) {
                            console.log('Mobile Grid: Found task element for edit (form), replacing with new HTML');
                            // Create a temporary container to parse the HTML
                            const tempContainer = document.createElement('div');
                            tempContainer.innerHTML = response.task_html;
                            const newTaskElement = tempContainer.firstElementChild;
                            
                            if (newTaskElement) {
                                // Replace the old task with the new one
                                taskElement.replaceWith(newTaskElement);
                                console.log('Mobile Grid: Task element successfully replaced (form)');
                                // Re-process HTMX for the new element so edit button works
                                if (typeof htmx !== 'undefined') {
                                    htmx.process(newTaskElement);
                                    console.log('Mobile Grid: HTMX reprocessed for new task element (form)');
                                }
                            } else {
                                console.warn('Mobile Grid: No new task element found in response HTML (form)');
                            }
                        } else {
                            console.warn('Mobile Grid: Task element not found in DOM for edit (form):', response.task_id);
                        }
                        
                        // Hide the modal
                        this.hideModal();
                    }
                    // Check if this is a row edit
                    else if (response.success && response.row_name) {
                        console.log('Mobile Grid: Edit row form detected');
                        console.log('Mobile Grid: Row updated successfully:', response.row_name);
                        
                        // Update the row name in the UI
                        // Find the row that was edited by looking for the form that was submitted
                        const formAction = e.target.action;
                        const rowIdMatch = formAction.match(/\/rows\/(\d+)\/edit\//);
                        if (rowIdMatch) {
                            const rowId = rowIdMatch[1];
                            console.log('Mobile Grid: Looking for row with ID:', rowId);
                            // Find the row container and update its name
                            const rowContainers = document.querySelectorAll('.bg-[var(--container-bg)]');
                            rowContainers.forEach(container => {
                                const rowNameElement = container.querySelector('h3');
                                if (rowNameElement) {
                                    // Check if this row contains the edited row ID in its task containers
                                    const taskContainers = container.querySelectorAll('[id^="tasks-"]');
                                    taskContainers.forEach(taskContainer => {
                                        if (taskContainer.id.includes(`-${rowId}-`)) {
                                            rowNameElement.textContent = response.row_name;
                                            console.log('Mobile Grid: Updated row name in UI:', response.row_name);
                                        }
                                    });
                                }
                            });
                        }
                        // Hide the modal (do not reload the page)
                        this.hideModal();
                        // Do not reload or refresh the column
                        return;
                    } else {
                        console.log('Mobile Grid: Edit response does not contain expected update data (form)');
                    }
                } catch (e) {
                    console.log('Mobile Grid: Edit response is not JSON (form), continuing with normal modal handling');
                    // Not a JSON response, continue with normal modal handling
                }
            }
        }
        
        // Handle row deletion form submission
        if (e.target.id === 'delete-row-form' && e.detail.successful) {
            console.log('Mobile Grid: Row deletion form submitted successfully');
            try {
                const response = JSON.parse(e.detail.xhr.responseText);
                console.log('Mobile Grid: Row deletion response:', response);
                
                if (response.success) {
                    console.log('Mobile Grid: Row deleted successfully, refreshing page');
                    // Hide the delete modal
                    this.hideDeleteRowModal();
                    // Refresh the page to show updated grid
                    window.location.reload();
                } else {
                    console.error('Mobile Grid: Row deletion failed:', response.message);
                }
            } catch (e) {
                console.log('Mobile Grid: Row deletion response is not JSON, refreshing page');
                // Hide the delete modal
                this.hideDeleteRowModal();
                // Refresh the page to show updated grid
                window.location.reload();
            }
        }
        
        // Restore scroll position for mobile grid
        this.restoreScrollPosition();
        
        // Reinitialize components that might have been replaced
        this.reinitializeComponents();
        // Set container height after content changes
        this.setContainerHeightToActiveColumn();
    }

    handleHtmxAfterSwap(e) {
        console.log('Mobile Grid: HTMX afterSwap event:', e.detail);
        
        // Hide loading indicator when content is swapped
        if (e.target.id === 'modal-content') {
            const loadingIndicator = e.target.querySelector('.htmx-indicator');
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
            
            // Ensure modal is visible and centered
            this.showModal();
        }
        
        // Handle edit task form submission response
        if (e.target.id === 'modal-content' && e.detail.xhr && e.detail.xhr.responseText) {
            console.log('Mobile Grid: Processing modal content response');
            try {
                const response = JSON.parse(e.detail.xhr.responseText);
                console.log('Mobile Grid: Parsed response:', response);
                
                if (response.success && response.task_id && response.task_html) {
                    console.log('Mobile Grid: Updating task in place:', response.task_id);
                    // Update the task in place
                    const taskElement = document.querySelector(`[data-task-id="${response.task_id}"]`);
                    if (taskElement) {
                        console.log('Mobile Grid: Found task element, replacing with new HTML');
                        // Create a temporary container to parse the HTML
                        const tempContainer = document.createElement('div');
                        tempContainer.innerHTML = response.task_html;
                        const newTaskElement = tempContainer.firstElementChild;
                        
                        if (newTaskElement) {
                            // Replace the old task with the new one
                            taskElement.replaceWith(newTaskElement);
                            console.log('Mobile Grid: Task element successfully replaced');
                            // Re-process HTMX for the new element so edit button works
                            if (typeof htmx !== 'undefined') {
                                htmx.process(newTaskElement);
                                console.log('Mobile Grid: HTMX reprocessed for new task element');
                            }
                        } else {
                            console.warn('Mobile Grid: No new task element found in response HTML');
                        }
                    } else {
                        console.warn('Mobile Grid: Task element not found in DOM:', response.task_id);
                        // Try to find by ID as fallback
                        const taskElementById = document.getElementById(`task-${response.task_id}`);
                        if (taskElementById) {
                            console.log('Mobile Grid: Found task element by ID, replacing');
                            const tempContainer = document.createElement('div');
                            tempContainer.innerHTML = response.task_html;
                            const newTaskElement = tempContainer.firstElementChild;
                            
                            if (newTaskElement) {
                                taskElementById.replaceWith(newTaskElement);
                                console.log('Mobile Grid: Task element successfully replaced by ID');
                                // Re-process HTMX for the new element so edit button works
                                if (typeof htmx !== 'undefined') {
                                    htmx.process(newTaskElement);
                                    console.log('Mobile Grid: HTMX reprocessed for new task element by ID');
                                }
                            }
                        } else {
                            console.error('Mobile Grid: Task element not found by ID either:', response.task_id);
                        }
                    }
                    
                    // Hide the modal
                    this.hideModal();
                } else {
                    console.log('Mobile Grid: Response does not contain task update data');
                }
            } catch (e) {
                console.log('Mobile Grid: Not a JSON response, continuing with normal modal handling');
                // Not a JSON response, continue with normal modal handling
            }
        }
        
        // Handle focus management for new content
        if (e.target.id === 'modal-content') {
            const firstInput = e.target.querySelector('input, textarea, select, button');
            if (firstInput) {
                setTimeout(() => {
                    firstInput.focus();
                }, 100);
            }
            
            // Add escape key handler for new modal content
            const handleKeyDown = (evt) => {
                if (evt.key === 'Escape') {
                    this.hideModal();
                    document.removeEventListener('keydown', handleKeyDown);
                }
            };
            document.addEventListener('keydown', handleKeyDown);
        }
        
        // Restore scroll position
        this.restoreScrollPosition();
        // Set container height after content changes
        this.setContainerHeightToActiveColumn();
    }
    
    handleHtmxError(e) {
        console.error('Mobile Grid: HTMX Error:', e.detail);
        
        // Handle modal content errors
        if (e.detail.target && e.detail.target.id === 'modal-content') {
            this.elements.modalContent.innerHTML = `<div class="flex items-center justify-center p-8"><div class="flex flex-col items-center space-y-3 text-center"><div class="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center"><i class="fas fa-exclamation-triangle text-red-500 text-xl"></i></div><div><h3 class="text-lg font-medium text-[var(--text-primary)]">Error Loading Content</h3><p class="text-sm text-[var(--text-secondary)] mt-1">Unable to load the requested content. Please try again.</p></div><button type="button" class="close-modal mt-4 px-4 py-2 bg-[var(--primary-action-bg)] hover:bg-[var(--primary-action-hover-bg)] text-white rounded-lg transition-colors">Close</button></div></div>`;
        }
        
        // Handle task form submission errors
        if (e.detail.target && e.detail.target.classList.contains('task-form')) {
            const errorDiv = e.detail.target.querySelector('.error-message');
            if (errorDiv) {
                if (e.detail.xhr && e.detail.xhr.status === 0) {
                    // Connection refused or network error
                    errorDiv.innerHTML = 'Network error: Unable to connect to server. Please check your connection and try again.';
                } else if (e.detail.xhr && e.detail.xhr.status >= 500) {
                    // Server error
                    errorDiv.innerHTML = 'Server error: Please try again later.';
                } else if (e.detail.xhr && e.detail.xhr.status >= 400) {
                    // Client error
                    errorDiv.innerHTML = 'Request error: Please check your input and try again.';
                } else {
                    // Generic error
                    errorDiv.innerHTML = 'An error occurred. Please try again.';
                }
                errorDiv.style.display = 'block';
            }
            
            // Reset form state
            const submitBtn = e.detail.target.querySelector('button[type="submit"]');
            if (submitBtn) {
                const spinner = submitBtn.querySelector('.htmx-indicator-spinner');
                if (spinner) {
                    spinner.style.opacity = '0';
                }
            }
        }
    }

    // Grid state management
    handleRefreshGrid() { window.location.reload(); }
    handleScrollToEnd() {
        sessionStorage.setItem('scrollToEnd', 'true');
        window.location.reload();
    }
    handleResetGridToInitial() {
        sessionStorage.setItem('resetToInitial', 'true');
        window.location.reload();
    }
    handleWindowResize() {
        this.scrollToCol(this.state.currentCol, 'auto');
    }

    restoreScrollPosition() {
        const scrollToEnd = sessionStorage.getItem('scrollToEnd');
        const resetToInitial = sessionStorage.getItem('resetToInitial');
        
        sessionStorage.removeItem('scrollToEnd');
        sessionStorage.removeItem('resetToInitial');

        if (resetToInitial) {
            this.scrollToCol(0, 'auto');
            return;
        }
        if (scrollToEnd) {
            // Recalculate total columns from DOM
            const columns = document.querySelectorAll('.mobile-column');
            if (columns.length > 0) {
                this.state.totalColumns = columns.length;
                this.scrollToCol(this.state.totalColumns - 1, 'auto');
            }
        }
    }

    setContainerHeightToActiveColumn() {
        // Find the active column
        const activeCol = Array.from(this.elements.columns).find(col => col.classList.contains('active'));
        if (activeCol) {
            // Get the height of the active column's content
            const contentHeight = activeCol.scrollHeight;
            const marginOfError = 75; // Add extra space to avoid cut-off
            const totalHeight = contentHeight + marginOfError;
            // Set the container's height to match
            if (this.elements.gridContainer) {
                this.elements.gridContainer.style.height = totalHeight + 'px';
            }
            // Optionally, also set the slider's height
            if (this.elements.gridSlider) {
                this.elements.gridSlider.style.height = totalHeight + 'px';
            }
        }
    }


    reinitializeComponents() {
        const currentCol = this.state.currentCol;
        this.cacheElements();
        this.setupMobileGrid();
        this.state.currentCol = currentCol; // Restore state
        this.scrollToCol(this.state.currentCol, 'auto'); // Re-apply state to UI
    }

    cleanup() {
        this.eventListeners.forEach((listeners, element) => {
            listeners.forEach(({ event, handler }) => {
                element.removeEventListener(event, handler);
            });
        });
        this.eventListeners.clear();
    }

    init() {
        this.cacheElements();
        console.log('Mobile Grid Manager initialized. Modal elements:', {
            deleteModal: this.elements.deleteModal,
            modal: this.elements.modal,
            modalContent: this.elements.modalContent
        });
        console.log('Mobile Grid Manager: HTMX available:', typeof htmx !== 'undefined');
        this.addEventListeners();
        this.setupMobileGrid();
        this.restoreScrollPosition();

        if (typeof htmx !== 'undefined') {
            htmx.config.disableSelector = '[hx-disable]';
            htmx.config.useTemplateFragments = false;
            console.log('Mobile Grid Manager: HTMX configuration applied');
        }
        
        // Test if HTMX events are being captured
        console.log('Mobile Grid Manager: Event listeners added, testing HTMX event capture');
    }
}

function validateTaskForm(form) {
    const textInput = form.querySelector('input[name="text"]');
    const errorDiv = form.querySelector('.error-message');
    
    if (!textInput || !errorDiv) return true;
    
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

document.addEventListener('DOMContentLoaded', function() {
    window.mobileGridManager = new MobileGridManager();
});

// Global function to close all dropdowns - called from inline onclick handlers
window.closeAllDropdowns = function() {
    if (window.mobileGridManager) {
        window.mobileGridManager.closeAllDropdowns();
    }
};



window.addEventListener('beforeunload', function() {
    if (window.mobileGridManager) {
        window.mobileGridManager.cleanup();
    }
});