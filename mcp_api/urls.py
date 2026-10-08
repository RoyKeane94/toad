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
    path('add_row', views.add_row, name='add_row'),
    path('add_column', views.add_column, name='add_column'),
    path('reorder_rows', views.reorder_rows, name='reorder_rows'),
    path('reorder_columns', views.reorder_columns, name='reorder_columns'),
    path('log_request', views.log_request, name='log_request'),
]
