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
            currentTaskId: null,
            currentDeleteUrl: null,
            currentRowId: null,
            currentRowDeleteUrl: null,
            currentColumnId: null,
            currentColumnDeleteUrl: null,
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
            // Grid Tabs
            gridTabs: '#grid-tabs',
            
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
            saveTemplateModal: '#save-template-modal',
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

        const actionBtn = e.target.closest('.column-actions-btn, .row-actions-btn');
        if (actionBtn) {
            e.stopPropagation(); this.toggleActionDropdown(actionBtn); return;
        }
        if (!e.target.closest('.column-actions-dropdown, .row-actions-dropdown')) this.closeAllActionDropdowns();

        const deleteTaskBtn = e.target.closest('.delete-task-btn');
        if (deleteTaskBtn) {
            e.preventDefault();
            e.stopPropagation(); // Prevent task selection when clicking delete
            this.showDeleteModal(deleteTaskBtn.dataset.taskId, deleteTaskBtn.dataset.taskText, deleteTaskBtn.dataset.deleteUrl);
            return;
        }

        const deleteRowBtn = e.target.closest('.delete-row-btn');
        if (deleteRowBtn) {
            e.preventDefault();
            this.showDeleteRowModal(deleteRowBtn.dataset.rowId, deleteRowBtn.dataset.rowName, deleteRowBtn.dataset.deleteUrl);
            return;
        }

        const deleteColumnBtn = e.target.closest('.delete-column-btn');
        if (deleteColumnBtn) {
            e.preventDefault();
            e.stopPropagation(); // Prevent column editing when clicking delete
            this.showDeleteColumnModal(deleteColumnBtn.dataset.columnId, deleteColumnBtn.dataset.columnName, deleteColumnBtn.dataset.deleteUrl);
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

        // Handle task selection and editing
        const taskItem = e.target.closest('[data-task-id]');
        if (taskItem && !e.target.closest('input[type="checkbox"]') && !e.target.closest('button') && !e.target.closest('form')) {
            // If clicking on task text specifically, start editing
            const taskText = e.target.closest('[id^="task-text-"]');
            if (taskText && !taskText.classList.contains('editing')) {
                this.handleTaskSelection(taskItem);
                this.startTaskEditing(taskText);
            } else {
                this.handleTaskSelection(taskItem);
            }
            return;
        }

        // Handle row editing
        const rowHeader = e.target.closest('h3[data-row-id]');
        if (rowHeader && !rowHeader.classList.contains('editing') && !e.target.closest('button') && !e.target.closest('.mobile-row-actions')) {
            this.startRowEditing(rowHeader);
            return;
        }

        // Handle column editing
        const columnHeader = e.target.closest('#mobile-column-header h2');
        if (columnHeader && !columnHeader.classList.contains('editing')) {
            this.startColumnEditing(columnHeader);
            return;
        }
    }

    // Function to close all dropdowns - called from inline onclick handlers
    closeAllDropdowns() {
        this.closeAllActionDropdowns();
    }

    // Handle task selection
    handleTaskSelection(taskItem) {
        // Find the main task container - the one with id="task-{id}"
        let mainTaskContainer = taskItem;
        
        // If we clicked on the inner task-text element, find the parent task container
        if (taskItem.id && taskItem.id.startsWith('task-text-')) {
            const taskId = taskItem.id.replace('task-text-', '');
            mainTaskContainer = document.getElementById(`task-${taskId}`);
        }
        
        // If still not found, use closest to find the main task container
        if (!mainTaskContainer || !mainTaskContainer.id || !mainTaskContainer.id.startsWith('task-')) {
            mainTaskContainer = taskItem.closest('[id^="task-"]:not([id*="text"])');
        }
        
        // Remove selection from all other tasks
        this.clearAllTaskSelections();
        
        // Add selection to the main task container
        if (mainTaskContainer) {
            mainTaskContainer.classList.add('task-selected');
        }
    }
    
    // Clear all task selections
    clearAllTaskSelections() {
        document.querySelectorAll('.task-selected').forEach(task => {
            task.classList.remove('task-selected');
        });
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
        
        // Hide task action buttons after grid setup
        this.hideTaskActionButtons();
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
            this.closeAllActionDropdowns();
            this.hideDeleteModal();
            this.hideDeleteRowModal();
            this.hideModal();
            this.collapseAllAddTaskForms();
            this.closeAllTaskEditing();
            this.closeAllRowEditing();
            this.closeAllColumnEditing();
        } else if (e.key === 'ArrowLeft') {
            this.scrollToCol(this.state.currentCol - 1);
        } else if (e.key === 'ArrowRight') {
            this.scrollToCol(this.state.currentCol + 1);
        }
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
        this.state.currentColumnId = null;
        this.state.currentColumnDeleteUrl = null;
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

    showDeleteColumnModal(columnId, columnName, deleteUrl) {
        // For now, we'll use the same delete modal structure as tasks
        // In a full implementation, you might want a separate column delete modal
        this.state.currentColumnId = columnId;
        this.state.currentColumnDeleteUrl = deleteUrl;
        
        if (this.elements.taskToDelete) this.elements.taskToDelete.textContent = `column "${columnName}"`;
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
    
    showSaveTemplateModal() {
        if (this.elements.saveTemplateModal) {
            this.elements.saveTemplateModal.classList.remove('opacity-0', 'invisible');
            this.elements.saveTemplateModal.classList.add('opacity-100', 'visible');
            const modalContent = this.elements.saveTemplateModal.querySelector('div');
            if (modalContent) {
                modalContent.classList.remove('scale-95');
                modalContent.classList.add('scale-100');
            }
            document.body.style.overflow = 'hidden';
        }
    }
    
    hideSaveTemplateModal() {
        if (this.elements.saveTemplateModal) {
            this.elements.saveTemplateModal.classList.add('opacity-0', 'invisible');
            this.elements.saveTemplateModal.classList.remove('opacity-100', 'visible');
            const modalContent = this.elements.saveTemplateModal.querySelector('div');
            if (modalContent) {
                modalContent.classList.remove('scale-100');
                modalContent.classList.add('scale-95');
            }
            document.body.style.overflow = '';
        }
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
        if (collapsed && expanded && input) {
            collapsed.style.display = 'none';
            expanded.classList.remove('hidden');
            
            // Immediately focus and trigger mobile keyboard
            setTimeout(() => {
                input.focus();
                input.click(); // Additional click to ensure mobile keyboard appears
                
                // For iOS specifically, ensure keyboard appears
                if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
                    input.setAttribute('readonly', false);
                    input.removeAttribute('readonly');
                }
            }, 50); // Reduced timeout for faster response
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

    // Inline task editing methods
    startTaskEditing(taskElement) {
        if (!taskElement) return;
        
        // Close any other editing tasks first
        this.closeAllTaskEditing();
        

        
        const taskText = taskElement.textContent.trim();
        const taskId = taskElement.dataset.taskId;
        
        // Store original content for restoration
        taskElement.dataset.originalContent = taskElement.innerHTML;
        taskElement.dataset.originalText = taskText;
        
        // Create editing textarea for multi-line support
        const editInput = document.createElement('textarea');
        
        // Get computed styles from the actual text element (p tag) to match exactly
        const textElement = taskElement.querySelector('p') || taskElement;
        const computedStyle = window.getComputedStyle(textElement);
        
        // Copy ALL computed styles to ensure exact match
        editInput.style.cssText = `
            width: 100% !important;
            border: 2px dashed #f97316 !important;
            border-radius: 6px !important;
            background: transparent !important;
            outline: none !important;
            resize: none !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
            font-size: ${computedStyle.fontSize} !important;
            line-height: ${computedStyle.lineHeight} !important;
            font-family: ${computedStyle.fontFamily} !important;
            font-weight: ${computedStyle.fontWeight} !important;
            color: ${computedStyle.color} !important;
            letter-spacing: ${computedStyle.letterSpacing} !important;
            text-align: ${computedStyle.textAlign} !important;
            padding: 4px 8px !important;
            margin: 0 !important;
            min-height: 24px !important;
        `;
        
        editInput.value = taskText;
        editInput.maxLength = 500;
        
        // Auto-resize function
        const autoResize = () => {
            editInput.style.height = 'auto';
            editInput.style.height = editInput.scrollHeight + 'px';
        };
        
        // Replace the text content with the input
        taskElement.innerHTML = '';
        taskElement.appendChild(editInput);
        
        // Add editing class
        taskElement.classList.add('editing');
        
        // Auto-resize initially and on input
        autoResize();
        editInput.addEventListener('input', autoResize);
        
        // Focus the input
            editInput.focus();
            editInput.select();
        
        // Add keyboard event listeners
        const handleKeydown = (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                // Ctrl+Enter or Cmd+Enter to save (allow normal Enter for new lines)
                e.preventDefault();
                this.saveTaskEditing(taskElement);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                this.cancelTaskEditing(taskElement);
            }
            // Allow normal Enter key for line breaks in textarea
        };
        
        // Add blur event to save when input loses focus
        const handleBlur = () => {
            setTimeout(() => this.saveTaskEditing(taskElement), 100);
        };
        
        editInput.addEventListener('keydown', handleKeydown);
        editInput.addEventListener('blur', handleBlur);
        
        // Store handlers for cleanup
        taskElement._keydownHandler = handleKeydown;
        taskElement._blurHandler = handleBlur;
        taskElement._autoResize = autoResize;
        taskElement._editInput = editInput;
    }

    saveTaskEditing(taskElement) {
        if (!taskElement || !taskElement._editInput) return;
        
        const input = taskElement._editInput;
        const newText = input.value.trim();
        const taskId = taskElement.dataset.taskId;
        
        if (!newText) {
            // Don't save empty text
            this.cancelTaskEditing(taskElement);
            return;
        }
        
        if (newText === taskElement.dataset.originalText) {
            // No changes, just cancel editing
            this.cancelTaskEditing(taskElement);
            return;
        }
        
        // Send update to server
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
                // Update the task text and restore normal view (preserve line breaks)
                const formattedText = newText.replace(/\n/g, '<br>');
                taskElement.innerHTML = `<p>${formattedText}</p>`;
                taskElement.classList.remove('editing');
                
                // Update the dataset for future reference
                taskElement.dataset.originalText = newText;
                
                // Clean up event listeners
                if (taskElement._editInput) {
                    if (taskElement._keydownHandler) {
                        taskElement._editInput.removeEventListener('keydown', taskElement._keydownHandler);
                    }
                    if (taskElement._blurHandler) {
                        taskElement._editInput.removeEventListener('blur', taskElement._blurHandler);
                    }
                    if (taskElement._autoResize) {
                        taskElement._editInput.removeEventListener('input', taskElement._autoResize);
                    }
                }
                
                // Clean up references
                delete taskElement._keydownHandler;
                delete taskElement._blurHandler;
                delete taskElement._autoResize;
                delete taskElement._editInput;
                delete taskElement.dataset.originalContent;
                

                
                // Clear task selection (remove orange dotted border and delete button)
                // Remove selection from all tasks to ensure clean state
                document.querySelectorAll('.task-selected').forEach(task => {
                    task.classList.remove('task-selected');
                });
                
                // Also specifically target the main container
                const mainTaskContainer = taskElement.closest('[id^="task-"]');
                if (mainTaskContainer) {
                    mainTaskContainer.classList.remove('task-selected');
                }
                

            } else {
                // Show error and restore original
                console.error('Failed to save task:', data.errors || data.error || 'Unknown error');
                this.cancelTaskEditing(taskElement);
            }
        })
        .catch(error => {
            console.error('Error saving task:', error);
            this.cancelTaskEditing(taskElement);
        });
    }

    cancelTaskEditing(taskElement) {
        if (!taskElement) return;
        

        
        // Restore original content (preserve line breaks)
        const originalText = taskElement.dataset.originalText || '';
        const formattedText = originalText.replace(/\n/g, '<br>');
        taskElement.innerHTML = `<p>${formattedText}</p>`;
        taskElement.classList.remove('editing');
        
        // Clean up event listeners
        if (taskElement._editInput) {
            if (taskElement._keydownHandler) {
                taskElement._editInput.removeEventListener('keydown', taskElement._keydownHandler);
            }
            if (taskElement._blurHandler) {
                taskElement._editInput.removeEventListener('blur', taskElement._blurHandler);
            }
            if (taskElement._autoResize) {
                taskElement._editInput.removeEventListener('input', taskElement._autoResize);
            }
        }
        
        // Clean up references
        delete taskElement._keydownHandler;
        delete taskElement._blurHandler;
        delete taskElement._autoResize;
        delete taskElement._editInput;
        delete taskElement.dataset.originalContent;
    }

    closeAllTaskEditing() {
        document.querySelectorAll('.task-text-editable.editing').forEach(taskElement => {
            this.cancelTaskEditing(taskElement);
        });
    }

    // Row editing methods
    startRowEditing(rowHeader) {
        if (!rowHeader) return;
        
        // Close any other editing and clear task selections
        this.closeAllTaskEditing();
        this.closeAllRowEditing();
        this.closeAllColumnEditing();
        this.clearAllTaskSelections();
        
        const rowText = rowHeader.textContent.trim();
        const rowId = rowHeader.dataset.rowId;
        
        // Store original content
        rowHeader.dataset.originalText = rowText;
        
        // Create editing input
        const editInput = document.createElement('input');
        editInput.type = 'text';
        editInput.className = 'w-full px-2 py-1 text-base font-bold rounded bg-white text-gray-800 focus:outline-none';
        editInput.style.border = '2px dotted #f97316';
        editInput.style.fontSize = 'inherit';
        editInput.style.lineHeight = 'inherit';
        editInput.style.fontFamily = 'inherit';
        editInput.style.fontWeight = 'inherit';
        editInput.value = rowText;
        editInput.maxLength = 100;
        
        // Replace content
        rowHeader.innerHTML = '';
        rowHeader.appendChild(editInput);
        rowHeader.classList.add('editing');
        
        // Show the delete button for this row
        const rowContainer = rowHeader.closest('.bg-white');
        if (rowContainer) {
            const deleteBtn = rowContainer.querySelector('.delete-row-btn');
            if (deleteBtn) {
                deleteBtn.style.cssText = `
                    display: inline-flex !important;
                    opacity: 1 !important;
                    visibility: visible !important;
                    pointer-events: auto !important;
                `;
                console.log('Delete button shown for row:', rowText);
        } else {
                console.log('Delete button not found in row container');
            }
        } else {
            console.log('Row container not found');
        }
        
        // Focus and select
        editInput.focus();
        editInput.select();
        
        // Event listeners
        const handleKeydown = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.saveRowEditing(rowHeader);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                this.cancelRowEditing(rowHeader);
            }
        };
        
        const handleBlur = () => {
            setTimeout(() => this.saveRowEditing(rowHeader), 100);
        };
        
        editInput.addEventListener('keydown', handleKeydown);
        editInput.addEventListener('blur', handleBlur);
        
        // Store references
        rowHeader._keydownHandler = handleKeydown;
        rowHeader._blurHandler = handleBlur;
        rowHeader._editInput = editInput;
    }

    saveRowEditing(rowHeader) {
        if (!rowHeader || !rowHeader._editInput) return;
        
        const input = rowHeader._editInput;
        const newText = input.value.trim();
        const rowId = rowHeader.dataset.rowId;
        
        if (!newText) {
            this.cancelRowEditing(rowHeader);
            return;
        }
        
        if (newText === rowHeader.dataset.originalText) {
            this.cancelRowEditing(rowHeader);
            return;
        }
        
        // Get project ID for the URL
        const projectId = this.getProjectId();
        if (!projectId) {
            console.error('Could not determine project ID');
            this.cancelRowEditing(rowHeader);
            return;
        }
        
        // Send update to server
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
                // Update the current row header
                rowHeader.innerHTML = newText;
                rowHeader.classList.remove('editing');
                rowHeader.dataset.originalText = newText;
                
                // Update all row headers with the same row ID across all columns
                const rowId = rowHeader.dataset.rowId;
                document.querySelectorAll(`h3[data-row-id="${rowId}"]`).forEach(otherRowHeader => {
                    if (otherRowHeader !== rowHeader) {
                        otherRowHeader.innerHTML = newText;
                        otherRowHeader.dataset.originalText = newText;
                    }
                });
                
                // Clean up and hide delete button
                this.cleanupRowEditing(rowHeader);
                this.hideRowDeleteButton(rowHeader);
        } else {
                console.error('Failed to save row:', data.errors || data.error || 'Unknown error');
                this.cancelRowEditing(rowHeader);
            }
        })
        .catch(error => {
            console.error('Error saving row:', error);
            this.cancelRowEditing(rowHeader);
        });
    }

    cancelRowEditing(rowHeader) {
        if (!rowHeader) return;
        
        const originalText = rowHeader.dataset.originalText || '';
        rowHeader.innerHTML = originalText;
        rowHeader.classList.remove('editing');
        
        this.cleanupRowEditing(rowHeader);
        this.hideRowDeleteButton(rowHeader);
    }

    cleanupRowEditing(rowHeader) {
        if (rowHeader._editInput) {
            if (rowHeader._keydownHandler) {
                rowHeader._editInput.removeEventListener('keydown', rowHeader._keydownHandler);
            }
            if (rowHeader._blurHandler) {
                rowHeader._editInput.removeEventListener('blur', rowHeader._blurHandler);
            }
        }
        
        delete rowHeader._keydownHandler;
        delete rowHeader._blurHandler;
        delete rowHeader._editInput;
        delete rowHeader.dataset.originalText;
    }

    closeAllRowEditing() {
        document.querySelectorAll('h3[data-row-id].editing').forEach(rowHeader => {
            this.cancelRowEditing(rowHeader);
        });
    }

    hideRowDeleteButton(rowHeader) {
        const rowContainer = rowHeader.closest('.bg-white');
        if (rowContainer) {
            const deleteBtn = rowContainer.querySelector('.delete-row-btn');
            if (deleteBtn) {
                deleteBtn.style.cssText = `
                    display: none !important;
                    opacity: 0 !important;
                    visibility: hidden !important;
                    pointer-events: none !important;
                `;
            }
        }
    }

    // Column editing methods
    startColumnEditing(columnHeader) {
        if (!columnHeader) return;
        
        // Close any other editing and clear task selections
        this.closeAllTaskEditing();
        this.closeAllRowEditing();
        this.closeAllColumnEditing();
        this.clearAllTaskSelections();
        
        const columnText = columnHeader.textContent.trim();
        const currentColumn = this.elements.columns[this.state.currentCol];
        const columnId = currentColumn ? currentColumn.dataset.columnId : null;
        
        if (!columnId) {
            console.error('Could not determine column ID');
            return;
        }
        
        // Store original content
        columnHeader.dataset.originalText = columnText;
        columnHeader.dataset.columnId = columnId;
        
        // Create editing input
        const editInput = document.createElement('input');
        editInput.type = 'text';
        editInput.className = 'w-full px-2 py-1 text-lg font-bold rounded bg-white text-gray-800 focus:outline-none text-center';
        editInput.style.border = '2px dotted #f97316';
        editInput.style.fontSize = 'inherit';
        editInput.style.lineHeight = 'inherit';
        editInput.style.fontFamily = 'inherit';
        editInput.style.fontWeight = 'inherit';
        editInput.value = columnText;
        editInput.maxLength = 100;
        
        // Replace content
        columnHeader.innerHTML = '';
        columnHeader.appendChild(editInput);
        columnHeader.classList.add('editing');
        
        // Show the delete button for this column
        this.showColumnDeleteButton();
        
        // Focus and select
        editInput.focus();
        editInput.select();
        
        // Event listeners
        const handleKeydown = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.saveColumnEditing(columnHeader);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                this.cancelColumnEditing(columnHeader);
            }
        };
        
        const handleBlur = () => {
            setTimeout(() => this.saveColumnEditing(columnHeader), 100);
        };
        
        editInput.addEventListener('keydown', handleKeydown);
        editInput.addEventListener('blur', handleBlur);
        
        // Store references
        columnHeader._keydownHandler = handleKeydown;
        columnHeader._blurHandler = handleBlur;
        columnHeader._editInput = editInput;
    }

    saveColumnEditing(columnHeader) {
        if (!columnHeader || !columnHeader._editInput) return;
        
        const input = columnHeader._editInput;
        const newText = input.value.trim();
        const columnId = columnHeader.dataset.columnId;
        
        if (!newText) {
            this.cancelColumnEditing(columnHeader);
            return;
        }
        
        if (newText === columnHeader.dataset.originalText) {
            this.cancelColumnEditing(columnHeader);
            return;
        }
        
        // Get project ID for the URL
        const projectId = this.getProjectId();
        if (!projectId) {
            console.error('Could not determine project ID');
            this.cancelColumnEditing(columnHeader);
            return;
        }
        
        // Send update to server
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
                // Update the column header
                columnHeader.innerHTML = newText;
                columnHeader.classList.remove('editing');
                columnHeader.dataset.originalText = newText;
                columnHeader.dataset.columnName = newText;
                
                // Update the current column's data attribute
                const currentColumn = this.elements.columns[this.state.currentCol];
                if (currentColumn) {
                    currentColumn.dataset.columnName = newText;
                }
                
                // Clean up and hide delete button
                this.cleanupColumnEditing(columnHeader);
                this.hideColumnDeleteButton();
            } else {
                console.error('Failed to save column:', data.errors || data.error || 'Unknown error');
                this.cancelColumnEditing(columnHeader);
            }
        })
        .catch(error => {
            console.error('Error saving column:', error);
            this.cancelColumnEditing(columnHeader);
        });
    }

    cancelColumnEditing(columnHeader) {
        if (!columnHeader) return;
        
        const originalText = columnHeader.dataset.originalText || '';
        columnHeader.innerHTML = originalText;
        columnHeader.classList.remove('editing');
        
        this.cleanupColumnEditing(columnHeader);
        this.hideColumnDeleteButton();
    }

    cleanupColumnEditing(columnHeader) {
        if (columnHeader._editInput) {
            if (columnHeader._keydownHandler) {
                columnHeader._editInput.removeEventListener('keydown', columnHeader._keydownHandler);
            }
            if (columnHeader._blurHandler) {
                columnHeader._editInput.removeEventListener('blur', columnHeader._blurHandler);
            }
        }
        
        delete columnHeader._keydownHandler;
        delete columnHeader._blurHandler;
        delete columnHeader._editInput;
        delete columnHeader.dataset.originalText;
        delete columnHeader.dataset.columnId;
    }

    closeAllColumnEditing() {
        document.querySelectorAll('#mobile-column-header h2.editing').forEach(columnHeader => {
            this.cancelColumnEditing(columnHeader);
        });
    }

    showColumnDeleteButton() {
        const deleteBtn = document.querySelector('.delete-column-btn');
        if (deleteBtn) {
            deleteBtn.style.display = 'inline-flex';
            deleteBtn.style.opacity = '1';
            deleteBtn.style.visibility = 'visible';
            deleteBtn.style.pointerEvents = 'auto';
            
            // Update the button's data attributes for the current column
            const currentColumn = this.elements.columns[this.state.currentCol];
            if (currentColumn) {
                deleteBtn.dataset.columnId = currentColumn.dataset.columnId;
                deleteBtn.dataset.columnName = currentColumn.dataset.columnName;
                deleteBtn.dataset.deleteUrl = currentColumn.dataset.deleteUrl;
            }
        }
    }

    hideColumnDeleteButton() {
        const deleteBtn = document.querySelector('.delete-column-btn');
        if (deleteBtn) {
            deleteBtn.style.display = 'none';
            deleteBtn.style.opacity = '0';
            deleteBtn.style.visibility = 'hidden';
            deleteBtn.style.pointerEvents = 'none';
        }
    }
    
    hideTaskActionButtons() {
        // Hide all edit and delete buttons by default on mobile
        document.querySelectorAll('.edit-task-btn, .delete-task-btn').forEach(button => {
            button.style.display = 'none';
            button.style.visibility = 'hidden';
            button.style.opacity = '0';
            button.style.pointerEvents = 'none';
        });
        
        // Also remove any edit button click handlers to prevent edit modal from opening
        document.querySelectorAll('.edit-task-btn').forEach(button => {
            button.removeEventListener('click', this.handleEditButtonClick);
            button.addEventListener('click', this.handleEditButtonClick);
        });
    }
    
    handleEditButtonClick(e) {
        // Prevent edit modal from opening on mobile
        e.preventDefault();
        e.stopPropagation();
        return false;
    }
    
    removeEditButtons() {
        // Completely remove all edit buttons from the DOM on mobile
        document.querySelectorAll('.edit-task-btn').forEach(button => {
            button.remove();
        });
        
        // Also remove any edit buttons that might be added later
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const editButtons = node.querySelectorAll ? node.querySelectorAll('.edit-task-btn') : [];
                        editButtons.forEach(button => button.remove());
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
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
                // Check if this was a column deletion
                if (this.state.currentColumnId) {
                    // Hide the delete modal
                    this.hideDeleteModal();
                    // Refresh the page for column deletion
                    window.location.reload();
                    return;
                }
                
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
        
        // Re-hide task action buttons after content changes
        this.hideTaskActionButtons();
        
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
        
        // Re-hide task action buttons after content changes
        this.hideTaskActionButtons();
        
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
        
        // Initialize Save Template Modal functionality
        this.initializeSaveTemplateModal();
        
                // Initialize inline task editing
        this.initializeInlineTaskEditing();
        
        // Completely remove edit buttons on mobile
        this.removeEditButtons();
        
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

        // Initialize Grid Actions Dropdown
        this.initializeGridActionsDropdown();

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
    
    initializeSaveTemplateModal() {
        const withTasksBtn = document.getElementById('with-tasks-btn');
        const structureOnlyBtn = document.getElementById('structure-only-btn');
        const templateStyleInput = document.getElementById('template_style');
        
        if (withTasksBtn && structureOnlyBtn && templateStyleInput) {
            // Set initial state to "Save with clean structure"
            const structureCircle = structureOnlyBtn.querySelector('.w-3.h-3');
            if (structureCircle) structureCircle.classList.remove('opacity-0');
            
            // Handle "Save with example tasks" selection
            withTasksBtn.addEventListener('click', () => {
                const withTasksCircle = withTasksBtn.querySelector('.w-3.h-3');
                const structureCircle = structureOnlyBtn.querySelector('.w-3.h-3');
                
                if (withTasksCircle) withTasksCircle.classList.remove('opacity-0');
                if (structureCircle) structureCircle.classList.add('opacity-0');
                
                templateStyleInput.value = 'with_tasks';
            });
            
            // Handle "Save with clean structure" selection
            structureOnlyBtn.addEventListener('click', () => {
                const withTasksCircle = withTasksBtn.querySelector('.w-3.h-3');
                const structureCircle = structureOnlyBtn.querySelector('.w-3.h-3');
                
                if (withTasksCircle) withTasksCircle.classList.add('opacity-0');
                if (structureCircle) structureCircle.classList.remove('opacity-0');
                
                templateStyleInput.value = 'structure_only';
            });
        }
    }
    
    initializeInlineTaskEditing() {
        // Add click event listeners to all task text elements
        document.addEventListener('click', (e) => {
            const taskText = e.target.closest('.task-text-editable');
            if (taskText && !taskText.classList.contains('editing')) {
                e.preventDefault();
                this.startTaskEditing(taskText);
            }
        });
        
        // Ensure all task elements have the necessary data attributes
        document.querySelectorAll('.task-text-editable').forEach(taskElement => {
            if (!taskElement.dataset.taskText) {
                taskElement.dataset.taskText = taskElement.textContent.trim();
            }
        });
        
        // Hide edit buttons and delete buttons by default on mobile
        this.hideTaskActionButtons();
        
        // Add mobile-specific styling for inline editing
        const style = document.createElement('style');
        style.textContent = `
            .task-text-editable.editing {
                background-color: var(--container-bg) !important;
                border: 2px dashed var(--tertiary-action-bg) !important;
                border-radius: 6px !important;
                padding: 4px 8px !important;
                outline: none !important;
                min-height: 24px !important;
                box-shadow: 0 0 0 3px var(--tertiary-action-bg) / 0.1 !important;
                position: relative !important;
            }
            
            .task-text-editable.editing:focus {
                box-shadow: 0 0 0 3px var(--tertiary-action-bg) / 0.2 !important;
                border-color: var(--tertiary-action-bg) !important;
            }
            
            /* Completely hide edit buttons on mobile */
            .edit-task-btn {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                pointer-events: none !important;
            }
            
            /* Hide delete buttons by default on mobile */
            .task-text-editable .delete-task-btn {
                display: none !important;
            }
            
            /* Show delete button only when editing */
            .task-text-editable.editing .delete-task-btn {
                display: inline-flex !important;
            }
            
            /* Style delete button to match row delete button exactly */
            .task-text-editable.editing .delete-task-btn {
                background-color: transparent !important;
                color: inherit !important;
            }
            
            .task-text-editable.editing .delete-task-btn:hover {
                background-color: var(--grid-header-bg) !important;
            }
            
            .task-text-editable.editing .delete-task-btn i {
                color: #9ca3af !important; /* text-gray-400 */
            }
            
            .task-text-editable.editing .delete-task-btn:hover i {
                color: var(--delete-button-bg) !important;
            }
            
            /* Ensure the task element maintains its position when editing */
            .task-text-editable.editing {
                background-color: transparent !important;
                border: none !important;
                border-radius: 0 !important;
                padding: 0 !important;
                box-shadow: none !important;
                position: relative !important;
                display: block !important;
                min-height: 24px !important;
                transition: all 0.2s ease !important;
            }
            
            /* Ensure the editing interface doesn't shift the layout */
            .task-text-editable.editing > div {
                position: relative !important;
                width: 100% !important;
                transition: all 0.2s ease !important;
            }
            
            /* Prevent layout jumping */
            .task-text-editable {
                transition: all 0.2s ease !important;
                min-height: 24px !important;
            }
            
            /* Force wide editing interface */
            .task-text-editable.editing {
                width: 100% !important;
                min-width: 100% !important;
                max-width: 100% !important;
            }
            
            .task-text-editable.editing > div {
                width: 100% !important;
                min-width: 100% !important;
                max-width: 100% !important;
            }
            
            .task-text-editable.editing input {
                width: 100% !important;
                min-width: 100% !important;
                max-width: 100% !important;
                font-size: inherit !important;
                line-height: inherit !important;
                font-family: inherit !important;
                font-weight: inherit !important;
                background: transparent !important;
                border: 2px dashed var(--tertiary-action-bg) !important;
                border-radius: 6px !important;
                padding: 4px 8px !important;
            }
            
            /* Ensure the existing delete button in the task container remains visible during editing */
            .task-text-editable.editing ~ .mobile-task-actions .delete-task-btn,
            .task-text-editable.editing ~ .desktop-task-actions .delete-task-btn {
                display: inline-flex !important;
                opacity: 1 !important;
                visibility: visible !important;
            }
        `;
        document.head.appendChild(style);
    }

    initializeGridActionsDropdown() {
        const dropdownBtn = document.getElementById('grid-actions-dropdown-btn');
        const dropdown = document.getElementById('grid-actions-dropdown');
        
        if (dropdownBtn && dropdown) {
            // Toggle dropdown on button click
            dropdownBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleGridActionsDropdown();
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!dropdown.contains(e.target) && !dropdownBtn.contains(e.target)) {
                    this.closeGridActionsDropdown();
                }
            });
            
            // Close dropdown on escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.closeGridActionsDropdown();
                }
            });
        }
    }
    
    toggleGridActionsDropdown() {
        const dropdown = document.getElementById('grid-actions-dropdown');
        if (dropdown) {
            const isOpen = !dropdown.classList.contains('opacity-0');
            if (isOpen) {
                this.closeGridActionsDropdown();
            } else {
                this.openGridActionsDropdown();
            }
        }
    }
    
    openGridActionsDropdown() {
        const dropdown = document.getElementById('grid-actions-dropdown');
        if (dropdown) {
            dropdown.classList.remove('opacity-0', 'invisible', 'scale-95');
            dropdown.classList.add('opacity-100', 'visible', 'scale-100');
        }
    }
    
    closeGridActionsDropdown() {
        const dropdown = document.getElementById('grid-actions-dropdown');
        if (dropdown) {
            dropdown.classList.add('opacity-0', 'invisible', 'scale-95');
            dropdown.classList.remove('opacity-100', 'visible', 'scale-100');
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

// Global function to hide save template modal - called from inline onclick handlers
window.hideSaveTemplateModal = function() {
    if (window.mobileGridManager) {
        window.mobileGridManager.hideSaveTemplateModal();
    }
};

// Global function to close grid actions dropdown - called from inline onclick handlers
window.closeGridActionsDropdown = function() {
    if (window.mobileGridManager) {
        window.mobileGridManager.closeGridActionsDropdown();
    }
};


window.addEventListener('beforeunload', function() {
    if (window.mobileGridManager) {
        window.mobileGridManager.cleanup();
    }
});