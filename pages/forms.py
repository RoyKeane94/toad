from django import forms
from .models import Project, RowHeader, ColumnHeader, Task

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)]',
                'placeholder': 'Enter grid name',
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
                'rows': 5,
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
                'class': 'w-full px-3 py-2 text-sm placeholder-[var(--text-secondary)] text-[var(--text-primary)] transition-colors duration-200 mobile-task-input',
                'placeholder': 'Add task',
                'required': True,
                'name': 'text',
                'style': 'border: 0 !important; border-bottom: 2px solid #10b981 !important; border-radius: 0 !important; box-shadow: none !important; outline: none !important; background: transparent !important; height: 36px; font-size: 14px !important;',
                'onfocus': 'this.style.borderBottomColor="#059669"; this.style.boxShadow="none";',
                'onblur': 'this.style.borderBottomColor="#10b981"; this.style.boxShadow="none";',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the text field required and strip whitespace
        self.fields['text'].required = True
        self.fields['text'].strip = True
    
    def clean_text(self):
        text = self.cleaned_data.get('text', '')
        if not text or not text.strip():
            raise forms.ValidationError('Please enter a task description')
        return text.strip()

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
