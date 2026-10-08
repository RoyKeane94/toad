import json

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from pages.models import Project, RowHeader, ColumnHeader, Task, TaskNote
from .models import PersonalAccessToken, MCPRequestLog

User = get_user_model()


class MCPApiTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='owner@example.com',
            first_name='Owner',
            last_name='User',
            password='testpass123',
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            first_name='Other',
            last_name='User',
            password='testpass123',
        )
        self.raw_token = PersonalAccessToken.issue_for_user(self.user)
        self.other_token = PersonalAccessToken.issue_for_user(self.other_user)

        self.project = Project.objects.create(name='Work Grid', user=self.user)
        self.other_project = Project.objects.create(name='Secret Grid', user=self.other_user)

        self.category = ColumnHeader.objects.create(
            project=self.project, name='Category', order=0, is_category_column=True
        )
        self.column = ColumnHeader.objects.create(
            project=self.project, name='This week', order=1
        )
        self.row = RowHeader.objects.create(project=self.project, name='Today', order=0)
        self.later_row = RowHeader.objects.create(project=self.project, name='Later', order=1)

        self.task = Task.objects.create(
            project=self.project,
            row_header=self.row,
            column_header=self.column,
            text='Write tests',
        )
        TaskNote.objects.create(task=self.task, created_by=self.user, note='Cover the MCP API')

        self.other_task = Task.objects.create(
            project=self.other_project,
            row_header=RowHeader.objects.create(project=self.other_project, name='R', order=0),
            column_header=ColumnHeader.objects.create(project=self.other_project, name='C', order=1),
            text='Private task',
        )

    def post(self, name, payload=None, token=None):
        headers = {}
        if token is not None:
            headers['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return self.client.post(
            reverse(f'mcp_api:{name}'),
            data=json.dumps(payload or {}),
            content_type='application/json',
            **headers,
        )

    def test_missing_token_is_rejected(self):
        response = self.post('list_grids', token=None)
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_is_rejected(self):
        response = self.post('list_grids', token='toad_not-a-real-token')
        self.assertEqual(response.status_code, 401)

    def test_list_grids_returns_own_grids_only(self):
        response = self.post('list_grids', token=self.raw_token)
        self.assertEqual(response.status_code, 200)
        grids = response.json()['grids']
        names = {grid['name'] for grid in grids}
        self.assertIn('Work Grid', names)
        self.assertNotIn('Secret Grid', names)
        self.assertTrue(any(grid['id'] == self.project.id for grid in grids))

    def test_get_grid_includes_rows_columns_and_tagged_tasks(self):
        response = self.post('get_grid', {'grid_id': self.project.id}, token=self.raw_token)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['name'], 'Work Grid')
        self.assertEqual([row['name'] for row in body['rows']], ['Today', 'Later'])
        task = body['tasks'][0]
        self.assertEqual(task['text'], 'Write tests')
        self.assertEqual(task['row'], 'Today')
        self.assertEqual(task['column'], 'This week')
        self.assertFalse(task['ticked'])
        self.assertEqual(task['note'], 'Cover the MCP API')

    def test_cannot_read_another_users_grid(self):
        response = self.post('get_grid', {'grid_id': self.other_project.id}, token=self.raw_token)
        self.assertEqual(response.status_code, 404)

    def test_add_task_with_optional_note(self):
        response = self.post(
            'add_task',
            {
                'grid_id': self.project.id,
                'row_id': self.row.id,
                'column_id': self.column.id,
                'text': 'Ship MCP',
                'note': 'First test',
            },
            token=self.raw_token,
        )
        self.assertEqual(response.status_code, 201)
        task = response.json()['task']
        self.assertEqual(task['text'], 'Ship MCP')
        self.assertEqual(task['row'], 'Today')
        self.assertEqual(task['column'], 'This week')
        self.assertFalse(task['ticked'])
        self.assertEqual(task['note'], 'First test')
        self.assertTrue(Task.objects.filter(pk=task['id'], project=self.project).exists())

    def test_cannot_add_task_to_category_column(self):
        response = self.post(
            'add_task',
            {
                'grid_id': self.project.id,
                'row_id': self.row.id,
                'column_id': self.category.id,
                'text': 'Should fail',
            },
            token=self.raw_token,
        )
        self.assertEqual(response.status_code, 400)

    def test_update_task_tick_rename_and_move(self):
        response = self.post(
            'update_task',
            {
                'task_id': self.task.id,
                'ticked': True,
                'text': 'Write more tests',
                'row_id': self.later_row.id,
            },
            token=self.raw_token,
        )
        self.assertEqual(response.status_code, 200)
        task = response.json()['task']
        self.assertTrue(task['ticked'])
        self.assertEqual(task['text'], 'Write more tests')
        self.assertEqual(task['row'], 'Later')
        self.task.refresh_from_db()
        self.assertTrue(self.task.completed)
        self.assertEqual(self.task.row_header_id, self.later_row.id)

    def test_cannot_update_another_users_task(self):
        response = self.post(
            'update_task',
            {'task_id': self.other_task.id, 'ticked': True},
            token=self.raw_token,
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_task(self):
        response = self.post('delete_task', {'task_id': self.task.id}, token=self.raw_token)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(pk=self.task.id).exists())

    def test_log_request_stores_who_what_when_and_follow_up_without_output(self):
        response = self.post(
            'log_request',
            {
                'asked_by': 'Tom',
                'what': 'Tick the MCP tasks on Work Grid',
                'follow_up_needed': True,
            },
            token=self.raw_token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True})
        log = MCPRequestLog.objects.get()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.asked_by, 'Tom')
        self.assertEqual(log.request_text, 'Tick the MCP tasks on Work Grid')
        self.assertTrue(log.follow_up_needed)
        self.assertIsNotNone(log.created_at)
        self.assertFalse(hasattr(log, 'output'))

    def test_regenerating_token_invalidates_the_old_one(self):
        new_token = PersonalAccessToken.issue_for_user(self.user)
        old_response = self.post('list_grids', token=self.raw_token)
        new_response = self.post('list_grids', token=new_token)
        self.assertEqual(old_response.status_code, 401)
        self.assertEqual(new_response.status_code, 200)


class MCPTokenSettingsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='settings@example.com',
            first_name='Settings',
            last_name='User',
            password='testpass123',
            email_verified=True,
        )

    def test_generate_token_from_settings(self):
        self.client.login(email='settings@example.com', password='testpass123')
        response = self.client.post(reverse('accounts:mcp_token_generate'))
        self.assertRedirects(
            response,
            reverse('accounts:account_settings'),
            fetch_redirect_response=False,
        )
        self.assertTrue(PersonalAccessToken.objects.filter(user=self.user).exists())
        self.assertIn('new_mcp_token', self.client.session)
        raw_token = self.client.session['new_mcp_token']
        settings_page = self.client.get(reverse('accounts:account_settings'))
        self.assertContains(settings_page, raw_token)
        second_load = self.client.get(reverse('accounts:account_settings'))
        self.assertNotContains(second_load, raw_token)

    def test_revoke_token_from_settings(self):
        PersonalAccessToken.issue_for_user(self.user)
        self.client.login(email='settings@example.com', password='testpass123')
        response = self.client.post(reverse('accounts:mcp_token_revoke'))
        self.assertRedirects(response, reverse('accounts:account_settings'))
        self.assertFalse(PersonalAccessToken.objects.filter(user=self.user).exists())
