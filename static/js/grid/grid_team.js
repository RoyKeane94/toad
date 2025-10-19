// Team functionality for Toad Grid
// Handles task assignment, user avatars, and team collaboration features

// Define color palette for user avatars
const avatarColors = [
    '#FF6B6B', // Red
    '#4ECDC4', // Teal
    '#45B7D1', // Blue
    '#FFA07A', // Light Salmon
    '#98D8C8', // Mint
    '#F7DC6F', // Yellow
    '#BB8FCE', // Purple
    '#85C1E2', // Sky Blue
    '#F8B88B', // Peach
    '#52B788'  // Green
];

// Function to get initials from a name
function getInitials(name) {
    const words = name.trim().split(' ');
    if (words.length >= 2) {
        return (words[0][0] + words[words.length - 1][0]).toUpperCase();
    }
    return name[0] ? name[0].toUpperCase() : '';
}

// Function to update task assignment display without page refresh
function updateTaskAssignmentDisplay(taskId, assignedUserId, assignedUserName) {
    const taskElement = document.getElementById(`task-${taskId}`);
    if (!taskElement) {
        return;
    }
    
    // Find the task text container
    const taskTextContainer = taskElement.querySelector('.flex-1.min-w-0');
    if (!taskTextContainer) {
        return;
    }
    
    // Check if assignment display already exists
    let assignmentDisplay = taskTextContainer.querySelector('.assignee-display');
    
    if (assignedUserId && assignedUserName) {
        // Get initials from name
        const initials = getInitials(assignedUserName);
        
        // Get color for this user using their ID for consistency
        const color = avatarColors[parseInt(assignedUserId) % avatarColors.length];
        
        if (!assignmentDisplay) {
            // Create new assignment display
            assignmentDisplay = document.createElement('div');
            assignmentDisplay.className = 'assignee-display flex items-center mt-1 text-xs ml-1';
            assignmentDisplay.innerHTML = `
                <div class="assignee-avatar" 
                     style="width: 16px; height: 16px; border-radius: 50%; background-color: ${color}; color: white; font-weight: 600; font-size: 8px; display: flex; align-items: center; justify-content: center; margin-right: 4px;" 
                     title="${assignedUserName}">
                    ${initials}
                </div>
            `;
            // Insert after the reminder display if it exists, otherwise after task text
            const taskTextDiv = taskTextContainer.querySelector('[id^="task-text-"]');
            const reminderDisplay = taskTextContainer.querySelector('.reminder-display');
            if (taskTextDiv) {
                if (reminderDisplay) {
                    // Insert after reminder display
                    reminderDisplay.parentNode.insertBefore(assignmentDisplay, reminderDisplay.nextSibling);
                } else {
                    // Insert after task text
                    taskTextDiv.parentNode.insertBefore(assignmentDisplay, taskTextDiv.nextSibling);
                }
            } else {
                taskTextContainer.appendChild(assignmentDisplay);
            }
        } else {
            // Update existing assignment display
            assignmentDisplay.innerHTML = `
                <div class="assignee-avatar" 
                     style="width: 16px; height: 16px; border-radius: 50%; background-color: ${color}; color: white; font-weight: 600; font-size: 8px; display: flex; align-items: center; justify-content: center; margin-right: 4px;" 
                     title="${assignedUserName}">
                    ${initials}
                </div>
            `;
        }
        
        // Update assign button data attribute
        const assignButtons = taskElement.querySelectorAll('.assign-task-btn');
        assignButtons.forEach(btn => {
            btn.setAttribute('data-assigned-to', assignedUserId);
        });
        
        // Update task element data attribute for filtering
        taskElement.setAttribute('data-assigned-user-id', assignedUserId);
    } else {
        // Remove assignment display if no user assigned
        if (assignmentDisplay) {
            assignmentDisplay.remove();
        }
        
        // Update assign button data attributes
        const assignButtons = taskElement.querySelectorAll('.assign-task-btn');
        assignButtons.forEach(btn => {
            btn.removeAttribute('data-assigned-to');
        });
        
        // Remove task element data attribute for filtering
        taskElement.removeAttribute('data-assigned-user-id');
    }
}

// Assign Task popup functionality
let currentTaskId = null;
let currentTaskText = null;
let assignPopup = null;

// Store team members data (populated from Django template)
let teamMembers = [];

