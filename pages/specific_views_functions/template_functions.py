from ..models import Project, RowHeader, ColumnHeader, Task

# Essay Planner Grid

def create_essay_planner_grid(user):
    """
    Create an Essay Planner grid with predefined rows and columns for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Essay Planner"
    )
    
    # Create row headers
    row_headers = [
        "Research",
        "Outline", 
        "Writing",
        "Editing"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers
    column_headers = [
        "Core Tasks",
        "Sources & Reading",
        "Key Arguments",
        "Admin and Deadlines"
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
    
    # Create tasks based on the images provided
    tasks_data = [
        # Research row
        (0, 0, "Deconstruct essay questions", False),  # Core Tasks
        (0, 0, "Pull together a reading list and bibliography", False),  # Core Tasks
        (0, 1, "Find 5 relevant journal articles", False),  # Sources & Reading
        (0, 1, "Write notes on journal articles", False),  # Sources & Reading
        (0, 2, "Note down initial 3 - 4 core arguments", False),  # Key Arguments
        (0, 2, "Find counter arguments", False),  # Key Arguments
        (0, 3, "Find out final deadline for the essay", False),  # Admin and Deadlines
        
        # Outline row
        (1, 0, "Create a high-level outline", False),  # Core Tasks
        (1, 2, "Integrate core arguments into outline", False),  # Key Arguments
        (1, 3, "Get outline feedback from tutor by [x]", False),  # Admin and Deadlines
        
        # Writing row
        (2, 0, "Introduction", False),  # Core Tasks
        (2, 0, "Main body paragraphs", False),  # Core Tasks
        (2, 0, "Conclusion", False),  # Core Tasks
        (2, 3, "First draft completed by [x]", False),  # Admin and Deadlines
        
        # Editing row
        (3, 0, "Proofread for spelling and grammar errors", False),  # Core Tasks
        (3, 0, "Read the essay out loud for flow", False),  # Core Tasks
        (3, 2, "Check all arguments are well supported", False),  # Key Arguments
        (3, 3, "Check all citations and references are correct", False),  # Admin and Deadlines
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


def create_course_planner_template_grid(user):
    """
    Create a Course Planner template grid with predefined rows and columns for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Course Planner"
    )
    
    # Create row headers
    row_headers = [
        "Admin",
        "Weekly Tasks & Reading", 
        "Assignments & Coursework",
        "Exam Prep"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers
    column_headers = [
        "Macroeconomic Policy",
        "Microeconomic Policy",
        "Economic History"
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
        (0, 0, "Buy Economics, 11th Ed, by Begg, D., Vernasca, G., Fischer, S., and Dornbusch, R", False),  # Macroeconomic Policy
        
        # Weekly Tasks & Reading row
        (1, 0, "Download seminar questions for week 3", False),  # Macroeconomic Policy
        (1, 0, "Read Chapter 5 on Fiscal Policy for week 3 seminar", False),  # Macroeconomic Policy
        (1, 1, "Prepare for office hours on Wednesday at 16:00", False),  # Microeconomic Policy
        (1, 1, "Prepare week 3 seminar questions for Thursday at 16:00", False),  # Microeconomic Policy
        (1, 2, "Download reading list for the semester", False),  # Economic History
        
        
        # Assignments & Coursework row
        (2, 0, "Need to choose essay title by week 5 to submit on first Monday of week 8", False),  # Macroeconomic Policy
        (2, 0, "Have core outline sorted by week 6", False),  # Macroeconomic Policy
        (2, 1, "Pull together outline of draft essay using Toad by end of week 4", False),  # Microeconomic Policy
        (2, 2, "Think of who best to work with on group coursework", False),  # Economic History
        (2, 2, "Group coursework due by end of week 7", False),  # Economic History
        
        # Exam Prep row
        (3, 0, "Create flashcards for week 2", False),  # Macroeconomic Policy
        (3, 1, "Create flashcards for week 2", False),  # Microeconomic Policy
        (3, 1, "Go over flashcards for week 1", False),  # Microeconomic Policy
        (3, 2, "Create flashcards for week 2", False),  # Economic History
        (3, 2, "Go over flashcards for week 2", False),  # Economic History
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


def create_exam_revision_planner_grid(user):
    """
    Create an Exam Revision Planner grid with predefined rows and columns for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Exam Revision Planner"
    )
    
    # Create row headers
    row_headers = [
        "Review and Consolidate",
        "Recall and Memorisation", 
        "Practice and Application",
        "Final Review"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers
    column_headers = [
        "Macroeconomic Policy",
        "Statistical Methods for Economics",
        "Economic History"
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
        # Review and Consolidate row
        (0, 0, "Run through all lecture notes", False),  # Macroeconomic Policy
        (0, 0, "Re-read key textbook chapters", False),  # Macroeconomic Policy
        (0, 0, "Create a summary \"cheat sheet\" for the whole module", False),  # Macroeconomic Policy
        (0, 1, "Review formulae", False),  # Statistical Methods for Economics
        (0, 1, "Run through worked examples from lectures", False),  # Statistical Methods for Economics
        (0, 1, "Identify problem topics", False),  # Statistical Methods for Economics
        (0, 2, "Go through all lecture notes", False),  # Economic History
        
        # Recall and Memorisation row
        (1, 0, "Create flashcards for key concepts", False),  # Macroeconomic Policy
        (1, 0, "Practice explaining key concepts out loud", False),  # Macroeconomic Policy
        (1, 0, "Practice flashcards each morning", False),  # Macroeconomic Policy
        (1, 1, "Create flashcards for key Formulae", False),  # Statistical Methods for Economics
        (1, 2, "Create flashcards for key figures", False),  # Economic History
        (1, 2, "Create flashcards for key dates", False),  # Economic History
        (1, 2, "Run through flashcards", False),  # Economic History
        
        # Practice and Application row
        (2, 0, "Write an essay plan for a past paper question", False),  # Macroeconomic Policy
        (2, 1, "Complete the 2022 past paper under timed conditions", False),  # Statistical Methods for Economics
        (2, 1, "Mark the 2022 past paper", False),  # Statistical Methods for Economics
        (2, 1, "Complete the 2023 past paper under timed conditions", False),  # Statistical Methods for Economics
        (2, 2, "Write an essay plan for a past paper question", False),  # Economic History
        
        # Final Review row
        (3, 0, "Run through \"cheat sheet\"", False),  # Macroeconomic Policy
        (3, 0, "Run through flashcards", False),  # Macroeconomic Policy
        (3, 1, "Re-do one problem from each topic as a final check", False),  # Statistical Methods for Economics
        (3, 2, "Review flash cards", False),  # Economic History
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


def create_line_manager_grid(user):
    """
    Create a Line Manager grid with predefined rows and columns for team management.
    Uses the signal function for consistent template creation.
    """
    from ..signals import create_line_manager_grid_signal
    return create_line_manager_grid_signal(user)


def create_job_application_tracker_grid(user):
    """
    Create a Job Application Tracker grid with predefined rows and columns for the given user.
    """
    # Create the project
    project = Project.objects.create(
        user=user,
        name=f"{user.first_name}'s Job Application Tracker"
    )
    
    # Create row headers
    row_headers = [
        "Deloitte",
        "PwC", 
        "EY",
        "KPMG"
    ]
    
    for order, row_name in enumerate(row_headers):
        RowHeader.objects.create(
            project=project,
            name=row_name,
            order=order
        )
    
    # Create column headers
    column_headers = [
        "Research & Networking",
        "Application Preparation",
        "Assessment & Tests",
        "Interview"
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
        # Deloitte row
        (0, 0, "Research the difference between Audit and Tax schemes at Deloitte", False),  # Research & Networking
        (0, 0, "Find a campus networking event", False),  # Research & Networking
        (0, 1, "Tailor your CV to highlight analytical and teamwork skills", False),  # Application Preparation
        (0, 2, "Check online for hints about online assessment", False),  # Assessment & Tests
        (0, 2, "Complete online assessment", False),  # Assessment & Tests
        
        # PwC row
        (1, 0, "Research a recent deal PwC advised on", False),  # Research & Networking
        (1, 0, "Reach out to a Deal Advisory graduate on LinkedIn", False),  # Research & Networking
        (1, 1, "Find out application deadline", False),  # Application Preparation
        (1, 1, "Update CV to emphasise interest in Deal Advisory", False),  # Application Preparation
        (1, 2, "Practise numerical tests online", False),  # Assessment & Tests
        (1, 2, "Practise situational judgement tests online", False),  # Assessment & Tests
        (1, 3, "Prepare 'Why PwC?'", False),  # Interview
        (1, 3, "Prepare 'Why Deals?'", False),  # Interview
        
        # EY row
        (2, 0, "Understand the CIMA vs. ACA qualification paths", False),  # Research & Networking
        (2, 0, "Research their values", False),  # Research & Networking
        (2, 1, "Draft responses for the online application with an emphasis on their values", False),  # Application Preparation
        
        # KPMG row
        (3, 0, "Find a virtual event to attend", False),  # Research & Networking
        (3, 0, "Decide which scheme (e.g., Forensics or Tax) is the best fit", False),  # Research & Networking
        (3, 1, "Tailor CV and cover letter for Tax or Forensics once decided", False),  # Application Preparation
        (3, 2, "Prepare for the Launchpad assessment day", False),  # Assessment & Tests
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
