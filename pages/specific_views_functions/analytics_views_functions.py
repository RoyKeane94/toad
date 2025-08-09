from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from pages.models import Project, Task


def get_dashboard_analytics():
    """
    Get comprehensive analytics for the superuser dashboard
    """
    now = timezone.now()
    day_ago = now - timedelta(days=1)
    three_days_ago = now - timedelta(days=3)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # Total users
    total_users = User.objects.count()
    
    # Active Users windows (created grid, ticked off a task, or created a new task)
    last_day_active_users = User.objects.filter(
        Q(toad_projects__created_at__gte=day_ago) |
        Q(toad_projects__tasks__updated_at__gte=day_ago, toad_projects__tasks__completed=True) |
        Q(toad_projects__tasks__created_at__gte=day_ago)
    ).distinct().count()

    last_3_days_active_users = User.objects.filter(
        Q(toad_projects__created_at__gte=three_days_ago) |
        Q(toad_projects__tasks__updated_at__gte=three_days_ago, toad_projects__tasks__completed=True) |
        Q(toad_projects__tasks__created_at__gte=three_days_ago)
    ).distinct().count()
    
    # Weekly Active Users
    weekly_active_users = User.objects.filter(
        Q(toad_projects__created_at__gte=week_ago) |
        Q(toad_projects__tasks__updated_at__gte=week_ago, toad_projects__tasks__completed=True) |
        Q(toad_projects__tasks__created_at__gte=week_ago)
    ).distinct().count()
    
    # Monthly Active Users
    monthly_active_users = User.objects.filter(
        Q(toad_projects__created_at__gte=month_ago) |
        Q(toad_projects__tasks__updated_at__gte=month_ago, toad_projects__tasks__completed=True) |
        Q(toad_projects__tasks__created_at__gte=month_ago)
    ).distinct().count()
    
    # Inactive Users (no activity in the last month)
    inactive_users = User.objects.exclude(
        Q(toad_projects__created_at__gte=month_ago) |
        Q(toad_projects__tasks__updated_at__gte=month_ago, toad_projects__tasks__completed=True) |
        Q(toad_projects__tasks__created_at__gte=month_ago)
    ).count()
    
    # Users with specific grid counts (1 through 10, then 10+)
    users_with_1_grid = User.objects.annotate(
        grid_count=Count('toad_projects')
    ).filter(grid_count=1).count()
    
    users_with_2_grids = User.objects.annotate(
        grid_count=Count('toad_projects')
    ).filter(grid_count=2).count()
    
    users_with_3_grids = User.objects.annotate(
        grid_count=Count('toad_projects')
    ).filter(grid_count=3).count()
    
    users_with_4_grids = User.objects.annotate(
        grid_count=Count('toad_projects')
    ).filter(grid_count=4).count()
    
    users_with_5_grids = User.objects.annotate(
        grid_count=Count('toad_projects')
    ).filter(grid_count=5).count()
    
    users_with_6_grids = User.objects.annotate(
        grid_count=Count('toad_projects')
    ).filter(grid_count=6).count()
    
    users_with_7_grids = User.objects.annotate(
        grid_count=Count('toad_projects')
    ).filter(grid_count=7).count()
    
    users_with_8_grids = User.objects.annotate(
        grid_count=Count('toad_projects')
    ).filter(grid_count=8).count()
    
    users_with_9_grids = User.objects.annotate(
        grid_count=Count('toad_projects')
    ).filter(grid_count=9).count()
    
    users_with_10_grids = User.objects.annotate(
        grid_count=Count('toad_projects')
    ).filter(grid_count=10).count()
    
    users_with_10_plus_grids = User.objects.annotate(
        grid_count=Count('toad_projects')
    ).filter(grid_count__gte=10).count()
    
    # Calculate percentages
    last_day_active_percentage = round((last_day_active_users / total_users * 100), 1) if total_users > 0 else 0
    last_3_days_active_percentage = round((last_3_days_active_users / total_users * 100), 1) if total_users > 0 else 0
    weekly_active_percentage = round((weekly_active_users / total_users * 100), 1) if total_users > 0 else 0
    monthly_active_percentage = round((monthly_active_users / total_users * 100), 1) if total_users > 0 else 0
    inactive_percentage = round((inactive_users / total_users * 100), 1) if total_users > 0 else 0
    
    return {
        'total_users': total_users,
        'last_day_active_users': last_day_active_users,
        'last_day_active_percentage': last_day_active_percentage,
        'last_3_days_active_users': last_3_days_active_users,
        'last_3_days_active_percentage': last_3_days_active_percentage,
        'weekly_active_users': weekly_active_users,
        'weekly_active_percentage': weekly_active_percentage,
        'monthly_active_users': monthly_active_users,
        'monthly_active_percentage': monthly_active_percentage,
        'inactive_users': inactive_users,
        'inactive_percentage': inactive_percentage,
        'users_with_1_grid': users_with_1_grid,
        'users_with_2_grids': users_with_2_grids,
        'users_with_3_grids': users_with_3_grids,
        'users_with_4_grids': users_with_4_grids,
        'users_with_5_grids': users_with_5_grids,
        'users_with_6_grids': users_with_6_grids,
        'users_with_7_grids': users_with_7_grids,
        'users_with_8_grids': users_with_8_grids,
        'users_with_9_grids': users_with_9_grids,
        'users_with_10_grids': users_with_10_grids,
        'users_with_10_plus_grids': users_with_10_plus_grids,
    }
