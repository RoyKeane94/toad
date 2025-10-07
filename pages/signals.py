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
            "Your Turn!"
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
            # Row 1: Your First Five Minutes
            (0, 0, "✅ Welcome! Click the checkbox to complete your first task.", False),
            (0, 0, "✏️ Now, click on this text to edit it to something else.", False),
            (0, 0, "👇 Click 'Add Task' below to add a real task you have.", False),

            # Row 2: Make it Your Own
            (1, 0, "Let's expand. Add a new column to your right called 'In Progress'.", False),
            (1, 0, "Feeling organised? Hit 'Clear Completed' to tidy up checked-off tasks.", False),
            (1, 0, "This tutorial grid is just the start. You can delete it anytime.", True),

            # Row 3: Your Turn!
            (2, 0, "🔥 Your Mission: Create your first real grid.", False),
            (2, 0, "Click on 'New Grid' to create your own grid from scratch or leverage a template like 'Weekly Planner' or 'Product Development Tracker'.", False),
            (2, 0, "We're a small team building a simple tool. Ideas? Issues? Email tom@meettoad.co.uk", True),
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


def create_habit_development_tracker_grid(user):
    """
    Create a Habit Development Tracker grid with predefined rows and columns for the given user.
    Based on the Habit Development Tracker structure with days of the week and habit categories.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Habit Development Tracker"
    )
    
    # Create row headers (habit categories)
    row_headers = [
        "Morning Upgrades",
        "Evening Upgrades", 
        "Swaps",
        "Daily Victory"
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
    
    # Create tasks based on the Habit Development Tracker image
    tasks_data = [
        # Morning Upgrades row
        (0, 0, "Morning sunlight upon waking", False),  # Monday
        (0, 0, "Morning exercise", False),  # Monday
        (0, 1, "Morning exercise", False),  # Tuesday
        (0, 1, "Morning sunlight upon waking", False),  # Tuesday
        (0, 2, "Morning sunlight upon waking", False),  # Wednesday
        (0, 2, "Morning exercise", False),  # Wednesday
        
        # Evening Upgrades row
        (1, 0, "Go to bed by 10:30", False),  # Monday
        (1, 0, "Read for 30 minutes before bed", False),  # Monday
        (1, 1, "Go to bed by 10:30", False),  # Tuesday
        (1, 1, "Read for 30 minutes before bed", False),  # Tuesday
        (1, 2, "Go to bed by 10:30", False),  # Wednesday
        (1, 2, "Read for 30 minutes before bed", False),  # Wednesday
        
        # Swaps row
        (2, 0, "Don't look at phone for an hour post waking", False),  # Monday
        (2, 1, "Don't look at phone for an hour post waking", False),  # Tuesday
        (2, 2, "Don't look at phone for an hour post waking", False),  # Wednesday
        
        # Daily Victory row
        (3, 0, "Went to the loo without my phone", False),  # Monday
        (3, 1, "Chose to walk 30 minutes to work without headphones", False),  # Tuesday
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


def create_habit_development_tracker_grid_structure_only(user):
    """
    Create a Habit Development Tracker grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Habit Development Tracker"
    )
    
    # Create row headers
    row_headers = [
        "Morning Upgrades",
        "Evening Upgrades", 
        "Swaps",
        "Daily Victory"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers - include all days of the week
    column_headers = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
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

def create_product_development_tracker_grid(user):
    """
    Create a Product Development Tracker grid with predefined rows and columns for the given user.
    Based on the Product Development Tracker structure with phases and development areas.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Product Development Tracker"
    )
    
    # Create row headers (phases)
    row_headers = [
        "Phase 1: Planning and Design",
        "Phase 2: Core Build", 
        "Phase 3: Pre-Launch Polish",
        "Phase 4: Launch and Feedback"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (development areas)
    column_headers = [
        "Product and Design",
        "Development (Frontend)",
        "Development (Backend)",
        "Marketing and User Outreach"
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
    
    # Create tasks based on the Product Development Tracker image
    tasks_data = [
        # Phase 1: Planning and Design
        (0, 0, "Create user flow diagram", False),  # Product and Design
        (0, 0, "Design the main grid", False),  # Product and Design
        (0, 0, "Design the pricing page", False),  # Product and Design
        (0, 1, "Set up the basic Django project structure", False),  # Development (Frontend)
        (0, 2, "Design the initial database schema", False),  # Development (Backend)
        (0, 2, "Set up the database on Railway", False),  # Development (Backend)
        
        # Phase 2: Core Build
        (1, 0, "Finalise the 'Welcome Grid' content", False),  # Product and Design
        (1, 1, "Build the main grid view", False),  # Development (Frontend)
        (1, 1, "Ensure all buttons are consistently styled with Tailwind", False),  # Development (Frontend)
        (1, 2, "Build the user registration flow", False),  # Development (Backend)
        (1, 2, "Separate specific Django views into new files to improve readability", False),  # Development (Backend)
        (1, 2, "Add the template grids into Signals", False),  # Development (Backend)
        
        # Phase 3: Pre-Launch Polish
        (2, 0, "Review the FAQ Page", False),  # Product and Design
        (2, 0, "Look at adding a third column to make it more vibrant", False),  # Product and Design
        (2, 1, "Review JavaScript to ensure fully optimised", False),  # Development (Frontend)
        (2, 1, "Minify CSS and Javascript", False),  # Development (Frontend)
        (2, 2, "Integrate stripe for payments", False),  # Development (Backend)
        (2, 2, "Run Lighthouse on Chrome and implement feedback", False),  # Development (Backend)
        
        # Phase 4: Launch and Feedback
        (3, 0, "Pull together a list of user comments to review", False),  # Product and Design
        (3, 1, "Once reviewed, implement select user feedback", False),  # Development (Frontend)
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

def create_solopreneur_grid(user):
    """
    Create a Solopreneur grid with predefined rows and columns for the given user.
    Based on the Solopreneur structure with client work and business areas.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Solopreneur"
    )
    
    # Create row headers (client/business areas)
    row_headers = [
        "Client A: Smith & Jones Website",
        "Client B - Downton Limited",
        "Sales & Marketing",
        "Admin & Finance"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (time-based priorities)
    column_headers = [
        "This week's priorities",
        "To Do Today",
        "Waiting On / Blockers"
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
    
    # Create tasks based on the Solopreneur image
    tasks_data = [
        # Client A: Smith & Jones Website
        (0, 0, "Finish the homepage design mock-up", False),  # This week's priorities
        (0, 0, "Prepare for the weekly check-in call", False),  # This week's priorities
        (0, 1, "Send revised logo files to the client", False),  # To Do Today
        (0, 2, "Waiting for client to provide the final copy for the 'About Us' page", False),  # Waiting On / Blockers
        
        # Client B - Downton Limited
        (1, 0, "Finalise brand colour palette", False),  # This week's priorities
        (1, 1, "Draft three initial logo concepts", False),  # To Do Today
        
        # Sales & Marketing
        (2, 0, "Follow up on Umbrella Limited post discussion on the 12th", False),  # This week's priorities
        (2, 0, "Follow up on Hunt Limited post discussion on the 15th", False),  # This week's priorities
        (2, 1, "Send final proposal to Book Limited", False),  # To Do Today
        (2, 2, "Waiting for a reply from the podcast host I pitched", False),  # Waiting On / Blockers
        
        # Admin & Finance
        (3, 0, "Send out all outstanding invoices for September", False),  # This week's priorities
        (3, 0, "Categorise business expenses for August", False),  # This week's priorities
        (3, 1, "Chase the invoice from Stephens Limited", False),  # To Do Today
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

def create_weekly_planner_grid(user):
    """
    Create a Weekly Planner grid with predefined rows and columns for the given user.
    Based on the Weekly Planner Grid structure with days of the week and Admin/Meetings/Tasks rows.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Weekly Planner"
    )
    
    # Create row headers (weekly categories)
    row_headers = [
        "Admin",
        "Meetings", 
        "Tasks",
        "Waiting On / Follow Up"
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
    
    # Create tasks based on the Weekly Planner Grid image
    tasks_data = [
        # Admin row
        (0, 0, "Submit expenses for June", False),  # Monday
        (0, 0, "Book travel and hotel for trip to Doncaster next week", False),  # Monday
        (0, 1, "Ring dentist", False),  # Tuesday
        
        # Meetings row
        (1, 0, "10:00 - Catch up with James re Project Pearl", False),  # Monday
        (1, 0, "14:00 - Discuss external comms on Project Soft with Susie", False),  # Monday
        (1, 0, "16:30 - Intro call with diligence providers on Project Pearl", False),  # Monday
        (1, 1, "12:30 - Lunch with Olivia", False),  # Tuesday
        (1, 1, "14:00 - Management meeting on Project Coral", False),  # Tuesday
        (1, 2, "9:30 - Project Coral team meeting to discuss thoughts", False),  # Wednesday
        
        # Tasks row
        (2, 0, "Write up notes on Project Pearl and circulate", False),  # Monday
        (2, 0, "Draft external comms for Project Soft", False),  # Monday
        (2, 1, "Prepare Project Coral thoughts", False),  # Tuesday
        (2, 2, "Get final sign off on Project Soft comms", False),  # Wednesday
        (2, 2, "Share Project Soft comms to LinkedIn", False),  # Wednesday

        # Waiting On / Follow Up row
        (3, 0, "Trading update from Project Coral", False),  # Monday
        (3, 1, "Olivia sharing team overview page", False),  # Tuesday
        
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


def create_sell_side_project_grid(user):
    """
    Create a Sell Side Project grid with predefined rows and columns for the given user.
    Based on the Sell-Side Deal Grid structure.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Sell Side Project"
    )
    
    # Create row headers (project phases)
    row_headers = [
        "Initial Pitch & Analysis",
        "Marketing & Due Diligence",
        "Exclusivity & Legals"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (functional areas)
    column_headers = [
        "Project Management & Comms",
        "Preparation & Marketing",
        "Financial Modelling & Valuation",
        "Due Diligence & Legal"
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
    
    # Create tasks based on the Sell-Side Deal Grid image
    tasks_data = [
        # Row 1: Initial Pitch & Analysis
        (0, 0, "Set up internal deal team folder", False),  # Project Management & Comms
        (0, 0, "Schedule internal kick off call", False),  # Project Management & Comms
        (0, 0, "Pull together timeline", False),  # Project Management & Comms
        (0, 1, "Conduct preliminary buyer market research", False),  # Preparation & Marketing
        (0, 1, "Prepare initial pitch book for client", False),  # Preparation & Marketing
        (0, 1, "Identify buyer long list", False),  # Preparation & Marketing
        (0, 2, "Build initial financial model of the target company", False),  # Financial Modelling & Valuation
        (0, 2, "Perform a preliminary valuation (DCF, Comps, LBO)", False),  # Financial Modelling & Valuation
        (0, 3, "Client onboarding", False),  # Due Diligence & Legal
        (0, 3, "Draft engagement letter for the client", False),  # Due Diligence & Legal
        (0, 3, "Sign engagement letter with the client", False),  # Due Diligence & Legal
        (0, 3, "Get quotes from due diligence providers", False),  # Due Diligence & Legal
        (0, 3, "Choose due diligence providers across legal, commercial and financial", False),  # Due Diligence & Legal
        
        # Row 2: Marketing & Due Diligence
        (1, 0, "Schedule weekly client calls", False),  # Project Management & Comms
        (1, 0, "Track weekly progress against timeline", False),  # Project Management & Comms
        (1, 0, "Set up Q&A process", False),  # Project Management & Comms
        (1, 1, "Draft the teaser", False),  # Preparation & Marketing
        (1, 1, "Draft the IM", False),  # Preparation & Marketing
        (1, 1, "Contact potential buyers with the teaser", False),  # Preparation & Marketing
        (1, 1, "Share the IM with those buyers who have signed an NDA", False),  # Preparation & Marketing
        (1, 2, "Refine the financial model with new data", False),  # Financial Modelling & Valuation
        (1, 2, "Prepare a detailed valuation analysis", False),  # Financial Modelling & Valuation
        (1, 2, "Update the valuation based on first-round bids", False),  # Financial Modelling & Valuation
        (1, 3, "Finalise NDAs with potential buyers", False),  # Due Diligence & Legal
        (1, 3, "Populate VDR with initial diligence documents", False),  # Due Diligence & Legal
        (1, 3, "Facilitate legal, commercial and financial due diligence", False),  # Due Diligence & Legal
        
        # Row 3: Exclusivity & Legals
        (2, 0, "Set up weekly all parties calls if relevant", False),  # Project Management & Comms
        (2, 2, "Update model for latest trading", False),  # Financial Modelling & Valuation
        (2, 2, "Share trading update", False),  # Financial Modelling & Valuation
        (2, 3, "Instruct lawyers to draft the SPA", False),  # Due Diligence & Legal
        (2, 3, "Set up weekly legal calls", False),  # Due Diligence & Legal
        (2, 3, "Finalise SPA", False),  # Due Diligence & Legal
        (2, 3, "W&I", False),  # Due Diligence & Legal
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

def create_origination_director_grid(user):
    """
    Create an Origination Director grid with predefined rows and columns for the given user.
    Based on the Origination Grid structure with days of the week and Admin/Meetings/Tasks/Pitches rows.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Origination Director"
    )
    
    # Create row headers (origination categories)
    row_headers = [
        "Admin",
        "Meetings", 
        "Tasks",
        "Pitches"
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
    
    # Create sample tasks for each row
    tasks_data = [
        # Admin row
        (0, 0, "Review weekly origination pipeline", False),  # Monday
        (0, 1, "Update deal tracking spreadsheet", False),  # Tuesday
        (0, 2, "Prepare weekly origination report", False),  # Wednesday
        (0, 3, "Schedule team origination meeting", False),  # Thursday
        (0, 4, "Review weekend deal opportunities", False),  # Friday
        
        # Meetings row
        (1, 0, "09:00 - Weekly origination team standup", False),  # Monday
        (1, 0, "14:00 - Client pitch meeting - Project Alpha", False),  # Monday
        (1, 1, "10:00 - Sector team origination review", False),  # Tuesday
        (1, 1, "15:00 - External advisor catch-up", False),  # Tuesday
        (1, 2, "11:00 - Deal flow review with partners", False),  # Wednesday
        (1, 3, "13:00 - Origination strategy planning", False),  # Thursday
        (1, 4, "16:00 - Friday wrap-up call", False),  # Friday
        
        # Tasks row
        (2, 0, "Research new market opportunities", False),  # Monday
        (2, 0, "Draft initial pitch materials", False),  # Monday
        (2, 1, "Follow up on previous week's leads", False),  # Tuesday
        (2, 1, "Prepare sector analysis for meetings", False),  # Tuesday
        (2, 2, "Update deal pipeline database", False),  # Wednesday
        (2, 2, "Review competitor activity", False),  # Wednesday
        (2, 3, "Prepare origination metrics", False),  # Thursday
        (2, 3, "Coordinate with legal team on NDAs", False),  # Thursday
        (2, 4, "Plan next week's origination focus", False),  # Friday
        
        # Pitches row
        (3, 0, "Finalize Project Alpha pitch deck", False),  # Monday
        (3, 1, "Prepare Project Beta initial approach", False),  # Tuesday
        (3, 2, "Review Project Gamma pitch materials", False),  # Wednesday
        (3, 3, "Update Project Delta pitch strategy", False),  # Thursday
        (3, 4, "Plan Project Echo pitch approach", False),  # Friday
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

def create_course_planner_grid_structure_only(user):
    """
    Create a Course Planner grid structure only (no tasks) for the given user.
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
    
    # Create column headers - include all columns like the full template
    column_headers = [
        "Module 1",
        "Module 2",
        "Module 3",
        "Module 4"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project

def create_revision_guide_grid_structure_only(user):
    """
    Create a Revision Guide grid structure only (no tasks) for the given user.
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
    
    # Create column headers - include all columns like the full template
    column_headers = [
        "Module 1",
        "Module 2",
        "Module 3",
        "Module 4"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project


def create_essay_planner_grid_structure_only(user):
    """
    Create an Essay Planner grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Essay Planner"
    )
    
    # Create row headers
    row_headers = [
        "Research",
        "Planning", 
        "Writing",
        "Review"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers - include all columns like the full template
    column_headers = [
        "Core Tasks",
        "Sources & Reading",
        "Key Arguments",
        "Admin & Deadlines"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project


def create_job_application_tracker_grid_structure_only(user):
    """
    Create a Job Application Tracker grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Job Application Tracker"
    )
    
    # Create row headers
    row_headers = [
        "Research",
        "Application", 
        "Follow-up",
        "Interview Prep"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers - include all columns like the full template
    column_headers = [
        "Company",
        "Company 2",
        "Company 3",
        "Company 4"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project


def create_weekly_planner_grid_structure_only(user):
    """
    Create a Weekly Planner grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Weekly Planner"
    )
    
    # Create row headers
    row_headers = [
        "Admin",
        "Meetings", 
        "Tasks",
        "Waiting On / Follow Up",
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers - include all columns like the full template
    column_headers = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project

def create_line_manager_grid_structure_only(user):
    """
    Create a Line Manager grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Team Management Grid"
    )
    
    # Create row headers
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
    
    # Create column headers - include all columns like the full template
    column_headers = [
        "Team",
        "Employee 1",
        "Employee 2",
        "Employee 3",
        "Employee 4"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project

def create_sell_side_project_grid_structure_only(user):
    """
    Create a Sell Side Project grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Sell Side Project"
    )
    
    # Create row headers
    row_headers = [
        "Initial Pitch & Analysis",
        "Marketing & Due Diligence",
        "Exclusivity & Legals"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers - include all columns like the full template
    column_headers = [
        "Project Management & Comms",
        "Preparation & Marketing",
        "Financial Modelling & Valuation",
        "Due Diligence & Legal"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project

def create_origination_director_grid_structure_only(user):
    """
    Create an Origination Director grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Origination Director"
    )
    
    # Create row headers
    row_headers = [
        "Admin",
        "Meetings", 
        "Tasks",
        "Pitches"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers - include all columns like the full template
    column_headers = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project

def create_product_development_tracker_grid_structure_only(user):
    """
    Create a Product Development Tracker grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Product Development Tracker"
    )
    
    # Create row headers
    row_headers = [
        "Phase 1: Planning and Design",
        "Phase 2: Core Build", 
        "Phase 3: Pre-Launch Polish",
        "Phase 4: Launch and Feedback"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers - include all columns like the full template
    column_headers = [
        "Product and Design",
        "Development (Frontend)",
        "Development (Backend)",
        "Marketing and User Outreach"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project

def create_solopreneur_grid_structure_only(user):
    """
    Create a Solopreneur grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Solopreneur"
    )
    
    # Create row headers
    row_headers = [
        "Client A: Smith & Jones Website",
        "Client B - Downton Limited",
        "Sales & Marketing",
        "Admin & Finance"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers
    column_headers = [
        "This week's priorities",
        "To Do Today",
        "Waiting On / Blockers"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project

def create_weekly_fitness_tracker_grid(user):
    """
    Create a Weekly Fitness Tracker grid with predefined rows and columns for the given user.
    Based on the Weekly Fitness Tracker structure with days of the week and fitness categories.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Weekly Fitness Tracker"
    )
    
    # Create row headers (fitness categories)
    row_headers = [
        "Cardio",
        "Weights", 
        "Recovery"
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
    
    # Create tasks based on the Weekly Fitness Tracker image
    tasks_data = [
        # Cardio row
        (0, 0, "Training plan (3/14) - 5km at conversational pace before work", False),  # Monday
        (0, 1, "Training plan (3/14) - 8km at 5:20 per k/m running home", False),  # Tuesday
        (0, 2, "Cycling", False),  # Wednesday
        (0, 2, "Get off tube one stop early to get in a 45 minute evening walk", False),  # Wednesday
        
        # Weights row
        (1, 0, "45 minutes - arms and chest workout before work", False),  # Monday
        (1, 2, "45 minutes - leg workout pre work", False),  # Wednesday
        
        # Recovery row
        (2, 0, "Evening stretches - 15 minutes", False),  # Monday
        (2, 0, "Evening ice bath", False),  # Monday
        (2, 1, "Morning Sauna", False),  # Tuesday
        (2, 1, "Evening ice bath", False),  # Tuesday
        (2, 1, "Evening stretches - 15 minutes", False),  # Tuesday
        (2, 2, "Morning Sauna", False),  # Wednesday
        (2, 2, "Evening stretches - 15 minutes", False),  # Wednesday
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


def create_weekly_fitness_tracker_grid_structure_only(user):
    """
    Create a Weekly Fitness Tracker grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Weekly Fitness Tracker"
    )
    
    # Create row headers
    row_headers = [
        "Cardio",
        "Weights", 
        "Recovery"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers - include all days of the week
    column_headers = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project


def create_alternative_weekly_planner_grid(user):
    """
    Create an Alternative Weekly Planner grid with predefined rows and columns for the given user.
    Based on the Alternative Weekly Planner structure with Weekly Priorities and To Do Today columns.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Alternative Weekly Planner"
    )
    
    # Create row headers (project categories)
    row_headers = [
        "Admin",
        "Project Pearl",
        "Project Coral"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (Weekly Priorities and To Do Today)
    column_headers = [
        "Weekly Priorities",
        "To Do Today"
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
    
    # Create sample tasks based on the Alternative Weekly Planner structure
    tasks_data = [
        # Admin row - Weekly Priorities
        (0, 0, "Submit expenses", False),
        
        # Admin row - To Do Today  
        (0, 1, "Buy birthday card for Mum", False),
        
        # Project Pearl row - Weekly Priorities
        (1, 0, "Finalise resourcing", False),
        (1, 0, "Draft the client proposal", False),
        
        # Project Pearl row - To Do Today
        (1, 1, "Write up notes from team catch up and circulate", False),
        
        # Project Coral row - Weekly Priorities
        (2, 0, "Get final sign off on comms plan", False),
        (2, 0, "Write internal thought piece on project", False),
        
        # Project Coral row - To Do Today
        (2, 1, "Handover to Steve for my holiday next week", False),
    ]
    
    # Create all tasks
    for row_idx, col_idx, task_text, completed in tasks_data:
        Task.objects.create(
            project=project,
            row_header=row_objects[row_idx],
            column_header=col_objects[col_idx],
            text=task_text,
            completed=completed,
            order=0  # Will be updated by the bulk creation logic
        )
    
    return project

def create_alternative_weekly_planner_grid_structure_only(user):
    """
    Create an Alternative Weekly Planner grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Alternative Weekly Planner"
    )
    
    # Create row headers
    row_headers = [
        "Admin",
        "Project Pearl",
        "Project Coral"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers
    column_headers = [
        "Weekly Priorities",
        "To Do Today"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project


def create_coffee_shop_tracker_grid(user):
    """
    Create a Coffee Shop Tracker grid with predefined rows and columns for the given user.
    Based on the Coffee Shop Tracker structure with time-based rows and operational area columns.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Coffee Shop Tracker"
    )
    
    # Create row headers (time-based priorities)
    row_headers = [
        "To Do Today",
        "Weekly Priorities",
        "Projects"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (operational areas)
    column_headers = [
        "Admin",
        "Customers",
        "Product"
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
    
    # Create tasks based on the Coffee Shop Tracker image
    tasks_data = [
        # To Do Today row
        (0, 0, "Post job advert on Indeed", False),  # Admin
        (0, 1, "Design and print new WiFi password sign", False),  # Customers
        (0, 1, "Upload a new Instagram post introducing our new Barista", False),  # Customers
        (0, 2, "Replace broken mug", True),  # Product (completed)
        
        # Weekly Priorities row
        (1, 0, "Quarterly deep clean of the espresso machine", False),  # Admin
        (1, 1, "Respond to new Google reviews", False),  # Customers
        (1, 1, "Fix the wobbly table by the window", False),  # Customers
        (1, 2, "Finalise the cost out of the new Winter drinks menu", False),  # Product
        (1, 2, "Get quotes from two alternative oat milk suppliers", False),  # Product
        
        # Projects row
        (2, 0, "Sign off on Q3 accounts", True),  # Admin (completed)
        (2, 0, "Share Q3 accounts with accountant", False),  # Admin
        (2, 1, "Plan budget for Christmas marketing campaign", False),  # Customers
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


def create_coffee_shop_tracker_grid_structure_only(user):
    """
    Create a Coffee Shop Tracker grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Coffee Shop Tracker"
    )
    
    # Create row headers (time-based priorities)
    row_headers = [
        "To Do Today",
        "Weekly Priorities",
        "Projects"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (operational areas)
    column_headers = [
        "Admin",
        "Customers",
        "Product"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project


def create_content_creator_tracker_grid(user):
    """
    Create a Content Creator Tracker grid with predefined rows and columns for the given user.
    Based on the Content Creator Tracker structure with time-based rows and operational area columns.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Content Creator Tracker"
    )
    
    # Create row headers (time-based priorities)
    row_headers = [
        "To Do Today",
        "Weekly Priorities",
        "Projects"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (content areas)
    column_headers = [
        "Admin",
        "Content",
        "Collaborations"
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
    
    # Create tasks based on the Content Creator Tracker image
    tasks_data = [
        # To Do Today row
        (0, 0, "Clear email inbox", False),  # Admin
        (0, 1, "Respond to comments on latest Instagram Reel", False),  # Content
        (0, 1, "Schedule tomorrow's story", False),  # Content
        (0, 1, "Research trending topics for YouTube shorts", False),  # Content
        (0, 2, "Send follow up email to Daylesford", False),  # Collaborations
        (0, 2, "Draft pitch for Dyptique product collaboration", False),  # Collaborations
        
        # Weekly Priorities row
        (1, 0, "Submit Q2 accounts to accountant", False),  # Admin
        (1, 1, "Batch create 3 new reels for next week", False),  # Content
        (1, 1, "Plan grid posts for next 7 days", False),  # Content
        (1, 1, "Analyse reel interaction", False),  # Content
        (1, 1, "Outline script for next YouTube video", False),  # Content
        (1, 2, "Finalise contract with Sheer Luxe", False),  # Collaborations
        (1, 2, "Source products for upcoming unboxing video", False),  # Collaborations
        
        # Projects row
        (2, 0, "Update website for new media forms", False),  # Admin
        (2, 0, "Research new monetisation strategies", False),  # Admin
        (2, 1, "Plan a 6 part deep dive series for YouTube", False),  # Content
        (2, 1, "Research new camera equipment", False),  # Content
        (2, 2, "Create an \"About Me\" pitch deck", False),  # Collaborations
        (2, 2, "Create system for tracking collaboration ROI", False),  # Collaborations
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


def create_content_creator_tracker_grid_structure_only(user):
    """
    Create a Content Creator Tracker grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Content Creator Tracker"
    )
    
    # Create row headers (time-based priorities)
    row_headers = [
        "To Do Today",
        "Weekly Priorities",
        "Projects"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (content areas)
    column_headers = [
        "Admin",
        "Content",
        "Collaborations"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project


def create_interior_designer_tracker_grid(user):
    """
    Create an Interior Designer Tracker grid with predefined rows and columns for the given user.
    Based on the Interior Designer Tracker structure with project phases as rows and stakeholder columns.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Interior Designer Tracker"
    )
    
    # Create row headers (project phases)
    row_headers = [
        "Discovery and planning",
        "Design",
        "Procurement"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (stakeholder areas)
    column_headers = [
        "Client",
        "Suppliers",
        "Key deliverables"
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
    
    # Create tasks based on the Interior Designer Tracker image
    tasks_data = [
        # Discovery and planning row
        (0, 0, "Initial meeting on 3rd October", True),  # Client (completed)
        (0, 0, "Discuss scope of working including style likes and budget", False),  # Client
        (0, 0, "Get key measurements", False),  # Client
        (0, 1, "Speak to suppliers to come up with ideas", False),  # Suppliers
        (0, 1, "Contact decorators for quotes on wallpapering", False),  # Suppliers
        (0, 2, "Signed contract", False),  # Key deliverables
        (0, 2, "Initial design brief", False),  # Key deliverables
        (0, 2, "Client questionnaire", False),  # Key deliverables
        (0, 2, "Agree a timeline", False),  # Key deliverables
        
        # Design row
        (1, 0, "Pull together mood board to discuss", False),  # Client
        (1, 0, "Sketching to present to clients", False),  # Client
        (1, 0, "Share and discuss furniture options with client", False),  # Client
        (1, 1, "Get supplier product availability for wallpaper", False),  # Suppliers
        (1, 1, "Pull together options for bed", False),  # Suppliers
        (1, 1, "Pull together options for dressing table", False),  # Suppliers
        (1, 1, "Pull together options for carpet", False),  # Suppliers
        (1, 2, "Finalise design drawings with client", False),  # Key deliverables
        (1, 2, "Finalise furniture purchases with client", False),  # Key deliverables
        
        # Procurement row
        (2, 0, "Agree deliveries with client", False),  # Client
        (2, 0, "Agree decorator with client", False),  # Client
        (2, 1, "Speak to suppliers re agreed client purchase list", False),  # Suppliers
        (2, 1, "Inform client of any timeline issues with suppliers", False),  # Suppliers
        (2, 2, "Vendor confirmations", False),  # Key deliverables
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


def create_interior_designer_tracker_grid_structure_only(user):
    """
    Create an Interior Designer Tracker grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Interior Designer Tracker"
    )
    
    # Create row headers (project phases)
    row_headers = [
        "Discovery and planning",
        "Design",
        "Procurement"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (stakeholder areas)
    column_headers = [
        "Client",
        "Suppliers",
        "Key deliverables"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project


def create_online_store_tracker_grid(user):
    """
    Create an Online Store Tracker grid with predefined rows and columns for the given user.
    Based on the Online Store Tracker structure with time-based rows and operational area columns.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Online Store Tracker"
    )
    
    # Create row headers (time-based priorities)
    row_headers = [
        "To Do Today",
        "Weekly Priorities",
        "Projects"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (operational areas)
    column_headers = [
        "Admin",
        "Product Development",
        "Clients and Marketing"
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
    
    # Create tasks based on the Online Store Tracker image
    tasks_data = [
        # To Do Today row
        (0, 0, "Update website banner for autumn sale", False),  # Admin
        (0, 1, "Finalise designs for Spring collection", False),  # Product Development
        (0, 1, "Write description for Spring collection", False),  # Product Development
        (0, 2, "Respond to all customer DMs and emails", False),  # Clients and Marketing
        (0, 2, "Pack and ship all outstanding orders", False),  # Clients and Marketing
        
        # Weekly Priorities row
        (1, 0, "Conduct stock check", False),  # Admin
        (1, 0, "Send Q2 accounts to accountant", False),  # Admin
        (1, 1, "Winter collection photoshoot", False),  # Product Development
        (1, 2, "Schedule 3 social media posts for next week", False),  # Clients and Marketing
        (1, 2, "Send \"Thank You\" email to new customers", False),  # Clients and Marketing
        
        # Projects row
        (2, 0, "Migrate store to Shopify", False),  # Admin
        (2, 0, "Prepare relevant documents for end of year tax filing", False),  # Admin
        (2, 1, "Plan product release for Spring collection", False),  # Product Development
        (2, 1, "Look into more sustainable packaging solutions", False),  # Product Development
        (2, 2, "Plan and budget Black Friday marketing campaign", False),  # Clients and Marketing
        (2, 2, "Set up an automated email sequence for abandoned carts", False),  # Clients and Marketing
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


def create_online_store_tracker_grid_structure_only(user):
    """
    Create an Online Store Tracker grid structure only (no tasks) for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Online Store Tracker"
    )
    
    # Create row headers (time-based priorities)
    row_headers = [
        "To Do Today",
        "Weekly Priorities",
        "Projects"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers (operational areas)
    column_headers = [
        "Admin",
        "Product Development",
        "Clients and Marketing"
    ]
    
    for order, col_name in enumerate(column_headers):
        ColumnHeader.objects.create(
            project=project,
            name=col_name,
            order=order,
            is_category_column=False
        )
    
    return project


