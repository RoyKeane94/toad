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
});
