from django.contrib import admin

# Register your models here.

from .models import Project, RowHeader, ColumnHeader, Task, Template, TemplateRowHeader, TemplateColumnHeader

admin.site.register(Project)
admin.site.register(RowHeader)
admin.site.register(ColumnHeader)
admin.site.register(Task)
admin.site.register(Template)
admin.site.register(TemplateRowHeader)
admin.site.register(TemplateColumnHeader)