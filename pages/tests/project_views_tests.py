from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.contrib.messages import get_messages
from pages.models import Project, RowHeader, ColumnHeader, Task
from pages.forms import ProjectForm, RowHeaderForm, ColumnHeaderForm, QuickTaskForm, TaskForm

User = get_user_model()


@override_settings(
    HANDLER404='django.views.defaults.page_not_found',
    HANDLER500='django.views.defaults.server_error',
    HANDLER403='django.views.defaults.permission_denied'
)
class ProjectViewsTestCase(TestCase):
    """Test cases for project views in pages.specific_views.project_views"""
    
    def setUp(self):
        """Set up test client and user for tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            first_name='Other',
            last_name='User',
            password='testpass123'
        )
        
        # Create test project
        self.project = Project.objects.create(
            name='Test Project',
            user=self.user
        )
        
        # Create test headers
        self.category_column = ColumnHeader.objects.create(
            project=self.project,
            name='Time / Category',
            order=0,
            is_category_column=True
        )
        self.column1 = ColumnHeader.objects.create(
            project=self.project,
            name='Column 1',
            order=1
        )
        self.row1 = RowHeader.objects.create(
            project=self.project,
            name='Row 1',
            order=0
        )
        
        # Create test task
        self.task = Task.objects.create(
            project=self.project,
            row_header=self.row1,
            column_header=self.column1,
            text='Test Task'
        )
    
    # Project Views Tests
    
    def test_project_list_view_authenticated(self):
        """Test project list view for authenticated user"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('pages:project_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/overview/project_list.html')
        self.assertContains(response, 'Test Project')
        self.assertIn('projects', response.context)
        self.assertEqual(len(response.context['projects']), 1)
    
    def test_project_list_view_unauthenticated(self):
        """Test project list view redirects for unauthenticated user"""
        response = self.client.get(reverse('pages:project_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_project_list_view_only_shows_user_projects(self):
        """Test project list only shows current user's projects"""
        # Create project for other user
        Project.objects.create(name='Other User Project', user=self.other_user)
        
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('pages:project_list'))
        
        self.assertEqual(len(response.context['projects']), 1)
        self.assertEqual(response.context['projects'][0].name, 'Test Project')
    
    def test_project_create_view_get(self):
        """Test project create view GET request"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('pages:project_create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/actions_new_page/project_form.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['title'], 'Create Project')
    
    def test_project_create_view_post_valid(self):
        """Test project create view POST with valid data"""
        self.client.login(email='test@example.com', password='testpass123')
        
        data = {'name': 'New Test Project'}
        response = self.client.post(reverse('pages:project_create'), data)
        
        # Should redirect to project grid
        self.assertEqual(response.status_code, 302)
        
        # Check project was created
        new_project = Project.objects.get(name='New Test Project')
        self.assertEqual(new_project.user, self.user)
        
        # Check default headers were created
        self.assertEqual(new_project.column_headers.count(), 4)  # 1 category + 3 regular
        self.assertEqual(new_project.row_headers.count(), 4)
        
        # Check redirect URL
        self.assertIn(f'/projects/{new_project.pk}/', response.url)
    
    def test_project_create_view_post_invalid(self):
        """Test project create view POST with invalid data"""
        self.client.login(email='test@example.com', password='testpass123')
        
        data = {'name': ''}  # Empty name should be invalid
        response = self.client.post(reverse('pages:project_create'), data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/actions_new_page/project_form.html')
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
    
    def test_project_edit_view_get(self):
        """Test project edit view GET request"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('pages:project_edit', kwargs={'pk': self.project.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/actions_new_page/project_form.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['title'], 'Edit Project')
        self.assertEqual(response.context['project'], self.project)
    
    def test_project_edit_view_post_valid(self):
        """Test project edit view POST with valid data"""
        self.client.login(email='test@example.com', password='testpass123')
        
        data = {'name': 'Updated Project Name'}
        response = self.client.post(reverse('pages:project_edit', kwargs={'pk': self.project.pk}), data)
        
        self.assertEqual(response.status_code, 302)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Project Name')
    
    def test_project_edit_view_unauthorized_user(self):
        """Test project edit view with unauthorized user"""
        self.client.login(email='other@example.com', password='testpass123')
        response = self.client.get(reverse('pages:project_edit', kwargs={'pk': self.project.pk}))
        
        self.assertEqual(response.status_code, 404)
    
    def test_project_delete_view_get(self):
        """Test project delete view GET request"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('pages:project_delete', kwargs={'pk': self.project.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/actions_new_page/project_confirm_delete.html')
        self.assertEqual(response.context['project'], self.project)
    
    def test_project_delete_view_post(self):
        """Test project delete view POST request"""
        self.client.login(email='test@example.com', password='testpass123')
        project_pk = self.project.pk
        
        response = self.client.post(reverse('pages:project_delete', kwargs={'pk': project_pk}))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('pages:project_list'))
        
        # Check project was deleted
        with self.assertRaises(Project.DoesNotExist):
            Project.objects.get(pk=project_pk)
    
    def test_project_grid_view(self):
        """Test project grid view"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('pages:project_grid', kwargs={'pk': self.project.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/project_grid.html')
        
        context = response.context
        self.assertEqual(context['project'], self.project)
        self.assertIn('row_headers', context)
        self.assertIn('column_headers', context)
        self.assertIn('tasks_by_cell', context)
        self.assertIn('quick_task_form', context)
    
    def test_project_grid_view_unauthorized(self):
        """Test project grid view with unauthorized user"""
        self.client.login(email='other@example.com', password='testpass123')
        response = self.client.get(reverse('pages:project_grid', kwargs={'pk': self.project.pk}))
        
        self.assertEqual(response.status_code, 404)


@override_settings(
    HANDLER404='django.views.defaults.page_not_found',
    HANDLER500='django.views.defaults.server_error',
    HANDLER403='django.views.defaults.permission_denied'
)
class TaskViewsTestCase(TestCase):
    """Test cases for task CRUD views"""
    
    def setUp(self):
        """Set up test data for task tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        
        self.project = Project.objects.create(name='Test Project', user=self.user)
        self.column = ColumnHeader.objects.create(project=self.project, name='Test Column', order=1)
        self.row = RowHeader.objects.create(project=self.project, name='Test Row', order=0)
        self.task = Task.objects.create(
            project=self.project,
            row_header=self.row,
            column_header=self.column,
            text='Test Task'
        )
    
    def test_task_create_view_post_valid(self):
        """Test task creation with valid data"""
        self.client.login(email='test@example.com', password='testpass123')
        
        data = {'text': 'New Task'}
        response = self.client.post(
            reverse('pages:task_create', kwargs={
                'project_pk': self.project.pk,
                'row_pk': self.row.pk,
                'col_pk': self.column.pk
            }),
            data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(text='New Task').exists())
    
    def test_task_create_view_htmx_request(self):
        """Test task creation via HTMX"""
        self.client.login(email='test@example.com', password='testpass123')
        
        data = {'text': 'HTMX Task'}
        response = self.client.post(
            reverse('pages:task_create', kwargs={
                'project_pk': self.project.pk,
                'row_pk': self.row.pk,
                'col_pk': self.column.pk
            }),
            data,
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/actions_in_page/task_item.html')
        self.assertTrue(Task.objects.filter(text='HTMX Task').exists())
    
    def test_task_edit_view_get(self):
        """Test task edit view GET request"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('pages:task_edit', kwargs={'task_pk': self.task.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/task_form.html')
    
    def test_task_edit_view_htmx_get(self):
        """Test task edit view GET request via HTMX"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(
            reverse('pages:task_edit', kwargs={'task_pk': self.task.pk}),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/modals/task_form_content.html')
    
    def test_task_edit_view_post_valid(self):
        """Test task edit with valid data"""
        self.client.login(email='test@example.com', password='testpass123')
        
        data = {'text': 'Updated Task', 'completed': True}
        response = self.client.post(
            reverse('pages:task_edit', kwargs={'task_pk': self.task.pk}),
            data
        )
        
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.text, 'Updated Task')
    
    def test_task_toggle_complete_view(self):
        """Test task toggle completion"""
        self.client.login(email='test@example.com', password='testpass123')
        
        initial_status = self.task.completed
        response = self.client.post(
            reverse('pages:task_toggle_complete', kwargs={'task_pk': self.task.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.completed, not initial_status)
    
    def test_task_toggle_complete_htmx(self):
        """Test task toggle completion via HTMX"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('pages:task_toggle_complete', kwargs={'task_pk': self.task.pk}),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_task_delete_view(self):
        """Test task deletion"""
        self.client.login(email='test@example.com', password='testpass123')
        task_pk = self.task.pk
        
        response = self.client.post(
            reverse('pages:task_delete', kwargs={'task_pk': task_pk})
        )
        
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(Task.DoesNotExist):
            Task.objects.get(pk=task_pk)
    
    def test_task_delete_view_htmx(self):
        """Test task deletion via HTMX"""
        self.client.login(email='test@example.com', password='testpass123')
        task_pk = self.task.pk
        
        response = self.client.post(
            reverse('pages:task_delete', kwargs={'task_pk': task_pk}),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Task.DoesNotExist):
            Task.objects.get(pk=task_pk)


@override_settings(
    HANDLER404='django.views.defaults.page_not_found',
    HANDLER500='django.views.defaults.server_error',
    HANDLER403='django.views.defaults.permission_denied'
)
class RowColumnViewsTestCase(TestCase):
    """Test cases for row and column CRUD views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        
        self.project = Project.objects.create(name='Test Project', user=self.user)
        self.row = RowHeader.objects.create(project=self.project, name='Test Row', order=0)
        self.column = ColumnHeader.objects.create(project=self.project, name='Test Column', order=1)
    
    # Row Tests
    
    def test_row_create_view_get(self):
        """Test row create view GET request"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(
            reverse('pages:row_create', kwargs={'project_pk': self.project.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/actions_new_page/grid_item_form.html')
    
    def test_row_create_view_post_valid(self):
        """Test row creation with valid data"""
        self.client.login(email='test@example.com', password='testpass123')
        
        data = {'name': 'New Row'}
        response = self.client.post(
            reverse('pages:row_create', kwargs={'project_pk': self.project.pk}),
            data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(RowHeader.objects.filter(name='New Row').exists())
    
    def test_row_edit_view_get(self):
        """Test row edit view GET request"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(
            reverse('pages:row_edit', kwargs={
                'project_pk': self.project.pk,
                'row_pk': self.row.pk
            })
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/actions_new_page/grid_item_form.html')
    
    def test_row_edit_view_htmx_get(self):
        """Test row edit view GET request via HTMX"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(
            reverse('pages:row_edit', kwargs={
                'project_pk': self.project.pk,
                'row_pk': self.row.pk
            }),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/modals/row_form_content.html')
    
    def test_row_delete_view_htmx_get(self):
        """Test row delete view GET request via HTMX"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(
            reverse('pages:row_delete', kwargs={
                'project_pk': self.project.pk,
                'row_pk': self.row.pk
            }),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/modals/row_delete_content.html')
    
    def test_row_delete_view_post(self):
        """Test row deletion"""
        self.client.login(email='test@example.com', password='testpass123')
        row_pk = self.row.pk
        
        response = self.client.post(
            reverse('pages:row_delete', kwargs={
                'project_pk': self.project.pk,
                'row_pk': row_pk
            })
        )
        
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(RowHeader.DoesNotExist):
            RowHeader.objects.get(pk=row_pk)
    
    # Column Tests
    
    def test_column_create_view_get(self):
        """Test column create view GET request"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(
            reverse('pages:column_create', kwargs={'project_pk': self.project.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/actions_new_page/grid_item_form.html')
    
    def test_column_create_view_post_valid(self):
        """Test column creation with valid data"""
        self.client.login(email='test@example.com', password='testpass123')
        
        data = {'name': 'New Column'}
        response = self.client.post(
            reverse('pages:column_create', kwargs={'project_pk': self.project.pk}),
            data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ColumnHeader.objects.filter(name='New Column').exists())
    
    def test_column_edit_view_htmx_post_valid(self):
        """Test column edit via HTMX with valid data"""
        self.client.login(email='test@example.com', password='testpass123')
        
        data = {'name': 'Updated Column'}
        response = self.client.post(
            reverse('pages:column_edit', kwargs={
                'project_pk': self.project.pk,
                'col_pk': self.column.pk
            }),
            data,
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.column.refresh_from_db()
        self.assertEqual(self.column.name, 'Updated Column')
    
    def test_column_delete_view_htmx_post(self):
        """Test column deletion via HTMX"""
        self.client.login(email='test@example.com', password='testpass123')
        column_pk = self.column.pk
        
        response = self.client.post(
            reverse('pages:column_delete', kwargs={
                'project_pk': self.project.pk,
                'col_pk': column_pk
            }),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        with self.assertRaises(ColumnHeader.DoesNotExist):
            ColumnHeader.objects.get(pk=column_pk)


@override_settings(
    HANDLER404='django.views.defaults.page_not_found',
    HANDLER500='django.views.defaults.server_error',
    HANDLER403='django.views.defaults.permission_denied'
)
class UtilityViewsTestCase(TestCase):
    """Test cases for utility views like delete completed tasks and template creation"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        
        self.project = Project.objects.create(name='Test Project', user=self.user)
        self.column = ColumnHeader.objects.create(project=self.project, name='Test Column', order=1)
        self.row = RowHeader.objects.create(project=self.project, name='Test Row', order=0)
        
        # Create completed and incomplete tasks
        self.completed_task = Task.objects.create(
            project=self.project,
            row_header=self.row,
            column_header=self.column,
            text='Completed Task',
            completed=True
        )
        self.incomplete_task = Task.objects.create(
            project=self.project,
            row_header=self.row,
            column_header=self.column,
            text='Incomplete Task',
            completed=False
        )
    
    def test_delete_completed_tasks_view_get(self):
        """Test delete completed tasks view GET request"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(
            reverse('pages:delete_completed_tasks', kwargs={'pk': self.project.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/grid/actions_in_page/clear_completed_tasks.html')
    
    def test_delete_completed_tasks_view_post(self):
        """Test deletion of completed tasks"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('pages:delete_completed_tasks', kwargs={'pk': self.project.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Check completed task was deleted
        with self.assertRaises(Task.DoesNotExist):
            Task.objects.get(pk=self.completed_task.pk)
        
        # Check incomplete task still exists
        self.assertTrue(Task.objects.filter(pk=self.incomplete_task.pk).exists())
    
    def test_create_from_template_view_student_jobs(self):
        """Test creating project from student jobs template"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('pages:create_from_template', kwargs={'template_type': 'student_jobs'})
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Check project was created
        project = Project.objects.get(name='Student Job Applications')
        self.assertEqual(project.user, self.user)
        
        # Check headers were created
        self.assertEqual(project.column_headers.count(), 5)  # 1 category + 4 template columns
        self.assertEqual(project.row_headers.count(), 4)  # 4 template rows
    
    def test_create_from_template_view_student_revision(self):
        """Test creating project from student revision template"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('pages:create_from_template', kwargs={'template_type': 'student_revision'})
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Check project was created
        project = Project.objects.get(name='Student Revision Planner')
        self.assertEqual(project.user, self.user)
    
    def test_create_from_template_view_professionals_jobs(self):
        """Test creating project from professionals jobs template"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('pages:create_from_template', kwargs={'template_type': 'professionals_jobs'})
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Check project was created
        project = Project.objects.get(name='Professional Career Tracker')
        self.assertEqual(project.user, self.user)
    
    def test_create_from_template_view_invalid_template(self):
        """Test creating project with invalid template type"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('pages:create_from_template', kwargs={'template_type': 'invalid_template'})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('pages:templates_overview'))
    
    def test_create_from_template_view_get_request(self):
        """Test template creation with GET request (should redirect)"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.get(
            reverse('pages:create_from_template', kwargs={'template_type': 'student_jobs'})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('pages:templates_overview'))


@override_settings(
    HANDLER404='django.views.defaults.page_not_found',
    HANDLER500='django.views.defaults.server_error',
    HANDLER403='django.views.defaults.permission_denied'
)
class ProjectViewsPermissionsTestCase(TestCase):
    """Test cases for permissions and security in project views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            first_name='User',
            last_name='One',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            first_name='User',
            last_name='Two',
            password='testpass123'
        )
        
        self.project1 = Project.objects.create(name='User1 Project', user=self.user1)
        self.project2 = Project.objects.create(name='User2 Project', user=self.user2)
    
    def test_user_cannot_access_other_users_project(self):
        """Test that users cannot access other users' projects"""
        self.client.login(email='user1@example.com', password='testpass123')
        
        # Try to access user2's project
        response = self.client.get(reverse('pages:project_grid', kwargs={'pk': self.project2.pk}))
        self.assertEqual(response.status_code, 404)
        
        # Try to edit user2's project
        response = self.client.get(reverse('pages:project_edit', kwargs={'pk': self.project2.pk}))
        self.assertEqual(response.status_code, 404)
        
        # Try to delete user2's project
        response = self.client.get(reverse('pages:project_delete', kwargs={'pk': self.project2.pk}))
        self.assertEqual(response.status_code, 404)
    
    def test_unauthenticated_user_redirected_to_login(self):
        """Test that unauthenticated users are redirected to login"""
        login_required_views = [
            ('pages:project_list', {}),
            ('pages:project_create', {}),
            ('pages:project_grid', {'pk': self.project1.pk}),
            ('pages:delete_completed_tasks', {'pk': self.project1.pk}),
            ('pages:create_from_template', {'template_type': 'student_jobs'}),
        ]
        
        for view_name, kwargs in login_required_views:
            with self.subTest(view_name=view_name):
                response = self.client.get(reverse(view_name, kwargs=kwargs))
                self.assertEqual(response.status_code, 302)
                self.assertIn('/accounts/login/', response.url)


@override_settings(
    HANDLER404='django.views.defaults.page_not_found',
    HANDLER500='django.views.defaults.server_error',
    HANDLER403='django.views.defaults.permission_denied'
)
class ProjectViewsIntegrationTestCase(TestCase):
    """Integration tests for project views workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')
    
    def test_complete_project_workflow(self):
        """Test complete project creation and management workflow"""
        # 1. Create project
        response = self.client.post(reverse('pages:project_create'), {'name': 'Integration Test Project'})
        self.assertEqual(response.status_code, 302)
        
        project = Project.objects.get(name='Integration Test Project')
        
        # 2. Access project grid
        response = self.client.get(reverse('pages:project_grid', kwargs={'pk': project.pk}))
        self.assertEqual(response.status_code, 200)
        
        # 3. Create a task
        row = project.row_headers.first()
        column = project.column_headers.filter(is_category_column=False).first()
        
        response = self.client.post(
            reverse('pages:task_create', kwargs={
                'project_pk': project.pk,
                'row_pk': row.pk,
                'col_pk': column.pk
            }),
            {'text': 'Integration Test Task'}
        )
        self.assertEqual(response.status_code, 302)
        
        # 4. Toggle task completion
        task = Task.objects.get(text='Integration Test Task')
        response = self.client.post(
            reverse('pages:task_toggle_complete', kwargs={'task_pk': task.pk})
        )
        self.assertEqual(response.status_code, 302)
        
        # 5. Delete completed tasks
        response = self.client.post(
            reverse('pages:delete_completed_tasks', kwargs={'pk': project.pk})
        )
        self.assertEqual(response.status_code, 302)
        
        # Task should be deleted
        with self.assertRaises(Task.DoesNotExist):
            Task.objects.get(pk=task.pk)
    
    def test_template_creation_workflow(self):
        """Test template-based project creation workflow"""
        # Create from template
        response = self.client.post(
            reverse('pages:create_from_template', kwargs={'template_type': 'student_jobs'})
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify project was created with correct structure
        project = Project.objects.get(name='Student Job Applications')
        self.assertEqual(project.user, self.user)
        
        # Check structure matches template
        self.assertEqual(project.row_headers.count(), 4)
        self.assertEqual(project.column_headers.count(), 5)  # 1 category + 4 regular
        
        # Verify we can access the project
        response = self.client.get(reverse('pages:project_grid', kwargs={'pk': project.pk}))
        self.assertEqual(response.status_code, 200)
