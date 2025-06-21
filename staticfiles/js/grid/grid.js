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
    // Project Switcher Dropdown Functionality
    const switcherBtn = document.getElementById('project-switcher-btn');
    const switcherDropdown = document.getElementById('project-switcher-dropdown');
    const switcherChevron = document.getElementById('switcher-chevron');
    const switcherContainer = document.getElementById('project-switcher-container');
    
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
    
    // Toggle dropdown on button click
    switcherBtn.addEventListener('click', function(e) {
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
        setupTaskFormClearing();
        setupAddTaskForms();
        setupActionsDropdowns();
    });
    document.body.addEventListener('htmx:afterSettle', function() {
        setupTaskFormClearing();
        setupAddTaskForms();
        setupActionsDropdowns();
    });

    // Grid Horizontal Scrolling Enhancement
    function setupGridScrolling() {
        const gridContainer = document.querySelector('.grid-container');
        if (!gridContainer) return;

        let scrollIndicators = null;
        let currentVisibleStartColumn = 0; // Track which column is the first visible
        const maxVisibleColumns = 3; // Maximum number of data columns to show at once

        // Calculate and set column widths for optimal display
        function calculateColumnWidths() {
            const gridTable = gridContainer.querySelector('.grid-table');
            if (!gridTable) return;

            // Get total columns info from data attributes
            const totalColumns = parseInt(gridContainer.dataset.totalColumns) || 0;
            const totalDataColumns = totalColumns - 1; // Subtract category column
            
            if (totalDataColumns === 0) return;

            // Get responsive widths for category column
            const windowWidth = window.innerWidth;
            let categoryWidth;
            
            if (windowWidth <= 768) {
                categoryWidth = 200;
            } else if (windowWidth <= 1024) {
                categoryWidth = 250;
            } else {
                categoryWidth = 300;
            }

            // Calculate available width for data columns
            const containerWidth = gridContainer.clientWidth;
            const availableWidthForDataColumns = containerWidth - categoryWidth;
            
            // Determine how many data columns to show (up to max 3)
            const visibleDataColumns = Math.min(maxVisibleColumns, totalDataColumns);
            
            // Each visible data column gets equal share of available space
            const dataColumnWidth = Math.floor(availableWidthForDataColumns / visibleDataColumns);
            
            // Set category column width
            const categoryCol = gridTable.querySelector('colgroup col.category-column');
            if (categoryCol) {
                categoryCol.style.width = categoryWidth + 'px';
            }

            // Set ALL data column widths to the same value
            const dataColumns = gridTable.querySelectorAll('colgroup col.data-column');
            dataColumns.forEach(col => {
                col.style.width = dataColumnWidth + 'px';
            });

            // Calculate total table width for scrolling (includes all columns)
            const totalTableWidth = categoryWidth + (totalDataColumns * dataColumnWidth);
            gridTable.style.width = totalTableWidth + 'px';
            
            return { totalDataColumns, dataColumnWidth, categoryWidth, visibleDataColumns };
        }

        // Get scroll amount - one column width
        function getScrollAmount() {
            const columnInfo = calculateColumnWidths();
            return columnInfo ? columnInfo.dataColumnWidth : 300;
        }

        // Update which columns are visible based on scroll position
        function updateVisibleColumns() {
            const columnInfo = calculateColumnWidths();
            if (!columnInfo) return;

            const scrollLeft = gridContainer.scrollLeft;
            const columnWidth = columnInfo.dataColumnWidth;
            
            // Calculate which column should be the first visible based on scroll position
            currentVisibleStartColumn = Math.round(scrollLeft / columnWidth);
            currentVisibleStartColumn = Math.max(0, Math.min(currentVisibleStartColumn, columnInfo.totalDataColumns - 1));
        }

        // Setup external scroll buttons
        function setupScrollButtons() {
            // Find existing buttons in the template
            const leftBtn = document.querySelector('.left-scroll-btn');
            const rightBtn = document.querySelector('.right-scroll-btn');
            
            if (!leftBtn || !rightBtn) return;

            // Store reference to buttons
            scrollIndicators = {
                leftBtn: leftBtn,
                rightBtn: rightBtn
            };

            // Create scroll progress indicator
            let progressTrack = document.querySelector('.grid-scroll-progress-track');
            if (!progressTrack) {
                progressTrack = document.createElement('div');
                progressTrack.className = 'grid-scroll-progress-track';
                
                const progressBar = document.createElement('div');
                progressBar.className = 'grid-scroll-progress';
                progressBar.style.width = '0%';
                
                progressTrack.appendChild(progressBar);
                gridContainer.parentElement.appendChild(progressTrack);
            }

            // Add click handlers for scroll buttons
            leftBtn.addEventListener('click', () => {
                const columnInfo = calculateColumnWidths();
                if (!columnInfo) return;

                // Move one column to the left
                const targetColumn = Math.max(0, currentVisibleStartColumn - 1);
                const targetScrollPosition = targetColumn * columnInfo.dataColumnWidth;
                
                gridContainer.scrollTo({ left: targetScrollPosition, behavior: 'smooth' });
                
                // Update immediately for responsive UI
                currentVisibleStartColumn = targetColumn;
                setTimeout(updateScrollIndicators, 50);
                setTimeout(updateScrollIndicators, 300);
            });

            rightBtn.addEventListener('click', () => {
                const columnInfo = calculateColumnWidths();
                if (!columnInfo) return;

                // Move one column to the right
                const maxStartColumn = Math.max(0, columnInfo.totalDataColumns - maxVisibleColumns);
                const targetColumn = Math.min(maxStartColumn, currentVisibleStartColumn + 1);
                const targetScrollPosition = targetColumn * columnInfo.dataColumnWidth;
                
                gridContainer.scrollTo({ left: targetScrollPosition, behavior: 'smooth' });
                
                // Update immediately for responsive UI
                currentVisibleStartColumn = targetColumn;
                setTimeout(updateScrollIndicators, 50);
                setTimeout(updateScrollIndicators, 300);
            });
        }

        // Update scroll indicators visibility and progress
        function updateScrollIndicators() {
            if (!scrollIndicators) return;

            const progressBar = document.querySelector('.grid-scroll-progress');
            const columnInfo = calculateColumnWidths();
            if (!columnInfo) return;

            const totalDataColumns = columnInfo.totalDataColumns;
            
            // Update current visible start column based on actual scroll position
            updateVisibleColumns();
            
            // Determine if scrolling is needed
            const hasScrollableContent = totalDataColumns > maxVisibleColumns;
            
            if (hasScrollableContent) {
                const canScrollLeft = currentVisibleStartColumn > 0;
                const canScrollRight = currentVisibleStartColumn < (totalDataColumns - maxVisibleColumns);

                // Update button states
                if (canScrollLeft) {
                    scrollIndicators.leftBtn.classList.add('active');
                    scrollIndicators.leftBtn.disabled = false;
                } else {
                    scrollIndicators.leftBtn.classList.remove('active');
                    scrollIndicators.leftBtn.disabled = true;
                }

                if (canScrollRight) {
                    scrollIndicators.rightBtn.classList.add('active');
                    scrollIndicators.rightBtn.disabled = false;
                } else {
                    scrollIndicators.rightBtn.classList.remove('active');
                    scrollIndicators.rightBtn.disabled = true;
                }

                // Update progress bar
                if (progressBar) {
                    const maxScrollableColumns = totalDataColumns - maxVisibleColumns;
                    const scrollPercentage = maxScrollableColumns > 0 ? (currentVisibleStartColumn / maxScrollableColumns) * 100 : 0;
                    progressBar.style.width = Math.min(100, Math.max(0, scrollPercentage)) + '%';
                }
            } else {
                // No scrolling needed, disable buttons
                scrollIndicators.leftBtn.classList.remove('active');
                scrollIndicators.leftBtn.disabled = true;
                scrollIndicators.rightBtn.classList.remove('active');
                scrollIndicators.rightBtn.disabled = true;
                
                if (progressBar) {
                    progressBar.style.width = '0%';
                }
            }

            // Update scroll fade gradients (if needed in future)
            gridContainer.classList.toggle('can-scroll-left', hasScrollableContent && currentVisibleStartColumn > 0);
            gridContainer.classList.toggle('can-scroll-right', hasScrollableContent && currentVisibleStartColumn < (totalDataColumns - maxVisibleColumns));
        }

        // Initialize column widths and scroll indicators
        calculateColumnWidths();
        setupScrollButtons();
        updateScrollIndicators();

        // Update indicators on scroll
        gridContainer.addEventListener('scroll', updateScrollIndicators);

        // Force update after a short delay to ensure everything is rendered
        setTimeout(updateScrollIndicators, 100);
        setTimeout(updateScrollIndicators, 500);

        // Update everything on window resize
        window.addEventListener('resize', function() {
            calculateColumnWidths();
            setTimeout(updateScrollIndicators, 100);
        });

        // Keyboard navigation
        gridContainer.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowLeft' && e.ctrlKey) {
                e.preventDefault();
                scrollIndicators.leftBtn.click();
            } else if (e.key === 'ArrowRight' && e.ctrlKey) {
                e.preventDefault();
                scrollIndicators.rightBtn.click();
            }
        });

        // Make grid container focusable for keyboard navigation
        gridContainer.tabIndex = 0;
        gridContainer.style.outline = 'none';

        // Disable smooth scrolling behavior to prevent partial columns
        gridContainer.style.scrollBehavior = 'auto';

        // Disable horizontal mouse wheel scrolling only
        gridContainer.addEventListener('wheel', function(e) {
            // Only prevent horizontal scrolling, allow vertical scrolling
            if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
                e.preventDefault();
            }
        }, { passive: false });
    }

    // Initialize grid scrolling
    setupGridScrolling();

    // Re-initialize after HTMX updates
    document.body.addEventListener('htmx:afterSettle', function() {
        setupGridScrolling();
    });
});
