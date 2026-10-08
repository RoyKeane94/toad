from django.urls import path

from . import views

app_name = 'mcp_api'

urlpatterns = [
    path('whoami', views.whoami, name='whoami'),
    path('list_grids', views.list_grids, name='list_grids'),
    path('create_grid', views.create_grid, name='create_grid'),
    path('get_grid', views.get_grid, name='get_grid'),
    path('update_grid', views.update_grid, name='update_grid'),
    path('add_task', views.add_task, name='add_task'),
    path('update_task', views.update_task, name='update_task'),
    path('delete_task', views.delete_task, name='delete_task'),
    path('add_row', views.add_row, name='add_row'),
    path('add_column', views.add_column, name='add_column'),
    path('reorder_rows', views.reorder_rows, name='reorder_rows'),
    path('reorder_columns', views.reorder_columns, name='reorder_columns'),
    path('rename_row', views.rename_row, name='rename_row'),
    path('rename_column', views.rename_column, name='rename_column'),
    path('delete_row', views.delete_row, name='delete_row'),
    path('delete_column', views.delete_column, name='delete_column'),
    path('log_request', views.log_request, name='log_request'),
]
