// Mobile Grid JavaScript
class MobileGridManager {
    constructor() {
        this.state = {
            currentColumn: 0,
            totalColumns: 0,
            columnHeaders: [],
            touchStartX: 0,
            touchStartY: 0,
            touchEndX: 0,
            touchEndY: 0,
            isSwipeable: false,
            swipeThreshold: 50,
            isProjectSwitcherOpen: false,
            isActionsDropdownOpen: false,
            currentTaskId: null,
            currentDeleteUrl: null
        };
        
        this.elements = {};
        this.init();
    }

    // Cache DOM elements
    cacheElements() {
        this.elements = {
            // Mobile grid elements
            mobileGrid: document.getElementById('mobile-grid'),
            mobileColumnContent: document.getElementById('mobile-column-content'),
            mobileCurrentColumn: document.getElementById('mobile-current-column'),
            mobileTotalColumns: document.getElementById('mobile-total-columns'),
            mobileColumnTitle: document.getElementById('mobile-column-title'),
            mobileColumnEditBtn: document.getElementById('mobile-column-edit-btn'),
            mobileColumnDeleteBtn: document.getElementById('mobile-column-delete-btn'),
            mobilePrevBtn: document.getElementById('mobile-prev-btn'),
            mobileNextBtn: document.getElementById('mobile-next-btn'),
            
            // Project switcher
            mobileSwitcherBtn: document.getElementById('mobile-project-switcher-btn'),
            mobileSwitcherDropdown: document.getElementById('mobile-project-switcher-dropdown'),
            mobileSwitcherChevron: document.getElementById('mobile-switcher-chevron'),
            
            // Actions dropdown
            mobileActionsBtn: document.getElementById('mobile-actions-btn'),
            mobileActionsDropdown: document.getElementById('mobile-actions-dropdown'),
            mobileActionsChevron: document.getElementById('mobile-actions-chevron'),
            
            // Modals
            deleteModal: document.getElementById('delete-task-modal'),
            deleteModalContent: document.getElementById('delete-modal-content'),
            taskToDelete: document.getElementById('task-to-delete'),
            deleteTaskForm: document.getElementById('delete-task-form'),
            closeDeleteModal: document.getElementById('close-delete-modal'),
            cancelDeleteTask: document.getElementById('cancel-delete-task'),
            modal: document.getElementById('modal'),
            modalContent: document.getElementById('modal-content')
        };
    }

    // Initialize mobile columns
    initializeMobileColumns() {
        const columnPanels = document.querySelectorAll('.mobile-column-panel');
        
        this.state.columnHeaders = Array.from(columnPanels).map((panel, index) => {
            const columnId = panel.dataset.columnId;
            
            // Get column name from the panel or use fallback
            let name = 'Column ' + (index + 1);
            const headerElement = panel.querySelector('.mobile-column-title');
            if (headerElement) {
                name = headerElement.textContent || name;
            }
            
            return {
                id: columnId,
                element: panel,
                name: name
            };
        });
        
        this.state.totalColumns = this.state.columnHeaders.length;
        this.updateMobileColumnDisplay();
    }

    // Update mobile column display
    updateMobileColumnDisplay() {
        // Hide all columns
        this.state.columnHeaders.forEach(header => {
            header.element.style.display = 'none';
        });
        
        // Show current column
        if (this.state.columnHeaders[this.state.currentColumn]) {
            this.state.columnHeaders[this.state.currentColumn].element.style.display = 'block';
        }
        
        // Update indicators
        if (this.elements.mobileCurrentColumn) {
            this.elements.mobileCurrentColumn.textContent = this.state.currentColumn + 1;
        }
        if (this.elements.mobileTotalColumns) {
            this.elements.mobileTotalColumns.textContent = this.state.totalColumns;
        }
        
        // Update navigation buttons
        if (this.elements.mobilePrevBtn) {
            this.elements.mobilePrevBtn.disabled = this.state.currentColumn === 0;
        }
        if (this.elements.mobileNextBtn) {
            this.elements.mobileNextBtn.disabled = this.state.currentColumn >= this.state.totalColumns - 1;
        }
        
        this.updateMobileColumnHeader();
    }

    // Update mobile column header
    updateMobileColumnHeader() {
        const currentHeader = this.state.columnHeaders[this.state.currentColumn];
        if (currentHeader) {
            if (this.elements.mobileColumnTitle) {
                this.elements.mobileColumnTitle.textContent = currentHeader.name;
            }
            if (this.elements.mobileColumnEditBtn) {
                this.elements.mobileColumnEditBtn.dataset.columnId = currentHeader.id;
            }
            if (this.elements.mobileColumnDeleteBtn) {
                this.elements.mobileColumnDeleteBtn.dataset.columnId = currentHeader.id;
            }
        }
    }

    // Navigation methods
    moveToPreviousColumn() {
        if (this.state.currentColumn > 0) {
            this.state.currentColumn--;
            this.updateMobileColumnDisplay();
        }
    }

    moveToNextColumn() {
        if (this.state.currentColumn < this.state.totalColumns - 1) {
            this.state.currentColumn++;
            this.updateMobileColumnDisplay();
        }
    }

