// Grid JavaScript - Optimized Version
class GridManager {
    constructor() {
        // Only initialize on desktop - don't interfere with mobile
        if (window.innerWidth < 769) {
            console.log('GridManager: Skipping initialization on mobile device');
            return;
        }
        
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
                }
            }
        });

        // Sticky headers are not implemented
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

    // Function to close all dropdowns - called from inline onclick handlers
    closeAllDropdowns() {
        this.closeProjectSwitcher();
        this.closeAllActionDropdowns();
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
            leftBtn.onclick = () => this.scrollToCol(this.state.currentCol - 1);
            rightBtn.onclick = () => this.scrollToCol(this.state.currentCol + 1);
            
            // Add touch support for mobile
            leftBtn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.scrollToCol(this.state.currentCol - 1);
            });
            rightBtn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.scrollToCol(this.state.currentCol + 1);
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
            const scrollHandler = () => {
                if (this.state.dataColWidth > 0) {
                    const newCurrentCol = Math.round(scrollable.scrollLeft / this.state.dataColWidth);
                    if (newCurrentCol !== this.state.currentCol) {
                        this.state.currentCol = newCurrentCol;
                        this.updateScrollButtons();
                    }
                }
            };
            
            // Use passive listeners for better performance on mobile
            scrollable.addEventListener('scroll', scrollHandler, { passive: true });
            this.observers.set('scroll', { disconnect: () => scrollable.removeEventListener('scroll', scrollHandler) });
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
        const resetToInitial = sessionStorage.getItem('resetToInitial');
        
        if (resetToInitial) {
            sessionStorage.removeItem('resetToInitial');
            // Force reset to column 0
            this.state.currentCol = 0;
            this.scrollToCol(0, 'auto');
            return;
        } else if (scrollToEnd) {
            sessionStorage.removeItem('scrollToEnd');
            // Wait a bit longer for DOM to be stable and recalculate
            setTimeout(() => {
                // Recalculate total columns from actual DOM
                const dataColumns = document.querySelectorAll('.data-column');
                const actualColumnCount = dataColumns.length;
                
                if (actualColumnCount > 0) {
                    this.state.totalDataColumns = actualColumnCount;
                    // Update the grid table data attribute
                    if (this.elements.gridTable) {
                        this.elements.gridTable.dataset.totalDataColumns = actualColumnCount;
                    }
                    
                    // Recalculate widths
                    this.calculateAndApplyWidths();
                    
                    // Scroll to the last possible position
                    const lastColIndex = Math.max(0, this.state.totalDataColumns - this.state.columnsToShow);
                    this.scrollToCol(lastColIndex, 'smooth');
                } else {
                    this.scrollToCol(0, 'auto');
                }
            }, 200); // Increased timeout
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

    handleScrollToEnd() {
        // For new columns, we need to refresh to get the updated grid structure
        sessionStorage.setItem('scrollToEnd', 'true');
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
            this.elements.scrollable.scrollLeft = 0;
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
        });
    }

    updateRowHeader(rowId, newName) {
        const rowHeaders = document.querySelectorAll(`[data-row-id="${rowId}"]`);
        rowHeaders.forEach(header => {
            const nameElement = header.querySelector('span.font-semibold');
            if (nameElement) {
                nameElement.textContent = newName;
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

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.gridManager) {
        window.gridManager.cleanup();
    }
}); 