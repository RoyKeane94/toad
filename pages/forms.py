from django import forms
from .models import Project, RowHeader, ColumnHeader, Task

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)]',
                'placeholder': 'Enter project name...',
                'required': True,
            }),
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['text', 'completed']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)] resize-none',
                'placeholder': 'Enter task description...',
                'rows': 3,
                'required': True,
            }),
            'completed': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-[var(--border-color)] text-[var(--primary-action-bg)] focus:ring-[var(--primary-action-bg)]',
            }),
        }

class QuickTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md text-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-1 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)]',
                'placeholder': 'Add task',
                'required': True,
                'name': 'text',
                'data-validation-message': 'Please enter a task description',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the text field required
        self.fields['text'].required = True
        self.fields['text'].strip = True

class RowHeaderForm(forms.ModelForm):
    class Meta:
        model = RowHeader
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)]',
                'placeholder': 'Enter row name...',
                'required': True,
            }),
        }

class ColumnHeaderForm(forms.ModelForm):
    class Meta:
        model = ColumnHeader
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)]',
                'placeholder': 'Enter column name...',
                'required': True,
            }),
        }
