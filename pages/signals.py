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
        "Tasks"
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
