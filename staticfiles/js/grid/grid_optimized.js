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
            ['document', 'htmx:beforeRequest', this.handleHtmxBeforeRequest.bind(this)],
            ['document', 'htmx:afterRequest', this.handleHtmxAfterRequest.bind(this)],
            ['document', 'htmx:afterSwap', this.handleHtmxAfterSwap.bind(this)],
            ['document', 'htmx:afterSettle', this.handleHtmxAfterSettle.bind(this)],
            ['document', 'htmx:responseError', this.handleHtmxError.bind(this)],
            ['document', 'htmx:sendError', this.handleHtmxError.bind(this)],
            
            // Body level events
            ['body', 'openModal', this.showModal.bind(this)],
            ['body', 'closeModal', this.hideModal.bind(this)],
            ['body', 'refreshGrid', this.handleRefreshGrid.bind(this)],
            ['body', 'scrollToEnd', this.handleScrollToEnd.bind(this)],
            ['body', 'resetGridToInitial', this.handleResetGridToInitial.bind(this)]
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

        // Add explicit scrollToEnd listener for HTMX triggers
        document.addEventListener('scrollToEnd', (e) => {
            console.log('scrollToEnd event caught!', e);
            this.handleScrollToEnd();
        });

        // Also listen for HTMX trigger events (multiple ways HTMX can trigger events)
        document.addEventListener('htmx:trigger', (e) => {
            console.log('HTMX trigger event:', e.detail);
            if (e.detail.trigger === 'scrollToEnd') {
                console.log('scrollToEnd trigger detected via htmx:trigger!');
                this.handleScrollToEnd();
            }
        });

        // Listen for HTMX header triggers (HX-Trigger header from server)
        document.body.addEventListener('htmx:afterRequest', (e) => {
            if (e.detail.xhr && e.detail.xhr.getResponseHeader('HX-Trigger')) {
                const triggers = e.detail.xhr.getResponseHeader('HX-Trigger');
                console.log('HX-Trigger header found:', triggers);
                if (triggers && triggers.includes('scrollToEnd')) {
                    console.log('scrollToEnd trigger detected via HX-Trigger header!');
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
        const { scrollable, leftBtn, rightBtn, gridTable } = this.elements;
        if (!scrollable || !leftBtn || !rightBtn || !gridTable) return;

        // Always get fresh column count from DOM
        const dataCols = document.querySelectorAll('.data-column');
        this.elements.dataCols = dataCols;
        
        if (!dataCols.length) return;

        this.state.totalDataColumns = parseInt(gridTable.dataset.totalDataColumns) || dataCols.length;
        this.state.columnsToShow = Math.min(3, this.state.totalDataColumns);
        
        console.log('Setup grid scrolling - Total columns:', this.state.totalDataColumns);

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
        const resetToInitial = sessionStorage.getItem('resetToInitial');
        
        if (resetToInitial) {
            console.log('Resetting to initial state');
            sessionStorage.removeItem('resetToInitial');
            // Force reset to column 0
            this.state.currentCol = 0;
            this.scrollToCol(0, 'auto');
            return;
        } else if (scrollToEnd) {
            console.log('Restoring scroll to end position');
            sessionStorage.removeItem('scrollToEnd');
            // Wait a bit longer for DOM to be stable and recalculate
            setTimeout(() => {
                // Recalculate total columns from actual DOM
                const dataColumns = document.querySelectorAll('.data-column');
                const actualColumnCount = dataColumns.length;
                console.log('Actual column count from DOM:', actualColumnCount);
                
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
                    console.log('Scrolling to column index:', lastColIndex);
                    this.scrollToCol(lastColIndex, 'smooth');
                } else {
                    console.log('No data columns found, defaulting to start');
                    this.scrollToCol(0, 'auto');
                }
            }, 100);
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
        console.log('ScrollToEnd triggered');
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

    // Handle column/row header updates
    updateColumnHeader(columnId, newName) {
        console.log(`Updating column ${columnId} to ${newName}`);
        const columnHeaders = document.querySelectorAll(`[data-column-id="${columnId}"]`);
        console.log(`Found ${columnHeaders.length} column headers`);
        columnHeaders.forEach(header => {
            const nameElement = header.querySelector('span.font-semibold');
            console.log('Name element:', nameElement);
            if (nameElement) {
                nameElement.textContent = newName;
                console.log(`Updated column header to: ${newName}`);
            }
        });
    }

    updateRowHeader(rowId, newName) {
        console.log(`Updating row ${rowId} to ${newName}`);
        const rowHeaders = document.querySelectorAll(`[data-row-id="${rowId}"]`);
        console.log(`Found ${rowHeaders.length} row headers`);
        rowHeaders.forEach(header => {
            const nameElement = header.querySelector('span.font-semibold');
            console.log('Name element:', nameElement);
            if (nameElement) {
                nameElement.textContent = newName;
                console.log(`Updated row header to: ${newName}`);
            }
        });
    }

    // No sticky header functionality

    // Task edit column tracking no longer needed since we update in place

    // HTMX event handlers
    handleHtmxBeforeRequest(e) {
        console.log('HTMX Before Request:', e.detail);
        const url = e.detail.requestConfig?.url || 'unknown';
        const method = e.detail.requestConfig?.verb || 'unknown';
        console.log('About to make request:', method, url);
        
        // Check if it's a form submission
        if (e.target.tagName === 'FORM') {
            console.log('Form submission detected:', e.target);
            console.log('Form action:', e.target.action);
            console.log('Form method:', e.target.method);
            console.log('Form data:', new FormData(e.target));
        }
    }

    handleHtmxAfterRequest(e) {
        // Better debugging of the event structure
        console.log('Full HTMX event detail:', e.detail);
        
        const url = e.detail.requestConfig?.url || e.target?.getAttribute('hx-post') || e.target?.getAttribute('hx-get') || 'unknown';
        const method = e.detail.requestConfig?.verb || e.detail.requestConfig?.type || 
                      (e.target?.getAttribute('hx-post') ? 'post' : 
                       e.target?.getAttribute('hx-get') ? 'get' : 'unknown');
        
        console.log('HTMX After Request:', url, 'Method:', method, 'Success:', e.detail.successful);
        console.log('Target element:', e.target);
        console.log('Request config verb:', e.detail.requestConfig?.verb);
        console.log('Request config type:', e.detail.requestConfig?.type);
        console.log('Target hx-post:', e.target?.getAttribute('hx-post'));
        console.log('Target hx-get:', e.target?.getAttribute('hx-get'));
        
        // Check if we have response text
        if (e.detail.xhr && e.detail.xhr.responseText) {
            console.log('Response text length:', e.detail.xhr.responseText.length);
            console.log('Response text preview:', e.detail.xhr.responseText.substring(0, 200));
        }
        
        // Check for HX-Trigger header first (for column creation and row creation)
        if (e.detail.successful && e.detail.xhr) {
            const triggerHeader = e.detail.xhr.getResponseHeader('HX-Trigger');
            if (triggerHeader) {
                console.log('HX-Trigger header found:', triggerHeader);
                if (triggerHeader.includes('scrollToEnd')) {
                    console.log('scrollToEnd trigger detected via HX-Trigger header!');
                    this.handleScrollToEnd();
                    return;
                }
                if (triggerHeader.includes('refreshGrid')) {
                    console.log('refreshGrid trigger detected via HX-Trigger header!');
                    this.handleRefreshGrid();
                    return;
                }
                if (triggerHeader.includes('resetGridToInitial')) {
                    console.log('resetGridToInitial trigger detected via HX-Trigger header!');
                    this.handleResetGridToInitial();
                    return;
                }
            }
        }
        
        // Only handle POST requests for form submissions
        console.log('Checking if this is a POST request...');
        console.log('Method matches post?', method === 'post' || method === 'POST');
        console.log('Has responseText?', !!e.detail.xhr.responseText);
        
        if (e.detail.successful && (method === 'post' || method === 'POST') && e.detail.xhr.responseText) {
            console.log('Processing POST request...');
            // Store scroll position for form submissions
            const gridScrollable = document.querySelector('.grid-table-scrollable');
            const currentScrollLeft = gridScrollable ? gridScrollable.scrollLeft : 0;
            
            try {
                const response = JSON.parse(e.detail.xhr.responseText);
                console.log('Parsed JSON response:', response);
                console.log('Response success:', response.success);
                
                if (response.success) {
                    console.log('Processing successful response...');
                    console.log('URL to check:', url);
                    console.log('URL includes /column/?', url.includes('/column/'));
                    console.log('URL includes /edit/?', url.includes('/edit/'));
                    console.log('URL regex match:', url.match(/\/column\/\d+\/edit\//));
                    
                    // Check if this is a column update
                    if ((url.includes('/columns/') && url.includes('/edit/')) || url.match(/\/columns\/\d+\/edit\//)) {
                        console.log('Column update POST detected!');
                        
                        // Extract column ID from URL
                        let columnId = null;
                        const urlMatch = url.match(/\/columns\/(\d+)\//);
                        console.log('URL match result:', urlMatch);
                        if (urlMatch) {
                            columnId = urlMatch[1];
                        } else {
                            const urlParts = url.split('/');
                            console.log('URL parts:', urlParts);
                            const columnIndex = urlParts.indexOf('columns');
                            console.log('Column index:', columnIndex);
                            if (columnIndex >= 0 && columnIndex + 1 < urlParts.length) {
                                columnId = urlParts[columnIndex + 1];
                            }
                        }
                        console.log('Column ID extracted:', columnId);
                        
                        if (columnId && response.column_name) {
                            // Update column headers in place
                            this.updateColumnHeader(columnId, response.column_name);
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
                        console.log('Row update POST detected!');
                        
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
                        console.log('Row ID extracted:', rowId);
                        
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
                console.log('Response is not JSON (likely HTML form content)');
                console.log('Error:', err);
                console.log('Response text:', e.detail.xhr.responseText);
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
            console.log('Modal content swapped, processing HTMX attributes');
            // Ensure HTMX processes any new elements in the modal
            if (typeof htmx !== 'undefined') {
                htmx.process(e.detail.target);
                console.log('HTMX processing completed for modal content');
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
        
        // Configure HTMX to not cache modal content
        if (typeof htmx !== 'undefined') {
            htmx.config.disableSelector = '[hx-disable]';
            htmx.config.useTemplateFragments = false;
        }
        
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