    // Touch event handlers
    handleTouchStart(e) {
        this.state.touchStartX = e.touches[0].clientX;
        this.state.touchStartY = e.touches[0].clientY;
        this.state.isSwipeable = true;
    }

    handleTouchMove(e) {
        if (!this.state.isSwipeable) return;
        
        const touchX = e.touches[0].clientX;
        const touchY = e.touches[0].clientY;
        
        const deltaX = Math.abs(touchX - this.state.touchStartX);
        const deltaY = Math.abs(touchY - this.state.touchStartY);
        
        // If vertical scrolling, disable swipe
        if (deltaY > deltaX) {
            this.state.isSwipeable = false;
        }
        
        // Prevent default if horizontal swipe
        if (deltaX > deltaY && deltaX > 10) {
            e.preventDefault();
        }
    }

    handleTouchEnd(e) {
        if (!this.state.isSwipeable) return;
        
        this.state.touchEndX = e.changedTouches[0].clientX;
        this.state.touchEndY = e.changedTouches[0].clientY;
        
        const deltaX = this.state.touchEndX - this.state.touchStartX;
        const deltaY = Math.abs(this.state.touchEndY - this.state.touchStartY);
        
        // Check if it's a horizontal swipe
        if (Math.abs(deltaX) > this.state.swipeThreshold && Math.abs(deltaX) > deltaY) {
            if (deltaX > 0) {
                // Swipe right - previous column
                this.moveToPreviousColumn();
            } else {
                // Swipe left - next column
                this.moveToNextColumn();
            }
        }
        
        this.state.isSwipeable = false;
    }

    // Project switcher methods
    toggleProjectSwitcher() {
        this.state.isProjectSwitcherOpen = !this.state.isProjectSwitcherOpen;
        this.updateProjectSwitcherUI();
    }

    closeProjectSwitcher() {
        if (this.state.isProjectSwitcherOpen) {
            this.state.isProjectSwitcherOpen = false;
            this.updateProjectSwitcherUI();
        }
    }

    updateProjectSwitcherUI() {
        const { mobileSwitcherDropdown, mobileSwitcherChevron } = this.elements;
        if (!mobileSwitcherDropdown) return;

        const classes = this.state.isProjectSwitcherOpen 
            ? { remove: ['opacity-0', 'invisible', 'scale-95'], add: ['opacity-100', 'visible', 'scale-100'] }
            : { remove: ['opacity-100', 'visible', 'scale-100'], add: ['opacity-0', 'invisible', 'scale-95'] };

        mobileSwitcherDropdown.classList.remove(...classes.remove);
        mobileSwitcherDropdown.classList.add(...classes.add);
        
        if (mobileSwitcherChevron) {
            mobileSwitcherChevron.style.transform = this.state.isProjectSwitcherOpen ? 'rotate(180deg)' : 'rotate(0deg)';
        }
    }

    // Actions dropdown methods
    toggleActionsDropdown() {
        this.state.isActionsDropdownOpen = !this.state.isActionsDropdownOpen;
        this.updateActionsDropdownUI();
    }

    closeActionsDropdown() {
        if (this.state.isActionsDropdownOpen) {
            this.state.isActionsDropdownOpen = false;
            this.updateActionsDropdownUI();
        }
    }

    updateActionsDropdownUI() {
        const { mobileActionsDropdown, mobileActionsChevron } = this.elements;
        if (!mobileActionsDropdown) return;

        const classes = this.state.isActionsDropdownOpen 
            ? { remove: ['opacity-0', 'invisible', 'scale-95'], add: ['opacity-100', 'visible', 'scale-100'] }
            : { remove: ['opacity-100', 'visible', 'scale-100'], add: ['opacity-0', 'invisible', 'scale-95'] };

        mobileActionsDropdown.classList.remove(...classes.remove);
        mobileActionsDropdown.classList.add(...classes.add);
        
        if (mobileActionsChevron) {
            mobileActionsChevron.style.transform = this.state.isActionsDropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)';
        }
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
            this.elements.deleteTaskForm.setAttribute('hx-post', deleteUrl);
            