// Function to show assign popup
function showAssignPopup(button, taskId, taskText, currentAssignedTo) {
    if (!assignPopup) {
        return;
    }
    
    currentTaskId = taskId;
    currentTaskText = taskText;
    
    // Build user list
    const userList = document.getElementById('user-list');
    if (!userList) {
        return;
    }
    userList.innerHTML = '';
    
    teamMembers.forEach((member) => {
        const avatar = document.createElement('div');
        avatar.className = 'user-avatar';
        // Use user ID to get consistent color
        const userIndex = parseInt(member.id) % avatarColors.length;
        avatar.style.backgroundColor = avatarColors[userIndex];
        avatar.textContent = member.initials;
        avatar.title = member.name;
        avatar.dataset.userId = member.id;
        
        if (member.id === currentAssignedTo) {
            avatar.classList.add('selected');
        }
        
        avatar.addEventListener('click', function() {
            assignTaskToUser(taskId, member.id, member.name);
        });
        
        userList.appendChild(avatar);
    });
    
    // Add unassign option if someone is currently assigned
    if (currentAssignedTo) {
        const unassignDiv = document.createElement('div');
        unassignDiv.className = 'unassign-option';
        unassignDiv.textContent = 'Unassign';
        unassignDiv.addEventListener('click', function() {
            assignTaskToUser(taskId, null, null);
        });
        userList.appendChild(unassignDiv);
    }
    
    // Position popup near the button
    const rect = button.getBoundingClientRect();
    assignPopup.style.position = 'fixed';
    assignPopup.style.left = `${rect.left}px`;
    assignPopup.style.top = `${rect.bottom + 8}px`;
    
    // Show popup
    assignPopup.classList.add('active');
}

// Function to hide assign popup
function hideAssignPopup() {
    assignPopup.classList.remove('active');
    currentTaskId = null;
    currentTaskText = null;
}

// Function to assign task to user
function assignTaskToUser(taskId, userId, userName) {
    const requestData = {
        user_id: userId || null
    };
    
    fetch(`/tasks/${taskId}/assign/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update the task display immediately
            updateTaskAssignmentDisplay(taskId, userId, userName);
            
            // Hide popup
            hideAssignPopup();
            
            // Show notification if available
            if (window.showNotification) {
                if (userId) {
                    window.showNotification('Task assigned successfully!', 'success');
                } else {
                    window.showNotification('Task unassigned successfully!', 'success');
                }
            }
        }
    })
    .catch(error => {
        if (window.showNotification) {
            window.showNotification('Error assigning task', 'error');
        }
    });
}

// Initialize team functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Load team members data
    try {
        const teamDataElement = document.getElementById('team-members-data');
        if (teamDataElement) {
            teamMembers = JSON.parse(teamDataElement.textContent);
        }
    } catch (error) {
        teamMembers = [];
    }
    
    // Initialize popup element
    assignPopup = document.getElementById('assign-task-popup');
    if (!assignPopup) {
        return;
    }
    
    // Handle assign task button clicks
    document.addEventListener('click', function(e) {
        const assignBtn = e.target.closest('.assign-task-btn');
        if (assignBtn) {
            e.preventDefault();
            e.stopPropagation();
            const taskId = assignBtn.dataset.taskId;
            const taskText = assignBtn.dataset.taskText;
            const currentAssignedTo = assignBtn.dataset.assignedTo;
            showAssignPopup(assignBtn, taskId, taskText, currentAssignedTo);
        } else if (!e.target.closest('#assign-task-popup')) {
            // Click outside popup - hide it
            hideAssignPopup();
        }
    });
    
    // Ensure assign buttons work for dynamically added tasks
    document.addEventListener('htmx:afterSwap', function(e) {
        // Check if new task elements were added
        const taskElements = e.detail.target.querySelectorAll('[data-task-id]');
        if (taskElements.length > 0) {
            // Ensure assign buttons are properly initialized
            const assignButtons = e.detail.target.querySelectorAll('.assign-task-btn');
            assignButtons.forEach(button => {
                // Force re-initialization of hover effects
                const icon = button.querySelector('i');
                if (icon) {
                    // Ensure the icon has the proper classes
                    icon.className = 'fas fa-user text-gray-400 hover:text-orange-500 text-xs transition-colors';
                }
            });
        }
    });
});
