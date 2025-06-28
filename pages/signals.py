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
            
            # Make It Your Own row
            (1, 0, "Make your grid your own by adding your own columns and rows", False),
            (1, 0, "Pick a template for your first grid using Templates or create your own grid by clicking Grids", False),
            (1, 0, "Tailor a grid to start planning your week better, find your next job or organise your holiday", False),
            
            # Your Beta Account row
            (2, 0, "We have built Toad to be simple and fast", True),
            (2, 0, "As a Beta user, you have a free Toad Pro plan for life, meaning no limit on grids and the ability to create your own templates", False),
            (2, 0, "Please reach out any time with issues or ideas to tom@toad.co.uk", False),
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
