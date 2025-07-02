// Grid JavaScript - Optimized Version
class GridManager {
    constructor() {
        this.state = {
            currentCol: 0,
            dataColWidth: 0,
            totalDataColumns: 0,
            columnsToShow: 3,
            isDropdownOpen: false,
            currentTaskId: null,
            currentDeleteUrl: null
        };
        
        this.elements = {};
        this.observers = new Map();
        this.eventListeners = new Map();
        this.stickyThreshold = 0;
        this.isHeaderSticky = false;
        this.originalHeaderPositions = new Map();
        
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
            dataTable: '.grid-table'
        };

        Object.keys(selectors).forEach(key => {
            const selector = selectors[key];
            if (selector.includes('All') || key.includes('Rows') || key === 'dataCols') {
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
            ['document', 'htmx:afterRequest', this.handleHtmxAfterRequest.bind(this)],
            ['document', 'htmx:afterSwap', this.handleHtmxAfterSwap.bind(this)],
            ['document', 'htmx:afterSettle', this.handleHtmxAfterSettle.bind(this)],
            
            // Body level events
            ['body', 'openModal', this.showModal.bind(this)],
            ['body', 'closeModal', this.hideModal.bind(this)],
            ['body', 'refreshGrid', () => window.location.reload()],
            ['body', 'scrollToEnd', this.handleScrollToEnd.bind(this)]
        ];

        listeners.forEach(([target, event, handler]) => {
            const element = target === 'document' ? document : document.body;
            element.addEventListener(event, handler);
            
            // Store for cleanup
            if (!this.eventListeners.has(element)) {
                this.eventListeners.set(element, []);
            }
            this.eventListeners.get(element).push({ event, handler });
        });

        // Sticky headers are now handled by setupStickyHeaders method
    }

    // Unified click handler to reduce event listeners
    handleDocumentClick(e) {
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

        // Action dropdowns
        const actionBtn = e.target.closest('.column-actions-btn, .row-actions-btn');
        if (actionBtn) {
            e.stopPropagation();
            this.toggleActionDropdown(actionBtn);
            return;
        }

        // Close action dropdowns if clicking outside
        if (!e.target.closest('.column-actions-dropdown, .row-actions-dropdown')) {
            this.closeAllActionDropdowns();
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
    }

    // Unified keyboard handler
    handleKeydown(e) {
        if (e.key === 'Escape') {
            this.closeProjectSwitcher();
            this.closeAllActionDropdowns();
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

    // Action dropdown methods
    toggleActionDropdown(btn) {
        const dropdown = btn.nextElementSibling;
        if (!dropdown) return;

        // Close all other dropdowns first
        this.closeAllActionDropdowns(dropdown);

        // Toggle current dropdown
        const isOpen = !dropdown.classList.contains('opacity-0');
        this.setDropdownState(dropdown, !isOpen);
    }

    closeAllActionDropdowns(except = null) {
        document.querySelectorAll('.column-actions-dropdown, .row-actions-dropdown').forEach(dropdown => {
            if (dropdown !== except) {
                this.setDropdownState(dropdown, false);
            }
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
        
        if (this.elements.taskToDelete) {
            this.elements.taskToDelete.textContent = taskText;
        }
        if (this.elements.deleteTaskForm) {
            this.elements.deleteTaskForm.action = deleteUrl;
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

    // Grid scrolling methods
    setupGridScrolling(skipRestore = false) {
        const { scrollable, leftBtn, rightBtn, gridTable, dataCols } = this.elements;
        if (!scrollable || !leftBtn || !rightBtn || !gridTable || !dataCols.length) return;

        this.state.totalDataColumns = parseInt(gridTable.dataset.totalDataColumns) || 0;
        this.state.columnsToShow = Math.min(3, this.state.totalDataColumns);

        // Setup scroll buttons (only if not already set)
        if (!leftBtn.onclick) {
            leftBtn.onclick = () => this.scrollToCol(this.state.currentCol - 1);
            rightBtn.onclick = () => this.scrollToCol(this.state.currentCol + 1);
        }

        // Setup resize observer (only once)
        if (!this.observers.has('resize')) {
            const resizeObserver = new ResizeObserver(() => {
                const currentScrollLeft = scrollable.scrollLeft;
                this.calculateAndApplyWidths();
                // Restore exact scroll position after resize
                scrollable.scrollLeft = currentScrollLeft;
                this.updateScrollButtons();
            });
            resizeObserver.observe(scrollable);
            this.observers.set('resize', resizeObserver);
        }

        this.calculateAndApplyWidths();
        this.updateScrollButtons();
        
        // Only restore position on initial load or explicit requests
        if (!skipRestore) {
            this.restoreScrollPosition();
        }
    }

    calculateAndApplyWidths() {
        const { scrollable, gridTable, dataCols } = this.elements;
        if (!scrollable || !dataCols.length) return;

        if (this.state.columnsToShow > 0) {
            const containerWidth = scrollable.clientWidth;
            this.state.dataColWidth = containerWidth / this.state.columnsToShow;
            
            dataCols.forEach(col => {
                col.style.width = `${this.state.dataColWidth}px`;
            });

            const totalTableWidth = this.state.dataColWidth * this.state.totalDataColumns;
            gridTable.style.width = `${totalTableWidth}px`;
        }
        
        this.syncRowHeights();
    }

    scrollToCol(colIdx, behavior = 'smooth') {
        const { scrollable } = this.elements;
        if (!scrollable) return;

        this.state.currentCol = Math.max(0, Math.min(colIdx, this.state.totalDataColumns - this.state.columnsToShow));
        const scrollLeft = this.state.currentCol * this.state.dataColWidth;
        scrollable.scrollTo({ left: scrollLeft, behavior });
        this.updateScrollButtons();
    }

    updateScrollButtons() {
        const { leftBtn, rightBtn } = this.elements;
        if (!leftBtn || !rightBtn) return;

        if (this.state.totalDataColumns <= this.state.columnsToShow) {
            leftBtn.disabled = rightBtn.disabled = true;
            leftBtn.style.display = rightBtn.style.display = 'none';
        } else {
            leftBtn.style.display = rightBtn.style.display = 'flex';
            leftBtn.disabled = this.state.currentCol === 0;
            rightBtn.disabled = this.state.currentCol >= this.state.totalDataColumns - this.state.columnsToShow;
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
        
        if (scrollToEnd) {
            sessionStorage.removeItem('scrollToEnd');
            // Use immediate scroll for scroll-to-end, only small delay for DOM stability
            setTimeout(() => {
                const lastColIndex = this.state.totalDataColumns - this.state.columnsToShow;
                this.scrollToCol(lastColIndex, 'auto');
            }, 10);
        } else if (savedPosition) {
            sessionStorage.removeItem('grid-scroll-position');
            // Restore saved position immediately for smoother experience
            const savedScrollLeft = parseFloat(savedPosition);
            if (this.elements.scrollable && savedScrollLeft > 0) {
                this.elements.scrollable.scrollLeft = savedScrollLeft;
                // Update current column state to match restored position
                this.state.currentCol = this.state.dataColWidth > 0 
                    ? Math.round(savedScrollLeft / this.state.dataColWidth) 
                    : 0;
                this.updateScrollButtons();
            }
        } else {
            // Default to start, no delay needed
            this.scrollToCol(0, 'auto');
        }
    }

    handleScrollToEnd() {
        sessionStorage.setItem('scrollToEnd', 'true');
        window.location.reload();
    }

    // Sticky header methods
    setupStickyHeaders() {
        // Calculate the threshold - when the header section scrolls out of view
        const headerSection = document.querySelector('.mb-6');
        if (headerSection) {
            const rect = headerSection.getBoundingClientRect();
            this.stickyThreshold = rect.bottom + window.scrollY;
        }
        
        // Store original positions of headers
        const headers = document.querySelectorAll('.grid-table-fixed th, .grid-table th');
        headers.forEach((header, index) => {
            const rect = header.getBoundingClientRect();
            this.originalHeaderPositions.set(header, {
                top: rect.top + window.scrollY,
                left: rect.left,
                width: rect.width,
                height: rect.height
            });
            
            // Apply base styling
            header.style.backgroundColor = 'var(--container-bg)';
            header.style.borderBottom = '2px solid var(--border-color)';
            header.style.zIndex = '1';
        });
        
        // Add scroll listener
        this.addScrollListener();
    }
    
    addScrollListener() {
        const scrollHandler = () => {
            const scrollY = window.pageYOffset;
            const shouldStick = scrollY > (this.stickyThreshold - 60); // 60px offset for better UX
            
            if (shouldStick && !this.isHeaderSticky) {
                this.makeHeadersSticky();
            } else if (!shouldStick && this.isHeaderSticky) {
                this.makeHeadersNormal();
            }
            
            // Update positions if sticky
            if (this.isHeaderSticky) {
                this.updateStickyPositions();
            }
        };
        
        window.addEventListener('scroll', scrollHandler);
        
        // Also listen for horizontal scroll to update positions
        const horizontalScrollHandler = () => {
            if (this.isHeaderSticky) {
                this.updateStickyPositions();
            }
        };
        
        const scrollableContainer = document.querySelector('.grid-table-scrollable');
        if (scrollableContainer) {
            scrollableContainer.addEventListener('scroll', horizontalScrollHandler);
        }
        
        // Store listeners for cleanup
        if (!this.eventListeners.has(window)) {
            this.eventListeners.set(window, []);
        }
        this.eventListeners.get(window).push({ event: 'scroll', handler: scrollHandler });
        
        if (scrollableContainer) {
            if (!this.eventListeners.has(scrollableContainer)) {
                this.eventListeners.set(scrollableContainer, []);
            }
            this.eventListeners.get(scrollableContainer).push({ event: 'scroll', handler: horizontalScrollHandler });
        }
    }
    
    makeHeadersSticky() {
        this.isHeaderSticky = true;
        
        const headers = document.querySelectorAll('.grid-table-fixed th, .grid-table th');
        headers.forEach(header => {
            const originalPos = this.originalHeaderPositions.get(header);
            if (originalPos) {
                header.style.position = 'fixed';
                header.style.top = '0px';
                header.style.left = originalPos.left + 'px';
                header.style.width = originalPos.width + 'px';
                header.style.height = originalPos.height + 'px';
                header.style.zIndex = '100';
                header.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
            }
        });
    }
    
    makeHeadersNormal() {
        this.isHeaderSticky = false;
        
        const headers = document.querySelectorAll('.grid-table-fixed th, .grid-table th');
        headers.forEach(header => {
            header.style.position = 'static';
            header.style.top = 'auto';
            header.style.left = 'auto';
            header.style.width = 'auto';
            header.style.height = 'auto';
            header.style.zIndex = '1';
            header.style.boxShadow = 'none';
        });
    }
    
    updateStickyPositions() {
        if (!this.isHeaderSticky) return;
        
        // Update positions based on current layout
        const gridWrapper = document.querySelector('.grid-container-wrapper');
        const scrollableContainer = document.querySelector('.grid-table-scrollable');
        
        if (gridWrapper && scrollableContainer) {
            const wrapperRect = gridWrapper.getBoundingClientRect();
            const scrollLeft = scrollableContainer.scrollLeft;
            
            const headers = document.querySelectorAll('.grid-table-fixed th, .grid-table th');
            headers.forEach(header => {
                const isInScrollableArea = header.closest('.grid-table-scrollable');
                
                if (isInScrollableArea) {
                    // For headers in scrollable area, adjust for horizontal scroll
                    const originalPos = this.originalHeaderPositions.get(header);
                    if (originalPos) {
                        header.style.left = (originalPos.left - scrollLeft) + 'px';
                    }
                } else {
                    // For fixed column headers, keep original position
                    const originalPos = this.originalHeaderPositions.get(header);
                    if (originalPos) {
                        header.style.left = wrapperRect.left + 'px';
                    }
                }
            });
        }
    }

    // Sticky headers are now handled purely by CSS

    // Task edit column tracking no longer needed since we update in place

    // HTMX event handlers
    handleHtmxAfterRequest(e) {
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
                console.log('Non-JSON response, reloading page');
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
        
        // Only reinitialize if this is a significant change (modal content or full grid updates)
        const isModalUpdate = e.detail.target && e.detail.target.id === 'modal-content';
        const isGridUpdate = e.detail.target && e.detail.target.closest('#grid-content');
        const isTaskUpdate = e.detail.target && e.detail.target.closest('[id^="task-"]');
        
        if (isModalUpdate) {
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

    reinitializeComponents() {
        // Store current scroll position before reinitializing
        const currentScrollLeft = this.elements.scrollable ? this.elements.scrollable.scrollLeft : 0;
        
        // Reset sticky headers state
        this.isHeaderSticky = false;
        this.originalHeaderPositions.clear();
        
        this.cacheElements();
        // Skip restore during reinit to avoid double scroll position changes
        this.setupGridScrolling(true);
        
        // Reinitialize sticky headers with a small delay to ensure layout is ready
        setTimeout(() => this.setupStickyHeaders(), 50);
        
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
        // Reset sticky headers if active
        if (this.isHeaderSticky) {
            this.makeHeadersNormal();
        }
        this.originalHeaderPositions.clear();
        
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
    }

    // Initialize everything
    init() {
        this.cacheElements();
        this.addEventListeners();
        this.setupGridScrolling();
        
        // Setup sticky headers after a short delay to ensure DOM is ready
        setTimeout(() => this.setupStickyHeaders(), 100);
        
        console.log('Grid JavaScript optimized and loaded');
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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.gridManager = new GridManager();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.gridManager) {
        window.gridManager.cleanup();
    }
}); 