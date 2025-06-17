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

    // Task Form Input Clearing
    function setupTaskFormClearing() {
        document.querySelectorAll('.task-form').forEach(form => {
            const input = form.querySelector('input[name="text"]');
            if (!input) return;
            
            // Clear input after successful HTMX request
            form.addEventListener('htmx:afterRequest', function(e) {
                if (e.detail.successful) {
                    input.value = '';
                    input.focus();
                    
                    // Clear any error messages
                    const errorDiv = form.querySelector('.error-message');
                    if (errorDiv) {
                        errorDiv.innerHTML = '';
                    }
                }
            });
        });
    }
    
    // Initial setup for task form clearing
    setupTaskFormClearing();
    
    // Re-setup after HTMX updates
    document.body.addEventListener('htmx:afterSwap', setupTaskFormClearing);
    document.body.addEventListener('htmx:afterSettle', setupTaskFormClearing);

    // Grid Horizontal Scrolling Enhancement
    function setupGridScrolling() {
        const gridContainer = document.querySelector('.grid-container');
        if (!gridContainer) return;

        let scrollIndicators = null;

        // Calculate and set column widths
        function calculateColumnWidths() {
            const gridTable = gridContainer.querySelector('.grid-table');
            if (!gridTable) return;

            const categoryColumns = gridTable.querySelectorAll('colgroup col.category-column');
            const dataColumns = gridTable.querySelectorAll('colgroup col.data-column');
            
            if (dataColumns.length === 0) return;

            // Get the actual available width (grid container wrapper is reduced by 120px for buttons)
            const containerWidth = gridContainer.clientWidth;
            const windowWidth = window.innerWidth;
            
            // Responsive breakpoints
            let categoryWidth = 300;
            let minDataColumnWidth = 380;
            
            if (windowWidth <= 768) {
                categoryWidth = 150;
                minDataColumnWidth = 320;
            } else if (windowWidth <= 1024) {
                minDataColumnWidth = 350;
            }

            const availableWidth = containerWidth - categoryWidth;
            const idealDataColumnWidth = availableWidth / dataColumns.length;

            // Check if we can fit all columns at their ideal width
            if (idealDataColumnWidth >= minDataColumnWidth) {
                // Columns can be evenly distributed
                gridTable.style.width = '100%';
                dataColumns.forEach(col => {
                    col.style.width = idealDataColumnWidth + 'px';
                });
            } else {
                // Columns need to be at minimum width, table becomes scrollable
                const totalMinWidth = categoryWidth + (dataColumns.length * minDataColumnWidth);
                gridTable.style.width = totalMinWidth + 'px';
                dataColumns.forEach(col => {
                    col.style.width = minDataColumnWidth + 'px';
                });
            }
        }

        // Get scroll amount based on current column width
        function getScrollAmount() {
            const windowWidth = window.innerWidth;
            if (windowWidth <= 768) {
                return 320; // Mobile column width
            } else if (windowWidth <= 1024) {
                return 350; // Tablet column width
            } else {
                return 380; // Desktop column width
            }
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
            const progressTrack = document.createElement('div');
            progressTrack.className = 'grid-scroll-progress-track';
            
            const progressBar = document.createElement('div');
            progressBar.className = 'grid-scroll-progress';
            progressBar.style.width = '0%';
            
            progressTrack.appendChild(progressBar);
            gridContainer.parentElement.appendChild(progressTrack);

            // Add click handlers for scroll buttons
            leftBtn.addEventListener('click', () => {
                const scrollAmount = getScrollAmount();
                const currentScroll = gridContainer.scrollLeft;
                const newScrollPosition = Math.max(0, Math.floor(currentScroll / scrollAmount) * scrollAmount - scrollAmount);
                gridContainer.scrollTo({ left: newScrollPosition, behavior: 'smooth' });
                
                // Force update indicators after scroll
                setTimeout(updateScrollIndicators, 50);
                setTimeout(updateScrollIndicators, 300);
            });

            rightBtn.addEventListener('click', () => {
                const scrollAmount = getScrollAmount();
                const currentScroll = gridContainer.scrollLeft;
                const maxScroll = gridContainer.scrollWidth - gridContainer.clientWidth;
                const newScrollPosition = Math.min(maxScroll, Math.ceil(currentScroll / scrollAmount) * scrollAmount + scrollAmount);
                gridContainer.scrollTo({ left: newScrollPosition, behavior: 'smooth' });
                
                // Force update indicators after scroll
                setTimeout(updateScrollIndicators, 50);
                setTimeout(updateScrollIndicators, 300);
            });
        }

        // Update scroll indicators visibility and progress
        function updateScrollIndicators() {
            if (!scrollIndicators) return;

            const progressBar = document.querySelector('.grid-scroll-progress');

            const currentScroll = Math.round(gridContainer.scrollLeft);
            const maxScroll = Math.round(gridContainer.scrollWidth - gridContainer.clientWidth);
            
            // More reliable scroll detection
            const canScrollLeft = currentScroll > 5; // Increased tolerance
            const canScrollRight = currentScroll < (maxScroll - 5); // Increased tolerance

            // Update button states - grey by default, green when active
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

            // Update scroll fade gradients
            gridContainer.classList.toggle('can-scroll-left', canScrollLeft);
            gridContainer.classList.toggle('can-scroll-right', canScrollRight);

            // Update progress bar
            if (progressBar) {
                const scrollPercentage = maxScroll > 0 ? (currentScroll / maxScroll) * 100 : 0;
                progressBar.style.width = Math.min(100, Math.max(0, scrollPercentage)) + '%';
            }
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
                const scrollAmount = getScrollAmount();
                const currentScroll = gridContainer.scrollLeft;
                const newScrollPosition = Math.max(0, Math.floor(currentScroll / scrollAmount) * scrollAmount - scrollAmount);
                gridContainer.scrollTo({ left: newScrollPosition, behavior: 'smooth' });
            } else if (e.key === 'ArrowRight' && e.ctrlKey) {
                e.preventDefault();
                const scrollAmount = getScrollAmount();
                const currentScroll = gridContainer.scrollLeft;
                const maxScroll = gridContainer.scrollWidth - gridContainer.clientWidth;
                const newScrollPosition = Math.min(maxScroll, Math.ceil(currentScroll / scrollAmount) * scrollAmount + scrollAmount);
                gridContainer.scrollTo({ left: newScrollPosition, behavior: 'smooth' });
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
        // Small delay to ensure DOM is fully updated
        setTimeout(() => {
            const gridContainer = document.querySelector('.grid-container');
            if (gridContainer) {
                const calculateColumnWidths = () => {
                    const gridTable = gridContainer.querySelector('.grid-table');
                    if (!gridTable) return;

                    const categoryColumns = gridTable.querySelectorAll('colgroup col.category-column');
                    const dataColumns = gridTable.querySelectorAll('colgroup col.data-column');
                    
                    if (dataColumns.length === 0) return;

                    const containerWidth = gridContainer.clientWidth;
                    const windowWidth = window.innerWidth;
                    
                    // Responsive breakpoints
                    let categoryWidth = 300;
                    let minDataColumnWidth = 380;
                    
                    if (windowWidth <= 768) {
                        categoryWidth = 150;
                        minDataColumnWidth = 320;
                    } else if (windowWidth <= 1024) {
                        minDataColumnWidth = 350;
                    }

                    const availableWidth = containerWidth - categoryWidth;
                    const idealDataColumnWidth = availableWidth / dataColumns.length;

                    // Check if we can fit all columns at their ideal width
                    if (idealDataColumnWidth >= minDataColumnWidth) {
                        // Columns can be evenly distributed
                        gridTable.style.width = '100%';
                        dataColumns.forEach(col => {
                            col.style.width = idealDataColumnWidth + 'px';
                        });
                    } else {
                        // Columns need to be at minimum width, table becomes scrollable
                        const totalMinWidth = categoryWidth + (dataColumns.length * minDataColumnWidth);
                        gridTable.style.width = totalMinWidth + 'px';
                        dataColumns.forEach(col => {
                            col.style.width = minDataColumnWidth + 'px';
                        });
                    }
                };
                calculateColumnWidths();
            }
        }, 100);
    });
});
