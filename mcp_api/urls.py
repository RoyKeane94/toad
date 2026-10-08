from django.urls import path

from . import views

app_name = 'mcp_api'

urlpatterns = [
    path('whoami', views.whoami, name='whoami'),
    path('list_grids', views.list_grids, name='list_grids'),
    path('get_grid', views.get_grid, name='get_grid'),
    path('update_grid', views.update_grid, name='update_grid'),
    path('add_task', views.add_task, name='add_task'),
    path('update_task', views.update_task, name='update_task'),
    path('delete_task', views.delete_task, name='delete_task'),
    path('log_request', views.log_request, name='log_request'),
]
