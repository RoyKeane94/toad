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
            "Next Steps",
            "Our Promise"
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
            (0, 1, "Pick a template for your first grid via the '+ New Grid' button", False),
            (0, 2, "We believe software should be simple and fast", False),
            
            # The Basics row (additional task)
            (0, 0, "Click the '+' at the bottom of a cell to add a new task.", False),
            (0, 1, "Click 'Clear Completed' to remove all completed tasks", False),
            
            # Make It Your Own row
            (1, 0, "Customize your grid by adding your own columns and rows", False),
            (1, 1, "Tailor a grid for that side project you've been planning", False),
            (1, 2, "Toad gives you the building blocks; you create the system", False),
            
            # Make It Your Own row (additional task)
            (1, 1, "Finally organize that holiday you've been dreaming of", False),
            
            # Your Beta Account row
            (2, 0, "Your account includes a free lifetime Personal plan", False),
            (2, 1, "This means you can create up to 10 grids", False),
            (2, 2, "Reach out any time with issues or ideas to tom@toad.co.uk", False),
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
