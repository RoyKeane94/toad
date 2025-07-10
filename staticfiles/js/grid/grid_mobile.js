// Grid JavaScript - Mobile Version
class MobileGridManager {
    constructor() {
        this.state = {
            currentCol: 0,
            totalColumns: 0,
            projectSwitcherOpen: false,
            actionsMenuOpen: false,
            currentTaskId: null,
            currentDeleteUrl: null,
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
            switcherDropdown: '#project-switcher-dropdown',
            switcherChevron: '#switcher-chevron',
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
        const modalTrigger = e.target.closest('[hx-target="#modal-content"]');
        if (modalTrigger) {
            this.clearModalContent();
            this.showModal();
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

        const deleteBtn = e.target.closest('.delete-task-btn');
        if (deleteBtn) {
            e.preventDefault();
            this.showDeleteModal(deleteBtn.dataset.taskId, deleteBtn.dataset.taskText, deleteBtn.dataset.deleteUrl);
            return;
        }

        const closeModalBtn = e.target.closest('.close-modal, #close-delete-modal, #cancel-delete-task');
        if (closeModalBtn) {
            if (closeModalBtn.id === 'close-delete-modal' || closeModalBtn.id === 'cancel-delete-task') this.hideDeleteModal();
            else if (closeModalBtn.classList.contains('close-modal')) this.hideModal();
            return;
        }

        if (e.target === this.elements.deleteModal) this.hideDeleteModal();
        if (e.target === this.elements.modal) this.hideModal();

        const addTaskTrigger = e.target.closest('.add-task-trigger');
        if (addTaskTrigger) { e.preventDefault(); this.expandAddTaskForm(addTaskTrigger.closest('.add-task-form')); return; }
        const addTaskCancel = e.target.closest('.add-task-cancel');
        if (addTaskCancel) { e.preventDefault(); this.collapseAddTaskForm(addTaskCancel.closest('.add-task-form')); return; }
        if (!e.target.closest('.add-task-form')) this.collapseAllAddTaskForms();
    }
    
    // Mobile Grid setup
    setupMobileGrid() {
        if (!this.elements.gridSlider || !this.elements.columns.length) return;

        this.state.totalColumns = this.elements.columns.length;

        if (this.elements.leftBtn) this.elements.leftBtn.onclick = () => this.scrollToCol(this.state.currentCol - 1);
        if (this.elements.rightBtn) this.elements.rightBtn.onclick = () => this.scrollToCol(this.state.currentCol + 1);

        this.scrollToCol(this.state.currentCol, 'auto');
    }

    scrollToCol(colIdx, behavior = 'smooth') {
        this.state.currentCol = Math.max(0, Math.min(colIdx, this.state.totalColumns - 1));
        
        const newTransform = `translateX(-${this.state.currentCol * 100}%)`;
        this.elements.gridSlider.style.transition = behavior === 'smooth' ? 'transform 0.3s ease-in-out' : 'none';
        this.elements.gridSlider.style.transform = newTransform;
        
        this.updateUI();
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

    showModal() { this.setModalState(this.elements.modal, this.elements.modalContent, true); }
    hideModal() { this.setModalState(this.elements.modal, this.elements.modalContent, false); }
    
    clearModalContent() {
        if (this.elements.modalContent) this.elements.modalContent.innerHTML = '';
    }

    setModalState(modal, content, isOpen) {
        if (!modal || !content) return;
    
        // Add a class to the modal for CSS transitions
        modal.classList.toggle('visible', isOpen);

        if (isOpen) {
            modal.classList.remove('opacity-0', 'invisible');
            content.classList.remove('scale-95');
            content.classList.add('scale-100');
        } else {
            modal.classList.add('opacity-0');
            content.classList.add('scale-95');
            setTimeout(() => modal.classList.add('invisible'), 300); // Wait for transition
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
    handleHtmxBeforeRequest(e) {}

    handleHtmxAfterRequest(e) {
        // Handle server-sent triggers
        if (e.detail.successful && e.detail.xhr) {
            const triggerHeader = e.detail.xhr.getResponseHeader('HX-Trigger');
            if (triggerHeader) {
                if (triggerHeader.includes('scrollToEnd')) { this.handleScrollToEnd(); return; }
                if (triggerHeader.includes('refreshGrid')) { this.handleRefreshGrid(); return; }
                if (triggerHeader.includes('resetGridToInitial')) { this.handleResetGridToInitial(); return; }
            }
        }
        
        // Handle successful task deletion
        if (e.detail.successful && e.target.id === 'delete-task-form' && e.detail.requestConfig.verb === 'post') {
            const taskId = this.state.currentTaskId;
            if (taskId) {
                const taskElement = document.getElementById(`task-${taskId}`);
                if (taskElement) {
                    const parentCard = taskElement.closest('.task-list'); // In mobile view, this is the container
                    taskElement.style.transition = 'all 0.3s ease';
                    taskElement.style.opacity = '0';
                    taskElement.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        // Instead of removing the task, we might get new content for an empty task placeholder
                        // We rely on htmx to swap in the new content if provided, or we just need to handle the visual removal
                    }, 300);
                }
            }
            this.hideDeleteModal();
            return;
        }

        // Handle other successful POSTs that might return JSON
        if (e.detail.successful && e.detail.requestConfig.verb === 'post') {
            try {
                const response = JSON.parse(e.detail.xhr.responseText);
                if(response.success) this.hideModal();
            } catch (err) {
                // Not a JSON response, likely HTML swap, which htmx handles
            }
        }
    }
    
    handleHtmxAfterSwap(e) {
        if (e.detail.target.id === 'modal-content') {
            this.showModal();
            const textField = e.detail.target.querySelector('textarea, input[name="text"]');
            if (textField) {
                const handleKeyDown = (evt) => {
                    if (evt.key === 'Enter' && !(textField.tagName.toLowerCase() === 'textarea' && evt.shiftKey)) {
                        evt.preventDefault();
                        const form = textField.closest('form');
                        if (form) (form.querySelector('button[type="submit"]') || form).click();
                    }
                };
                textField.addEventListener('keydown', handleKeyDown);
                setTimeout(() => {
                    textField.focus();
                    textField.setSelectionRange(textField.value.length, textField.value.length);
                }, 150);
            }
        }
        // Re-process htmx for any new content
        if (typeof htmx !== 'undefined') htmx.process(e.detail.target);

        // After a swap, especially for tasks, we might need to re-init
        this.reinitializeComponents();
    }
    
    handleHtmxError(e) {
        if (e.detail.target && e.detail.target.id === 'modal-content') {
            this.elements.modalContent.innerHTML = `<div class="flex items-center justify-center p-8"><div class="flex flex-col items-center space-y-3 text-center"><div class="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center"><i class="fas fa-exclamation-triangle text-red-500 text-xl"></i></div><div><h3 class="text-lg font-medium text-[var(--text-primary)]">Error Loading Content</h3><p class="text-sm text-[var(--text-secondary)] mt-1">Unable to load the requested content. Please try again.</p></div><button type="button" class="close-modal mt-4 px-4 py-2 bg-[var(--primary-action-bg)] hover:bg-[var(--primary-action-hover-bg)] text-white rounded-lg transition-colors">Close</button></div></div>`;
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

        if (typeof htmx !== 'undefined') {
            htmx.config.disableSelector = '[hx-disable]';
            htmx.config.useTemplateFragments = false;
        }
    }
}

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

document.addEventListener('DOMContentLoaded', function() {
    window.mobileGridManager = new MobileGridManager();
});

window.addEventListener('beforeunload', function() {
    if (window.mobileGridManager) {
        window.mobileGridManager.cleanup();
    }
});
