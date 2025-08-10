// Grid JavaScript - Mobile Version
class MobileGridManager {
    constructor() {
        // Only initialize on mobile - don't interfere with desktop
        if (window.innerWidth >= 769) {
            return;
        }
        
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

    // Initialize SortableJS for mobile task lists (clone-on-drag for smooth touch UX)
    initializeSortable() {
        // Ensure Sortable is available and we are on mobile
        if (typeof Sortable === 'undefined' || window.innerWidth >= 769) {
            return;
        }

        // Find all task containers (each cell task list)
        const taskContainers = document.querySelectorAll('[data-row][data-col]');
        taskContainers.forEach(container => {
            new Sortable(container, {
                handle: '.drag-handle',
                animation: 150,
                ghostClass: 'sortable-ghost',
                dragClass: 'sortable-drag',
                chosenClass: 'sortable-chosen',
                group: false,
                // On mobile we force fallback so a clone follows the finger
                forceFallback: true,
                fallbackOnBody: true,
                fallbackTolerance: 3,
                onEnd: () => {
                    const order = this.getTaskOrder();
                    this.saveTaskOrder(order);
                }
            });
        });
    }

    // Collect current order for all tasks similar to desktop
    getTaskOrder() {
        const order = [];
        document.querySelectorAll('[data-task-id]').forEach(task => {
            order.push({
                id: task.dataset.taskId,
                row: task.dataset.taskRow,
                col: task.dataset.taskCol,
                order: parseInt(task.dataset.taskOrder) || 0
            });
        });
        return order;
    }

    // Save order to server (reuse endpoints)
    saveTaskOrder(newOrder) {
        const projectId = this.getProjectId();
        if (!projectId) return;
        fetch(`/grids/${projectId}/tasks/reorder/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({ task_order: newOrder })
        }).then(() => {
            // no-op on success; UI already reflects order
        }).catch(() => {
            // ignore for now on mobile
        });
    }

    getProjectId() {
        const urlParts = window.location.pathname.split('/');
        const gridsIdx = urlParts.indexOf('grids');
        if (gridsIdx >= 0 && gridsIdx + 1 < urlParts.length) {
            return urlParts[gridsIdx + 1];
        }
        return null;
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
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
            this.clearModalContent(); // Always show loading spinner
            this.showModal();
            return;
        }

        // Handle modal triggers that use onclick handlers (fallback for mobile)
        if (e.target.closest('[onclick*="modal"]') || e.target.closest('[onclick*="Modal"]')) {
            const trigger = e.target.closest('[onclick*="modal"]') || e.target.closest('[onclick*="Modal"]');
            if (trigger) {
                this.clearModalContent();
                this.showModal();
                return;
            }
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
            e.preventDefault();
            this.showDeleteModal(deleteTaskBtn.dataset.taskId, deleteTaskBtn.dataset.taskText, deleteTaskBtn.dataset.deleteUrl);
            return;
        }

        const deleteRowBtn = e.target.closest('.delete-row-btn');
        if (deleteRowBtn) {
            e.preventDefault();
            this.showDeleteRowModal(deleteRowBtn.dataset.rowId, deleteRowBtn.dataset.rowName, deleteRowBtn.dataset.deleteUrl);
            return;
        }

        const closeModalBtn = e.target.closest('.close-modal, #close-delete-modal, #cancel-delete-task, #close-delete-row-modal, #cancel-delete-row');
        if (closeModalBtn) {
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

        // Update the column header UI first
        this.updateUI();

        // Dynamically update Edit/Delete Column actions for the current column (do not touch column header)
        const editColBtn = document.getElementById('edit-column-btn');
        const deleteColBtn = document.getElementById('delete-column-btn');
        if (editColBtn && deleteColBtn && this.elements.columns[this.state.currentCol]) {
            const colPk = this.elements.columns[this.state.currentCol].getAttribute('data-column-id');
            const projectPk = editColBtn.getAttribute('data-project-pk');
            if (colPk && projectPk) {
                editColBtn.setAttribute('data-col-pk', colPk);
                deleteColBtn.setAttribute('data-col-pk', colPk);
                // Update hx-get URLs using Django's expected pattern
                editColBtn.setAttribute('hx-get', `/pages/columns/${colPk}/edit/?project_pk=${projectPk}`);
                deleteColBtn.setAttribute('hx-get', `/pages/columns/${colPk}/delete/?project_pk=${projectPk}`);
            }
        }

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
        this.setModalState(this.elements.deleteModal, this.elements.deleteModalContent, false);
        this.state.currentTaskId = null;
        this.state.currentDeleteUrl = null;
    }

    showDeleteRowModal(rowId, rowName, deleteUrl) {
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
        this.setModalState(this.elements.deleteRowModal, this.elements.deleteRowModalContent, false);
        this.state.currentRowId = null;
        this.state.currentRowDeleteUrl = null;
    }

    showModal() { 
        this.setModalState(this.elements.modal, this.elements.modalContent, true); 
        // Ensure modal is properly positioned on mobile
        if (this.elements.modal) {
            this.elements.modal.style.display = 'flex';
            this.elements.modal.style.alignItems = 'center';
            this.elements.modal.style.justifyContent = 'center';
        }
    }
    hideModal() { 
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
            return;
        }
        
        if (isOpen) {
            modal.classList.remove('opacity-0', 'invisible');
            modal.classList.add('opacity-100', 'visible');
            content.classList.remove('scale-95');
            content.classList.add('scale-100');
            
            // Prevent body scroll
            document.body.style.overflow = 'hidden';
            
            // Mobile-specific modal positioning
            if (window.innerWidth <= 768) {
                modal.style.position = 'fixed';
                modal.style.top = '0';
                modal.style.left = '0';
                modal.style.right = '0';
                modal.style.bottom = '0';
                modal.style.zIndex = '9999';
            }
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
        // Hide loading indicator when request completes
        if (e.target.id === 'modal-content') {
            const loadingIndicator = e.target.querySelector('.htmx-indicator');
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
        }
        
        // Handle task form submission
        if (e.target.classList.contains('task-form')) {
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
                
                // Re-process HTMX for any new task elements that were added
                setTimeout(() => {
                    const taskList = e.target.closest('.task-list');
                    if (taskList) {
                        const newTaskElements = taskList.querySelectorAll('[data-task-id]');
                        if (typeof htmx !== 'undefined') {
                            newTaskElements.forEach(element => {
                                htmx.process(element);
                            });
                        }
                    }
                }, 100);
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
            if (e.detail.successful && e.detail.xhr && e.detail.xhr.responseText) {
                try {
                    const response = JSON.parse(e.detail.xhr.responseText);
                    if (response.success !== undefined) {
                        // The visual changes are already applied by the hyperscript in the template
                        // This just ensures the server response is handled properly
                    }
                } catch (e) {
                    // Not a JSON response, continue with normal handling
                }
            }
        }
        
        // Handle delete task form submission
        if (e.target.id === 'delete-task-form') {
            if (e.detail.successful) {
                // Store the task ID before hiding the modal (which clears it)
                const taskId = this.state.currentTaskId;
                
                // Hide the delete modal
                this.hideDeleteModal();
                
                // Remove the task from the DOM
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
                        taskElement.remove();
                    }
                }
            }
        }
        
        // Handle edit task form submission response
        if (e.target.id === 'modal-content' && e.detail.successful && e.detail.xhr && e.detail.xhr.responseText) {
            try {
                const response = JSON.parse(e.detail.xhr.responseText);
                
                if (response.success && response.task_id && response.task_html) {
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
                        // Create a temporary container to parse the HTML
                        const tempContainer = document.createElement('div');
                        tempContainer.innerHTML = response.task_html;
                        const newTaskElement = tempContainer.firstElementChild;
                        
                        if (newTaskElement) {
                            // Replace the old task with the new one
                            taskElement.replaceWith(newTaskElement);
                            // Re-process HTMX for the new element so edit button works
                            if (typeof htmx !== 'undefined') {
                                htmx.process(newTaskElement);
                            }
                        }
                    }
                    
                    // Hide the modal
                    this.hideModal();
                }
            } catch (e) {
                // Not a JSON response, continue with normal modal handling
            }
        }
        
        // Handle edit task form submission response (alternative detection)
        if (e.target.tagName === 'FORM' && e.detail.successful && e.detail.xhr && e.detail.xhr.responseText) {
            // Check if this is an edit form (task or row or column)
            if (e.target.action && e.target.action.includes('/edit/')) {
                try {
                    const response = JSON.parse(e.detail.xhr.responseText);
                    
                    // Check if this is a task edit
                    if (response.success && response.task_id && response.task_html) {
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
                            // Create a temporary container to parse the HTML
                            const tempContainer = document.createElement('div');
                            tempContainer.innerHTML = response.task_html;
                            const newTaskElement = tempContainer.firstElementChild;
                            
                            if (newTaskElement) {
                                // Replace the old task with the new one
                                taskElement.replaceWith(newTaskElement);
                                // Re-process HTMX for the new element so edit button works
                                if (typeof htmx !== 'undefined') {
                                    htmx.process(newTaskElement);
                                }
                            }
                        }
                        
                        // Hide the modal
                        this.hideModal();
                    }
                    // Check if this is a row edit
                    else if (response.success && response.row_name) {
                        // Update all row headers with the matching data-row-id
                        const formAction = e.target.action;
                        const rowIdMatch = formAction.match(/\/rows\/(\d+)\/edit\//);
                        if (rowIdMatch) {
                            const rowId = rowIdMatch[1];
                            const rowHeaders = document.querySelectorAll(`h3[data-row-id='${rowId}']`);
                            rowHeaders.forEach(header => {
                                header.textContent = response.row_name;
                            });
                        }
                        // Hide the modal (do not reload the page)
                        this.hideModal();
                        // Do not reload or refresh the column
                        return;
                    }
                    // Check if this is a column edit
                    else if (response.success && response.col_name) {
                        // Update the column header UI
                        if (this.elements.columnHeader) {
                            this.elements.columnHeader.textContent = response.col_name;
                            this.elements.columnHeader.dataset.columnName = response.col_name;
                        }
                        // Update the current column's data attribute
                        const colEl = this.elements.columns[this.state.currentCol];
                        if (colEl) {
                            colEl.setAttribute('data-column-name', response.col_name);
                        }
                        this.hideModal();
                        return;
                    }
                } catch (e) {
                    // Not a JSON response, continue with normal modal handling
                }
            }
        }
        
        // Handle row deletion form submission
        if (e.target.id === 'delete-row-form' && e.detail.successful) {
            try {
                const response = JSON.parse(e.detail.xhr.responseText);
                
                if (response.success) {
                    // Hide the delete modal
                    this.hideDeleteRowModal();
                    // Refresh the page to show updated grid
                    window.location.reload();
                }
            } catch (e) {
                // Hide the delete modal
                this.hideDeleteRowModal();
                // Refresh the page to show updated grid
                window.location.reload();
            }
        }
        
        // Restore scroll position for mobile grid
        this.restoreScrollPosition();
        
        // Reinitialize components that might have been replaced
        // Only reinitialize if the grid content itself was swapped, not the modal or anything else
        if (e.target && e.target.id === 'grid-content') {
            this.reinitializeComponents();
        }
        // Set container height after content changes
        this.setContainerHeightToActiveColumn();
    }

    handleHtmxAfterSwap(e) {
        // Hide loading indicator when content is swapped
        if (e.target.id === 'modal-content') {
            const loadingIndicator = e.target.querySelector('.htmx-indicator');
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
            
            // Ensure modal is visible and centered
            this.showModal();
        }
        
        // Handle task list updates (new tasks added)
        if (e.target.classList.contains('task-list')) {
            // Re-process HTMX for any new task elements
            const newTaskElements = e.target.querySelectorAll('[data-task-id]');
            if (typeof htmx !== 'undefined') {
                newTaskElements.forEach(element => {
                    htmx.process(element);
                });
            }
        }
        
        // Handle edit task form submission response
        if (e.target.id === 'modal-content' && e.detail.xhr && e.detail.xhr.responseText) {
            try {
                const response = JSON.parse(e.detail.xhr.responseText);
                
                if (response.success && response.task_id && response.task_html) {
                    // Update the task in place
                    const taskElement = document.querySelector(`[data-task-id="${response.task_id}"]`);
                    if (taskElement) {
                        // Create a temporary container to parse the HTML
                        const tempContainer = document.createElement('div');
                        tempContainer.innerHTML = response.task_html;
                        const newTaskElement = tempContainer.firstElementChild;
                        
                        if (newTaskElement) {
                            // Replace the old task with the new one
                            taskElement.replaceWith(newTaskElement);
                            // Re-process HTMX for the new element so edit button works
                            if (typeof htmx !== 'undefined') {
                                htmx.process(newTaskElement);
                            }
                        }
                    } else {
                        // Try to find by ID as fallback
                        const taskElementById = document.getElementById(`task-${response.task_id}`);
                        if (taskElementById) {
                            const tempContainer = document.createElement('div');
                            tempContainer.innerHTML = response.task_html;
                            const newTaskElement = tempContainer.firstElementChild;
                            
                            if (newTaskElement) {
                                taskElementById.replaceWith(newTaskElement);
                                // Re-process HTMX for the new element so edit button works
                                if (typeof htmx !== 'undefined') {
                                    htmx.process(newTaskElement);
                                }
                            }
                        }
                    }
                    
                    // Hide the modal
                    this.hideModal();
                }
            } catch (e) {
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
        this.addEventListeners();
        this.setupMobileGrid();
        this.restoreScrollPosition();
        // Drag-and-drop disabled on mobile
        
        // Mobile-specific form handling - let HTMX handle task forms
        if (window.innerWidth <= 768) {
            document.addEventListener('submit', (e) => {
                const form = e.target;
                if (form.classList.contains('task-form') && form.hasAttribute('hx-post')) {
                    // Let HTMX handle the submission naturally
                    // Don't prevent default - let HTMX do its job
                }
            }, true);
        }

        // Update Edit/Delete Column actions when Actions menu is opened
        const actionsMenuBtn = document.getElementById('actions-menu-btn');
        if (actionsMenuBtn) {
            actionsMenuBtn.addEventListener('click', () => {
                const editColBtn = document.getElementById('edit-column-btn');
                const deleteColBtn = document.getElementById('delete-column-btn');
                const colEl = this.elements.columns[this.state.currentCol];
                if (editColBtn && deleteColBtn && colEl) {
                    const colPk = colEl.getAttribute('data-column-id');
                    const projectPk = editColBtn.getAttribute('data-project-pk');
                    const editUrl = colEl.getAttribute('data-edit-url');
                    const deleteUrl = colEl.getAttribute('data-delete-url');
                    if (colPk && projectPk && editUrl && deleteUrl) {
                        editColBtn.setAttribute('data-col-pk', colPk);
                        deleteColBtn.setAttribute('data-col-pk', colPk);
                        editColBtn.setAttribute('hx-get', editUrl);
                        deleteColBtn.setAttribute('hx-get', deleteUrl);
                        editColBtn.disabled = false;
                        deleteColBtn.disabled = false;
                        if (typeof htmx !== 'undefined') {
                            htmx.process(editColBtn);
                            htmx.process(deleteColBtn);
                        }
                    }
                }
            });
        }

        if (typeof htmx !== 'undefined') {
            htmx.config.disableSelector = '[hx-disable]';
            htmx.config.useTemplateFragments = false;
            
            // Mobile-specific HTMX configuration
            htmx.config.timeout = 30000; // 30 second timeout for mobile
            htmx.config.requestClass = 'htmx-request';
            htmx.config.settlingClass = 'htmx-settling';
            htmx.config.swappingClass = 'htmx-swapping';
            
            // Ensure proper event handling on mobile
            htmx.config.allowEval = false;
            htmx.config.includeIndicatorStyles = false;
        }
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