            if (typeof htmx !== 'undefined') {
                htmx.process(this.elements.deleteTaskForm);
            }
        }
        
        this.setModalState(this.elements.deleteModal, this.elements.deleteModalContent, true);
        
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

    // Event handlers
    handleDocumentClick(e) {
        // Project switcher
        if (e.target.closest('#mobile-project-switcher-btn')) {
            e.stopPropagation();
            this.toggleProjectSwitcher();
            return;
        }
        if (!e.target.closest('#mobile-project-switcher-container')) {
            this.closeProjectSwitcher();
        }

        // Actions dropdown
        if (e.target.closest('#mobile-actions-btn')) {
            e.stopPropagation();
            this.toggleActionsDropdown();
            return;
        }
        if (!e.target.closest('#mobile-actions-container')) {
            this.closeActionsDropdown();
        }

        // Mobile row action buttons
        if (e.target.closest('.mobile-row-action-btn')) {
            e.preventDefault();
            e.stopPropagation();
            this.handleMobileRowAction(e);
            return;
        }

        // Mobile column action buttons
        if (e.target.closest('#mobile-column-edit-btn')) {
            e.preventDefault();
            e.stopPropagation();
            this.handleMobileColumnEdit(e);
            return;
        }
        if (e.target.closest('#mobile-column-delete-btn')) {
            e.preventDefault();
            e.stopPropagation();
            this.handleMobileColumnDelete(e);
            return;
        }

        // Task deletion
        const deleteBtn = e.target.closest('.delete-task-btn');
        if (deleteBtn) {
            e.preventDefault();
            this.showDeleteModal(
                deleteBtn.dataset.taskId,
                deleteBtn.dataset.taskText,
                deleteBtn.dataset.deleteUrl
            );
            return;
        }

        // Modal close buttons
        const closeModalBtn = e.target.closest('.close-modal, #close-delete-modal, #cancel-delete-task');
        if (closeModalBtn) {
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

        // Close mobile row dropdowns when clicking outside
        if (!e.target.closest('.mobile-row-actions')) {
            document.querySelectorAll('.mobile-row-actions-dropdown').forEach(dropdown => {
                dropdown.classList.remove('active');
            });
        }
    }

    handleMobileRowAction(e) {
        const btn = e.target.closest('.mobile-row-action-btn');
        if (!btn) return;

        const rowId = btn.dataset.rowId;
        const dropdown = document.querySelector(`.mobile-row-actions-dropdown[data-row-id="${rowId}"]`);
        
        if (dropdown) {
            // Close all other dropdowns
            document.querySelectorAll('.mobile-row-actions-dropdown').forEach(d => {
                if (d !== dropdown) {
                    d.classList.remove('active');
                }
            });
            
            // Toggle current dropdown
            dropdown.classList.toggle('active');
            
            // Close dropdown when clicking outside
            const clickOutsideHandler = (event) => {
                if (!event.target.closest('.mobile-row-actions')) {
                    dropdown.classList.remove('active');
                    document.removeEventListener('click', clickOutsideHandler);
                }
            };
            
            if (dropdown.classList.contains('active')) {
                setTimeout(() => document.addEventListener('click', clickOutsideHandler), 0);
            }
        }
    }

    handleMobileColumnEdit(e) {
        const btn = e.target.closest('#mobile-column-edit-btn');
        if (!btn) return;

        const columnId = btn.dataset.columnId;
        if (columnId) {
            // Trigger the edit modal
            const editUrl = `/projects/${this.getProjectId()}/columns/${columnId}/edit/`;
            if (typeof htmx !== 'undefined') {
                htmx.ajax('GET', editUrl, '#modal-content');
                this.showModal();
            }
        }
    }

    handleMobileColumnDelete(e) {
        const btn = e.target.closest('#mobile-column-delete-btn');
        if (!btn) return;

        const columnId = btn.dataset.columnId;
        if (columnId) {
            // Trigger the delete modal
            const deleteUrl = `/projects/${this.getProjectId()}/columns/${columnId}/delete/`;
            if (typeof htmx !== 'undefined') {
                htmx.ajax('GET', deleteUrl, '#modal-content');
                this.showModal();
            }
        }
    }

    getProjectId() {
        const path = window.location.pathname;
        const match = path.match(/\/projects\/(\d+)\//);
        return match ? match[1] : null;
    }

    handleKeydown(e) {
        if (e.key === 'Escape') {
            this.closeProjectSwitcher();
            this.closeActionsDropdown();
            this.hideDeleteModal();
            this.hideModal();
            this.collapseAllAddTaskForms();
        }
    }

    // Add event listeners
    addEventListeners() {
        // Navigation buttons
        if (this.elements.mobilePrevBtn) {
            this.elements.mobilePrevBtn.addEventListener('click', () => this.moveToPreviousColumn());
        }
        if (this.elements.mobileNextBtn) {
            this.elements.mobileNextBtn.addEventListener('click', () => this.moveToNextColumn());
        }

        // Touch events for swipe navigation
        if (this.elements.mobileColumnContent) {
            this.elements.mobileColumnContent.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
            this.elements.mobileColumnContent.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
            this.elements.mobileColumnContent.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: false });
        }

        // Document-level events
        document.addEventListener('click', (e) => this.handleDocumentClick(e));
        document.addEventListener('keydown', (e) => this.handleKeydown(e));

        // HTMX events
        document.addEventListener('htmx:afterSwap', (e) => {
            if (e.detail.target.id === 'modal-content') {
                this.showModal();
            }
        });
    }

    // Initialize everything
    init() {
        this.cacheElements();
        this.initializeMobileColumns();
        this.addEventListeners();
    }
}

// Task form validation function
function validateTaskForm(form) {
    const textInput = form.querySelector('input[name="text"]');
    const errorDiv = form.querySelector('.error-message');
    
    if (!textInput.value.trim()) {
        errorDiv.innerHTML = 'Please enter a task description';
        textInput.classList.add('border-red-500');
        textInput.focus();
        return false;
    } else {
        errorDiv.innerHTML = '';
        textInput.classList.remove('border-red-500');
        return true;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.mobileGridManager = new MobileGridManager();
}); 