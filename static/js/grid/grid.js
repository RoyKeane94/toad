// Task form validation function
function validateTaskForm(form) {
    const textInput = form.querySelector('input[name="text"]');
    const errorDiv = form.querySelector('.error-message');
    
    if (!textInput.value.trim()) {
        // Show error
        errorDiv.innerHTML = 'Please enter a task description';
        textInput.classList.remove('border-[var(--inline-input-border)]');
        textInput.classList.add('border-red-500');
        textInput.focus();
        return false; // Prevent form submission
    } else {
        // Clear error
        errorDiv.innerHTML = '';
        textInput.classList.remove('border-red-500');
        textInput.classList.add('border-[var(--inline-input-border)]');
        return true; // Allow form submission
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('Grid JavaScript loaded and DOM ready');
    
    // Project Switcher Dropdown Functionality
    function setupProjectSwitcher() {
    const switcherBtn = document.getElementById('project-switcher-btn');
    const switcherDropdown = document.getElementById('project-switcher-dropdown');
    const switcherChevron = document.getElementById('switcher-chevron');
    const switcherContainer = document.getElementById('project-switcher-container');
        
        if (!switcherBtn || !switcherDropdown || !switcherChevron || !switcherContainer) {
            return;
        }
    
    let isDropdownOpen = false;
    
    function toggleDropdown() {
        isDropdownOpen = !isDropdownOpen;
        
        if (isDropdownOpen) {
            // Show dropdown
            switcherDropdown.classList.remove('opacity-0', 'invisible', 'scale-95');
            switcherDropdown.classList.add('opacity-100', 'visible', 'scale-100');
            switcherChevron.style.transform = 'rotate(180deg)';
            
            // Add subtle glow effect to button
            switcherBtn.classList.add('ring-2', 'ring-[var(--primary-action-bg)]/20');
        } else {
            // Hide dropdown
            switcherDropdown.classList.add('opacity-0', 'invisible', 'scale-95');
            switcherDropdown.classList.remove('opacity-100', 'visible', 'scale-100');
            switcherChevron.style.transform = 'rotate(0deg)';
            
            // Remove glow effect
            switcherBtn.classList.remove('ring-2', 'ring-[var(--primary-action-bg)]/20');
        }
    }
    
    function closeDropdown() {
        if (isDropdownOpen) {
            toggleDropdown();
        }
    }
        
        // Remove any existing event listeners by cloning the button
        const newSwitcherBtn = switcherBtn.cloneNode(true);
        switcherBtn.parentNode.replaceChild(newSwitcherBtn, switcherBtn);
    
    // Toggle dropdown on button click
        newSwitcherBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleDropdown();
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!switcherContainer.contains(e.target)) {
            closeDropdown();
        }
    });
    
    // Close dropdown on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeDropdown();
        }
    });
    
    // Add smooth hover animations to dropdown items
    const dropdownItems = switcherDropdown.querySelectorAll('a');
    dropdownItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(2px)';
        });
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
        });
    });
    }
    
    // Initialize project switcher
    setupProjectSwitcher();

    // Row and Column Actions Dropdown Functionality
    function setupActionsDropdowns() {
        // Handle column actions dropdowns
        document.querySelectorAll('.column-actions-btn').forEach(btn => {
            const dropdown = btn.nextElementSibling;
            let isOpen = false;

            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                
                // Close all other dropdowns
                document.querySelectorAll('.column-actions-dropdown, .row-actions-dropdown').forEach(dd => {
                    if (dd !== dropdown) {
                        dd.classList.add('opacity-0', 'invisible', 'scale-95');
                        dd.classList.remove('opacity-100', 'visible', 'scale-100');
                    }
                });

                // Toggle current dropdown
                isOpen = !isOpen;
                if (isOpen) {
                    dropdown.classList.remove('opacity-0', 'invisible', 'scale-95');
                    dropdown.classList.add('opacity-100', 'visible', 'scale-100');
                } else {
                    dropdown.classList.add('opacity-0', 'invisible', 'scale-95');
                    dropdown.classList.remove('opacity-100', 'visible', 'scale-100');
                }
            });

            // Close dropdown when clicking on dropdown actions - but let HTMX handle the request first
            dropdown.addEventListener('click', function(e) {
                // Only close if not clicking on a button with HTMX attributes
                const clickedButton = e.target.closest('button');
                if (clickedButton && (clickedButton.hasAttribute('hx-get') || clickedButton.hasAttribute('hx-post'))) {
                    // Let HTMX handle this, close dropdown after a short delay
                    setTimeout(() => {
                        isOpen = false;
                        dropdown.classList.add('opacity-0', 'invisible', 'scale-95');
                        dropdown.classList.remove('opacity-100', 'visible', 'scale-100');
                    }, 100);
                } else {
                    // Close immediately for non-HTMX buttons
                isOpen = false;
                dropdown.classList.add('opacity-0', 'invisible', 'scale-95');
                dropdown.classList.remove('opacity-100', 'visible', 'scale-100');
                }
            });
        });

        // Handle row actions dropdowns
        document.querySelectorAll('.row-actions-btn').forEach(btn => {
            const dropdown = btn.nextElementSibling;
            let isOpen = false;

            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                
                // Close all other dropdowns
                document.querySelectorAll('.column-actions-dropdown, .row-actions-dropdown').forEach(dd => {
                    if (dd !== dropdown) {
                        dd.classList.add('opacity-0', 'invisible', 'scale-95');
                        dd.classList.remove('opacity-100', 'visible', 'scale-100');
                    }
                });

                // Toggle current dropdown
                isOpen = !isOpen;
                if (isOpen) {
                    dropdown.classList.remove('opacity-0', 'invisible', 'scale-95');
                    dropdown.classList.add('opacity-100', 'visible', 'scale-100');
                } else {
                    dropdown.classList.add('opacity-0', 'invisible', 'scale-95');
                    dropdown.classList.remove('opacity-100', 'visible', 'scale-100');
                }
            });

            // Close dropdown when clicking on dropdown actions - but let HTMX handle the request first
            dropdown.addEventListener('click', function(e) {
                // Only close if not clicking on a button with HTMX attributes
                const clickedButton = e.target.closest('button');
                if (clickedButton && (clickedButton.hasAttribute('hx-get') || clickedButton.hasAttribute('hx-post'))) {
                    // Let HTMX handle this, close dropdown after a short delay
                    setTimeout(() => {
                        isOpen = false;
                        dropdown.classList.add('opacity-0', 'invisible', 'scale-95');
                        dropdown.classList.remove('opacity-100', 'visible', 'scale-100');
                    }, 100);
                } else {
                    // Close immediately for non-HTMX buttons
                isOpen = false;
                dropdown.classList.add('opacity-0', 'invisible', 'scale-95');
                dropdown.classList.remove('opacity-100', 'visible', 'scale-100');
                }
            });
        });

        // Close all dropdowns when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.column-actions-btn') && !e.target.closest('.row-actions-btn') && !e.target.closest('.column-actions-dropdown') && !e.target.closest('.row-actions-dropdown')) {
                document.querySelectorAll('.column-actions-dropdown, .row-actions-dropdown').forEach(dropdown => {
                    dropdown.classList.add('opacity-0', 'invisible', 'scale-95');
                    dropdown.classList.remove('opacity-100', 'visible', 'scale-100');
                });
            }
        });

        // Close dropdowns on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                document.querySelectorAll('.column-actions-dropdown, .row-actions-dropdown').forEach(dropdown => {
                    dropdown.classList.add('opacity-0', 'invisible', 'scale-95');
                    dropdown.classList.remove('opacity-100', 'visible', 'scale-100');
                });
            }
        });
    }

    // Initialize actions dropdowns
    setupActionsDropdowns();

    // Task Deletion Modal Functionality
    const deleteModal = document.getElementById('delete-task-modal');
    const deleteModalContent = document.getElementById('delete-modal-content');
    const taskToDeleteElement = document.getElementById('task-to-delete');
    const deleteTaskForm = document.getElementById('delete-task-form');
    const closeDeleteModalBtn = document.getElementById('close-delete-modal');
    const cancelDeleteTaskBtn = document.getElementById('cancel-delete-task');
    
    let currentTaskId = null;
    let currentDeleteUrl = null;
    
    // Show delete modal
    function showDeleteModal(taskId, taskText, deleteUrl) {
        currentTaskId = taskId;
        currentDeleteUrl = deleteUrl;
        
        taskToDeleteElement.textContent = taskText;
        deleteTaskForm.action = deleteUrl;
        
        // Show modal with animation
        deleteModal.classList.remove('opacity-0', 'invisible');
        deleteModalContent.classList.remove('scale-95');
        deleteModalContent.classList.add('scale-100');
        
        // Focus on cancel button for accessibility
        setTimeout(() => cancelDeleteTaskBtn.focus(), 100);
    }
    
    // Hide delete modal
    function hideDeleteModal() {
        deleteModal.classList.add('opacity-0', 'invisible');
        deleteModalContent.classList.remove('scale-100');
        deleteModalContent.classList.add('scale-95');
        
        currentTaskId = null;
        currentDeleteUrl = null;
    }
    
    // Handle delete button clicks
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-task-btn')) {
            e.preventDefault();
            const btn = e.target.closest('.delete-task-btn');
            const taskId = btn.dataset.taskId;
            const taskText = btn.dataset.taskText;
            const deleteUrl = btn.dataset.deleteUrl;
            
            showDeleteModal(taskId, taskText, deleteUrl);
        }
    });
    
    // Handle modal close buttons
    closeDeleteModalBtn.addEventListener('click', hideDeleteModal);
    cancelDeleteTaskBtn.addEventListener('click', hideDeleteModal);
    
    // Handle clicking outside modal
    deleteModal.addEventListener('click', function(e) {
        if (e.target === deleteModal) {
            hideDeleteModal();
        }
    });
    
    // Handle escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !deleteModal.classList.contains('invisible')) {
            hideDeleteModal();
        }
    });
    
    // Handle delete form submission
    deleteTaskForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!currentTaskId || !currentDeleteUrl) return;
        
        // Show loading state
        const submitBtn = deleteTaskForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Deleting...';
        submitBtn.disabled = true;
        
        // Make HTMX request
        fetch(currentDeleteUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'HX-Request': 'true'
            }
        })
        .then(response => {
            if (response.ok) {
                // Remove task from DOM
                const taskElement = document.getElementById(`task-${currentTaskId}`);
                if (taskElement) {
                    taskElement.style.transform = 'translateX(-100%)';
                    taskElement.style.opacity = '0';
                    setTimeout(() => taskElement.remove(), 300);
                }
                hideDeleteModal();
            } else {
                throw new Error('Delete failed');
            }
        })
        .catch(error => {
            console.error('Error deleting task:', error);
            alert('Failed to delete task. Please try again.');
        })
        .finally(() => {
            // Restore button state
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
    });

    // Generic Modal Functionality
    const modal = document.getElementById('modal');
    const modalContent = document.getElementById('modal-content');

    // Show modal
    document.body.addEventListener('openModal', function() {
        modal.classList.remove('opacity-0', 'invisible');
        modal.classList.add('opacity-100', 'visible');
        modalContent.classList.remove('scale-95');
        modalContent.classList.add('scale-100');
    });

    // Hide modal
    document.body.addEventListener('closeModal', function() {
        modal.classList.add('opacity-0', 'invisible');
        modal.classList.remove('opacity-100', 'visible');
        modalContent.classList.add('scale-95');
        modalContent.classList.remove('scale-100');
    });

    // Refresh grid
    document.body.addEventListener('refreshGrid', function() {
        window.location.reload();
    });

    // Close modal when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            document.body.dispatchEvent(new Event('closeModal'));
        }
    });

    // Close modal when pressing Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !modal.classList.contains('invisible')) {
            document.body.dispatchEvent(new Event('closeModal'));
        }
    });

    // Handle close modal buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.close-modal')) {
            document.body.dispatchEvent(new Event('closeModal'));
        }
    });

    // Task Form Input Clearing and Add Task Form Behavior
    function setupTaskFormClearing() {
        document.querySelectorAll('.task-form').forEach(form => {
            const input = form.querySelector('input[name="text"]');
            if (!input) return;
            
            // Clear input after successful HTMX request
            form.addEventListener('htmx:afterRequest', function(e) {
                if (e.detail.successful) {
                    input.value = '';
                    
                    // For add task forms, collapse back to trigger state
                    if (form.classList.contains('add-task-form')) {
                        collapseAddTaskForm(form);
                    } else {
                        input.focus();
                    }
                    
                    // Clear any error messages
                    const errorDiv = form.querySelector('.error-message');
                    if (errorDiv) {
                        errorDiv.innerHTML = '';
                    }
                }
            });
        });
    }

    // Add Task Form Expand/Collapse Functionality
    function setupAddTaskForms() {
        document.querySelectorAll('.add-task-form').forEach(form => {
            const trigger = form.querySelector('.add-task-trigger');
            const collapsed = form.querySelector('.add-task-collapsed');
            const expanded = form.querySelector('.add-task-expanded');
            const cancelBtn = form.querySelector('.add-task-cancel');
            const input = form.querySelector('input[name="text"]');

            if (!trigger || !collapsed || !expanded || !cancelBtn || !input) return;

            // Expand form when trigger is clicked
            trigger.addEventListener('click', function(e) {
                e.preventDefault();
                expandAddTaskForm(form);
            });

            // Collapse form when cancel is clicked
            cancelBtn.addEventListener('click', function(e) {
                e.preventDefault();
                collapseAddTaskForm(form);
            });

            // Auto-focus input when expanded
            input.addEventListener('focus', function() {
                if (collapsed.style.display !== 'none') {
                    expandAddTaskForm(form);
                }
            });
        });

        // Close all expanded forms when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.add-task-form')) {
                document.querySelectorAll('.add-task-form').forEach(form => {
                    collapseAddTaskForm(form);
                });
            }
        });

        // Close expanded forms on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                document.querySelectorAll('.add-task-form').forEach(form => {
                    collapseAddTaskForm(form);
                });
            }
        });
    }

    function expandAddTaskForm(form) {
        const collapsed = form.querySelector('.add-task-collapsed');
        const expanded = form.querySelector('.add-task-expanded');
        const input = form.querySelector('input[name="text"]');

        if (collapsed && expanded && input) {
            collapsed.style.display = 'none';
            expanded.classList.remove('hidden');
            
            // Focus input after a small delay to ensure it's visible
            setTimeout(() => {
                input.focus();
            }, 100);
        }
    }

    function collapseAddTaskForm(form) {
        const collapsed = form.querySelector('.add-task-collapsed');
        const expanded = form.querySelector('.add-task-expanded');
        const input = form.querySelector('input[name="text"]');
        const errorDiv = form.querySelector('.error-message');

        if (collapsed && expanded) {
            collapsed.style.display = 'block';
            expanded.classList.add('hidden');
            
            // Clear input and errors when collapsing
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
    
    // Initial setup for task form clearing and add task forms
    setupTaskFormClearing();
    setupAddTaskForms();
    
    // Re-setup after HTMX updates
    document.body.addEventListener('htmx:afterSwap', function() {
        setupProjectSwitcher();
        setupTaskFormClearing();
        setupAddTaskForms();
        setupActionsDropdowns();
    });
    document.body.addEventListener('htmx:afterSettle', function() {
        setupProjectSwitcher();
        setupTaskFormClearing();
        setupAddTaskForms();
        setupActionsDropdowns();
    });

    // Grid Horizontal Scrolling Enhancement
    function setupGridScrolling() {
        const scrollable = document.querySelector('.grid-table-scrollable');
        if (!scrollable) return;
        const leftBtn = document.querySelector('.left-scroll-btn');
        const rightBtn = document.querySelector('.right-scroll-btn');
        const gridTable = scrollable.querySelector('.grid-table');
        const dataCols = scrollable.querySelectorAll('col.data-column');

        if (!leftBtn || !rightBtn || !gridTable || dataCols.length === 0) return;

        const totalDataColumns = parseInt(gridTable.dataset.totalDataColumns);
        const columnsToShow = Math.min(3, totalDataColumns);
        
        let currentCol = 0;
        let dataColWidth = 0;

        function calculateAndApplyWidths() {
            if (columnsToShow > 0) {
                const containerWidth = scrollable.clientWidth;
                dataColWidth = containerWidth / columnsToShow;
                dataCols.forEach(col => {
                    col.style.width = `${dataColWidth}px`;
                });

                // Explicitly set the total width of the inner table
                const totalTableWidth = dataColWidth * totalDataColumns;
                gridTable.style.width = `${totalTableWidth}px`;
            }
            syncRowHeights();
        }

        function updateButtons() {
            if (totalDataColumns <= columnsToShow) {
                leftBtn.disabled = true;
                rightBtn.disabled = true;
                leftBtn.style.display = 'none';
                rightBtn.style.display = 'none';
            } else {
                leftBtn.style.display = 'flex';
                rightBtn.style.display = 'flex';
                leftBtn.disabled = currentCol === 0;
                rightBtn.disabled = currentCol >= totalDataColumns - columnsToShow;
            }
        }

        function scrollToCol(colIdx, behavior = 'smooth') {
            currentCol = Math.max(0, Math.min(colIdx, totalDataColumns - columnsToShow));
            const scrollLeft = currentCol * dataColWidth;
            scrollable.scrollTo({ left: scrollLeft, behavior: behavior });
            updateButtons();
        }
        
        leftBtn.onclick = () => scrollToCol(currentCol - 1);
        rightBtn.onclick = () => scrollToCol(currentCol + 1);

        // Re-calculate on resize
        const resizeObserver = new ResizeObserver(entries => {
            calculateAndApplyWidths();
            scrollToCol(currentCol, 'auto'); // Snap without animation on resize
        });
        resizeObserver.observe(scrollable);

        // Initial setup
        calculateAndApplyWidths();
        updateButtons();
        
        const scrollToEnd = sessionStorage.getItem('scrollToEnd');
        if (scrollToEnd) {
            // Scroll to the very last column
            sessionStorage.removeItem('scrollToEnd'); // Use the flag and lose it
            setTimeout(() => {
                const lastColIndex = totalDataColumns - columnsToShow;
                scrollToCol(lastColIndex, 'auto');
            }, 50);

                } else {
            // Restore previous scroll position if it exists
            const savedPosition = sessionStorage.getItem('grid-scroll-position');
            if (savedPosition) {
                sessionStorage.removeItem('grid-scroll-position');
                setTimeout(() => {
                    if (dataColWidth > 0) {
                        const savedCol = Math.round(parseFloat(savedPosition) / dataColWidth);
                        scrollToCol(savedCol, 'auto');
                } else {
                        scrollToCol(0, 'auto');
                    }
                }, 50);
            } else {
                scrollToCol(0, 'auto');
            }
        }
        
        // Save scroll position before HTMX requests
        document.addEventListener('htmx:beforeRequest', function(event) {
            sessionStorage.setItem('grid-scroll-position', scrollable.scrollLeft.toString());
        });
    }

    function syncRowHeights() {
        const fixedRows = document.querySelectorAll('.grid-table-fixed tr');
        const scrollRows = document.querySelectorAll('.grid-table-scrollable .grid-table tr');
        if (fixedRows.length !== scrollRows.length) return;

        for (let i = 0; i < fixedRows.length; i++) {
            const fixedCell = fixedRows[i].querySelector('td, th');
            const scrollCell = scrollRows[i].querySelector('td, th');
            
            if (fixedCell && scrollCell) {
                // Reset heights to auto to get the natural height
                fixedCell.style.height = 'auto';
                scrollCell.style.height = 'auto';
                
                // Set both to the maximum of the two natural heights
                const maxH = Math.max(fixedCell.offsetHeight, scrollCell.offsetHeight);
                fixedCell.style.height = maxH + 'px';
                scrollCell.style.height = maxH + 'px';
            }
        }
    }

    // Re-initialize components after HTMX swaps
    document.body.addEventListener('htmx:afterSettle', function(event) {
        console.log('HTMX Swap: Re-initializing components.');
        
        // Re-init general components
        if (typeof setupProjectSwitcher === 'function') setupProjectSwitcher();
        if (typeof setupActionsDropdowns === 'function') setupActionsDropdowns();
        if (typeof setupAddTaskForms === 'function') setupAddTaskForms();
        
        // Always re-init grid and sync heights
        setupGridScrolling();
        setTimeout(syncRowHeights, 50); // Sync after content settles
    });

    // Initialize grid scrolling
    setupGridScrolling();
});
