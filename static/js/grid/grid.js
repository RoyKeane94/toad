// Optimized task form validation function
function validateTaskForm(form) {
    const textInput = form.querySelector('input[name="text"]');
    const errorDiv = form.querySelector('.error-message');
    const value = textInput.value.trim();
    
    if (!value) {
        // Show error with faster DOM manipulation
        errorDiv.textContent = 'Please enter a task description';
        textInput.classList.replace('border-[var(--inline-input-border)]', 'border-red-500');
        textInput.focus();
        return false;
    } else {
        // Clear error faster
        errorDiv.textContent = '';
        textInput.classList.replace('border-red-500', 'border-[var(--inline-input-border)]');
        return true;
    }
}

// Debounced validation for real-time feedback
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Fast modal state management
const ModalManager = {
    activeModal: null,
    
    show(modalId, contentUrl = null) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        this.activeModal = modal;
        
        // Immediate visual feedback
        modal.classList.remove('opacity-0', 'invisible');
        modal.classList.add('opacity-100', 'visible');
        
        const content = modal.querySelector('[id$="-content"]');
        if (content) {
            content.classList.remove('scale-95');
            content.classList.add('scale-100');
        }
        
        // Load content if URL provided
        if (contentUrl) {
            this.loadContent(modalId, contentUrl);
        }
    },
    
    hide(modalId = null) {
        const modal = modalId ? document.getElementById(modalId) : this.activeModal;
        if (!modal) return;
        
        modal.classList.add('opacity-0', 'invisible');
        modal.classList.remove('opacity-100', 'visible');
        
        const content = modal.querySelector('[id$="-content"]');
        if (content) {
            content.classList.add('scale-95');
            content.classList.remove('scale-100');
        }
        
        this.activeModal = null;
    },
    
    loadContent(modalId, url) {
        const modal = document.getElementById(modalId);
        const content = modal.querySelector('#modal-content');
        if (!content) return;
        
        // Show loading state
        content.innerHTML = '<div class="p-8 text-center"><i class="fas fa-spinner fa-spin text-2xl text-[var(--primary-action-bg)]"></i><p class="mt-2 text-[var(--text-secondary)]">Loading...</p></div>';
        
        // Fast HTMX request with timeout
        fetch(url, {
            method: 'GET',
            headers: {
                'HX-Request': 'true',
                'X-Requested-With': 'XMLHttpRequest'
            },
            signal: AbortSignal.timeout(5000) // 5 second timeout
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.text();
        })
        .then(html => {
            content.innerHTML = html;
            // Focus first input for better UX
            const firstInput = content.querySelector('input, textarea, select');
            if (firstInput) firstInput.focus();
        })
        .catch(error => {
            console.error('Error loading modal content:', error);
            content.innerHTML = '<div class="p-8 text-center text-red-500"><i class="fas fa-exclamation-triangle text-2xl"></i><p class="mt-2">Failed to load content. Please try again.</p></div>';
        });
    }
};

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

    // Optimized Modal Functionality using ModalManager
    const modal = document.getElementById('modal');
    const modalContent = document.getElementById('modal-content');

    // Show modal with instant feedback
    document.body.addEventListener('openModal', function() {
        ModalManager.show('modal');
    });

    // Hide modal with instant feedback
    document.body.addEventListener('closeModal', function() {
        ModalManager.hide('modal');
    });

    // Optimized grid refresh - only refresh if needed
    document.body.addEventListener('refreshGrid', function() {
        // Use HTMX to refresh only the grid container instead of full page reload
        const gridContainer = document.querySelector('.grid-container');
        if (gridContainer && window.htmx) {
            htmx.ajax('GET', window.location.href, {
                target: '.grid-container-wrapper',
                swap: 'outerHTML'
            });
        } else {
            window.location.reload();
        }
    });

    // Fast modal close handlers
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                ModalManager.hide('modal');
            }
        });
    }

    // Global escape key handler
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && ModalManager.activeModal) {
            ModalManager.hide();
        }
    });

    // Optimized close button handler with event delegation
    document.addEventListener('click', function(e) {
        if (e.target.closest('.close-modal')) {
            e.preventDefault();
            ModalManager.hide();
        }
    });

    // Optimize modal button clicks with immediate visual feedback
    document.addEventListener('click', function(e) {
        const modalBtn = e.target.closest('[hx-get][hx-target="#modal-content"]');
        if (modalBtn) {
            // Show modal immediately, then load content
            ModalManager.show('modal');
            
            // Add loading state to button
            const originalHtml = modalBtn.innerHTML;
            modalBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            modalBtn.disabled = true;
            
            // Restore button after a short delay
            setTimeout(() => {
                modalBtn.innerHTML = originalHtml;
                modalBtn.disabled = false;
            }, 1000);
        }
    });

    // Optimized Task Form Management
    function setupTaskFormClearing() {
        document.querySelectorAll('.task-form').forEach(form => {
            const input = form.querySelector('input[name="text"]');
            if (!input) return;
            
            // Add real-time validation
            const debouncedValidation = debounce(() => {
                if (input.value.trim()) {
                    const errorDiv = form.querySelector('.error-message');
                    if (errorDiv && errorDiv.textContent) {
                        errorDiv.textContent = '';
                        input.classList.replace('border-red-500', 'border-[var(--inline-input-border)]');
                    }
                }
            }, 300);
            
            input.addEventListener('input', debouncedValidation);
            
            // Optimized HTMX response handling
            form.addEventListener('htmx:afterRequest', function(e) {
                if (e.detail.successful) {
                    // Fast DOM updates
                    input.value = '';
                    input.focus();
                    
                    const errorDiv = form.querySelector('.error-message');
                    if (errorDiv) {
                        errorDiv.textContent = '';
                    }
                    
                    // Remove any error styling
                    input.classList.replace('border-red-500', 'border-[var(--inline-input-border)]');
                }
            });
            
            // Add optimized form submission feedback
            form.addEventListener('htmx:beforeRequest', function() {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.classList.add('opacity-75');
                    submitBtn.disabled = true;
                }
            });
            
            form.addEventListener('htmx:afterRequest', function() {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.classList.remove('opacity-75');
                    submitBtn.disabled = false;
                }
            });
        });
    }
    
    // Initial setup for task form clearing
    setupTaskFormClearing();
    
    // Re-setup after HTMX updates with debouncing
    const debouncedSetup = debounce(setupTaskFormClearing, 100);
    document.body.addEventListener('htmx:afterSwap', debouncedSetup);
    document.body.addEventListener('htmx:afterSettle', debouncedSetup);

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
