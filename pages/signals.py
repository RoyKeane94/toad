from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from .models import Project, RowHeader, ColumnHeader, Task


@receiver(post_save, sender=User)
def create_first_grid(sender, instance, created, **kwargs):
    """
    Create a '[FirstName]'s First Grid' project with predefined rows and columns 
    when a new user is created.
    """
    if created:  # Only run for newly created users
        # Create the project
        project = Project.objects.create(
            user=instance,
            name=f"{instance.first_name}'s First Grid"
        )
        
        # Create row headers
        row_headers = [
            "The Basics",
            "Make It Your Own", 
            "Your Beta Account"
        ]
        
        for order, row_name in enumerate(row_headers):
            RowHeader.objects.create(
                project=project,
                name=row_name,
                order=order
            )
        
        # Create column headers
        column_headers = [
            "Getting Started",
        ]
        
        col_objects = []
        for order, col_name in enumerate(column_headers):
            col_obj = ColumnHeader.objects.create(
                project=project,
                name=col_name,
                order=order,
                is_category_column=False  # None of these are category columns
            )
            col_objects.append(col_obj)
        
        # Create row objects list for easy reference
        row_objects = list(RowHeader.objects.filter(project=project).order_by('order'))
        
        # Create predefined tasks
        tasks_data = [
            # The Basics row
            (0, 0, "This is a task. You can check it off", False),
            (0, 0, "Easily add a new task by clicking 'Add Task'", False),
            (0, 0, "Tidy your grid by clicking 'Clear Completed' to remove all completed tasks", False),
            (0, 0, "If you're on desktop, you can drag and drop tasks to reorder them", False),
            
            # Make It Your Own row
            (1, 0, "Make your grid your own by adding your own columns and rows", False),
            (1, 0, "Pick a template for your first grid using Templates or create your own grid by clicking Grids", False),
            (1, 0, "Tailor a grid to start planning your week better, find your next job or organise your holiday", False),
            
            # Your Beta Account row
            (2, 0, "We have built Toad to be simple and fast", True),
            (2, 0, "As a Beta user, you have a free Toad Pro plan for life, meaning no limit on grids and the ability to create your own templates", False),
            (2, 0, "Please reach out any time with issues or ideas to tom@meettoad.co.uk", False),
        ]
        
        # Create all tasks
        for row_idx, col_idx, task_text, completed in tasks_data:
            Task.objects.create(
                project=project,
                row_header=row_objects[row_idx],
                column_header=col_objects[col_idx],
                text=task_text,
                completed=completed
            )


def create_course_planner_grid(user):
    """
    Create a Course Planner grid with predefined rows and columns for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Course Planner"
    )
    
    # Create row headers
    row_headers = [
        "Admin",
        "Weekly Tasks and Reading", 
        "Assignments and Coursework",
        "Exam Prep"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (assuming you want to rename "Module" to "Subject" - please confirm)
    column_headers = [
        "Subject",  # Renamed from "Module"
    ]
    
    col_objects = []
    for order, col_name in enumerate(column_headers):
        col_obj = ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
        col_objects.append(col_obj)
    
    # Create row objects list for easy reference
    row_objects = list(RowHeader.objects.filter(project=project).order_by('order'))
    
    # Create sample tasks for each row
    tasks_data = [
        # Admin row
        (0, 0, "Add your course modules/subjects", False),
        (0, 0, "Update your timetable", False),
        (0, 0, "Check important dates and deadlines", False),
        
        # Weekly Tasks and Reading row
        (1, 0, "Complete weekly readings", False),
        (1, 0, "Attend all lectures and seminars", False),
        (1, 0, "Take notes and review material", False),
        
        # Assignments and Coursework row
        (2, 0, "Start assignments early", False),
        (2, 0, "Research and gather resources", False),
        (2, 0, "Submit assignments on time", False),
        
        # Exam Prep row
        (3, 0, "Create revision schedule", False),
        (3, 0, "Practice past exam papers", False),
        (3, 0, "Review key concepts and theories", False),
    ]
    
    # Create all tasks
    for row_idx, col_idx, task_text, completed in tasks_data:
        Task.objects.create(
            project=project,
            row_header=row_objects[row_idx],
            column_header=col_objects[col_idx],
            text=task_text,
            completed=completed
        )
    
    return project


def create_shooting_grid(user):
    """
    Create a Shooting grid with predefined rows and columns for the given user.
    Based on the shooting template structure with days of the week and Admin/Equipment/Practice rows.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Shooting Schedule"
    )
    
    # Create row headers (shooting categories)
    row_headers = [
        "Admin",
        "Equipment", 
        "Practice"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (days of the week)
    column_headers = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]
    
    col_objects = []
    for order, col_name in enumerate(column_headers):
        col_obj = ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
        col_objects.append(col_obj)
    
    # Create row objects list for easy reference
    row_objects = list(RowHeader.objects.filter(project=project).order_by('order'))
    
    # Create tasks based on the shooting template
    tasks_data = [
        # Admin row
        (0, 0, "Book in for Thimbleby tomorrow", False),  # Monday
        (0, 1, "Check Guns on Pegs for the Yearsley Shoot address for Saturday", False),  # Tuesday
        
        # Equipment row
        (1, 0, "Clean guns post weekend", False),  # Monday
        (1, 2, "Buy 200 cartridges for the weekend", False),  # Wednesday
        
        # Practice row
        (2, 0, "At home - 50 DTL high shots", False),  # Monday
        (2, 1, "Thimbleby Shooting", False),  # Tuesday
        (2, 2, "At home - 50 DTL low shots", False),  # Wednesday
    ]
    
    # Create all tasks
    for row_idx, col_idx, task_text, completed in tasks_data:
        Task.objects.create(
            project=project,
            row_header=row_objects[row_idx],
            column_header=col_objects[col_idx],
            text=task_text,
            completed=completed
        )
    
    return project


