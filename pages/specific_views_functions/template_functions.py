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
        "Economic History",
        "Statistical Methods for Economics"
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
        (1, 3, "Download seminar questions for week 3", False),  # Statistical Methods for Economics
        
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
        (3, 3, "Create flashcards for week 3", False),  # Statistical Methods for Economics
        (3, 3, "Create flashcards for week 3", False),  # Statistical Methods for Economics
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