def create_line_manager_grid_signal(user):
    """
    Create a Line Manager grid with predefined rows and columns for the given user.
    Based on the Line Manager Picture.png structure.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Team Management Grid"
    )
    
    # Create row headers (project categories)
    row_headers = [
        "Admin",
        "Catch Ups", 
        "Project Thames",
        "Project Sun"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (team members)
    column_headers = [
        "Team",
        "Jake",
        "Lauren"
    ]
    
    col_objects = []
    for order, col_name in enumerate(column_headers):
        col_obj = ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
        col_objects.append(col_obj)
    
    # Create row objects list for easy reference
    row_objects = list(RowHeader.objects.filter(project=project).order_by('order'))
    
    # Create tasks based on the image provided
    tasks_data = [
        # Admin row
        (0, 0, "Organise summer drinks", False),  # Team
        (0, 1, "Sit down to give feedback on Project Jupiter", False),  # Jake
        (0, 2, "Approve annual leave", True),  # Lauren (completed)
        
        # Catch Ups row
        (1, 0, "Schedule September all team in-person catch up", False),  # Team
        (1, 1, "Schedule weekly catch up for w/c 18th August", False),  # Jake
        (1, 2, "Schedule weekly catch up for w/c 18th August", False),  # Lauren
        
        # Project Thames row
        (2, 0, "Final report deadline is 30th August", False),  # Team
        (2, 1, "Sit down to discuss team roles", True),  # Jake (completed)
        (2, 1, "Numbers to be agreed by 11th July", True),  # Jake (completed)
        (2, 1, "Touch base with Jake to ensure that he can still provide the final draft by 24th August", False),  # Jake
        (2, 2, "Prep agenda for internal stakeholder comms meeting", False),  # Lauren
        
        # Project Sun row
        (3, 0, "Check on team capacity for Project Sun", False),  # Team
    ]
    
    # Create all tasks
    for row_idx, col_idx, task_text, completed in tasks_data:
        Task.objects.create(
            project=project,
            row_header=row_objects[row_idx],
            column_header=col_objects[col_idx],
            text=task_text,
            completed=completed
        )
    
    return project


def create_revision_guide_grid(user):
    """
    Create a Revision Guide grid with predefined rows and columns for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Revision Guide"
    )
    
    # Create row headers
    row_headers = [
        "Review and Consolidate",
        "Active Recall and Memorisation", 
        "Practice and Application",
        "Final Review"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (renamed from "Module name" to "Subject")
    column_headers = [
        "Subject",  # Renamed from "Module name"
    ]
    
    col_objects = []
    for order, col_name in enumerate(column_headers):
        col_obj = ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
        col_objects.append(col_obj)
    
    # Create row objects list for easy reference
    row_objects = list(RowHeader.objects.filter(project=project).order_by('order'))
    
    # Create sample tasks for each row
    tasks_data = [
        # Review and Consolidate row
        (0, 0, "Go through all lecture notes", False),
        (0, 0, "Re-read key textbook chapters", False),
        (0, 0, "Create a summary 'Cheat Sheet' for the whole module", False),
        
        # Active Recall and Memorisation row
        (1, 0, "Create flashcards for key formulae and concepts", False),
        (1, 0, "Practice explaining key concepts out loud", False),
        
        # Practice and Application row
        (2, 0, "Find past paper questions", False),
        (2, 0, "Practice past paper questions in timed conditions", False),
        
        # Final Review row
        (3, 0, "Run through 'Cheat Sheet'", False),
    ]
    
    # Create all tasks
    for row_idx, col_idx, task_text, completed in tasks_data:
        Task.objects.create(
            project=project,
            row_header=row_objects[row_idx],
            column_header=col_objects[col_idx],
            text=task_text,
            completed=completed
        )
    
    return project
