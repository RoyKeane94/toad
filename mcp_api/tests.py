import json

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from pages.models import Project, RowHeader, ColumnHeader, Task, TaskNote
from .models import PersonalAccessToken, MCPRequestLog, TaskActivity

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

        self.project = Project.objects.create(
            name='Work Grid',
            user=self.user,
            brief='Ramble frozen positioning. My Stamp spec lives here.',
        )
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
        self.assertEqual(body['brief'], 'Ramble frozen positioning. My Stamp spec lives here.')
        self.assertEqual(task['owner'], 'you')
        self.assertFalse(task['needs_review'])
        self.assertEqual(body['activity'], [])

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
        self.assertEqual(task['owner'], 'agent')
        self.assertFalse(task['needs_review'])
        self.assertTrue(Task.objects.filter(pk=task['id'], project=self.project).exists())
        activity = TaskActivity.objects.get(action='added')
        self.assertEqual(activity.agent, 'Grok Bot')
        self.assertEqual(activity.task_id, task['id'])
        self.assertEqual(activity.task_text, 'Ship MCP')

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
        actions = list(TaskActivity.objects.filter(task=self.task).values_list('action', flat=True))
        self.assertIn('ticked', actions)
        self.assertIn('renamed', actions)
        self.assertIn('moved to Later', actions)
        self.assertNotIn('updated', actions)

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

    def mcp_rpc(self, method, params=None, token=None, rpc_id=1):
        headers = {'HTTP_ACCEPT': 'application/json, text/event-stream'}
        if token is not None:
            headers['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return self.client.post(
            '/mcp',
            data=json.dumps({
                'jsonrpc': '2.0',
                'id': rpc_id,
                'method': method,
                'params': params or {},
            }),
            content_type='application/json',
            **headers,
        )

    def test_mcp_get_is_not_a_404(self):
        response = self.client.get('/mcp', HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Toad MCP is running')

    def test_mcp_initialize_and_list_tools(self):
        response = self.mcp_rpc(
            'initialize',
            {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'test'}},
            token=self.raw_token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result']['serverInfo']['name'], 'Toad')

        listed = self.mcp_rpc('tools/list', token=self.raw_token)
        names = {tool['name'] for tool in listed.json()['result']['tools']}
        self.assertEqual(
            names,
            {
                'list_grids',
                'get_grid',
                'update_grid',
                'add_task',
                'update_task',
                'delete_task',
                'add_row',
                'add_column',
                'reorder_rows',
                'reorder_columns',
                'log_request',
            },
        )

    def test_mcp_list_grids_tool_call(self):
        response = self.mcp_rpc(
            'tools/call',
            {'name': 'list_grids', 'arguments': {}},
            token=self.raw_token,
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()['result']
        self.assertFalse(result['isError'])
        names = {grid['name'] for grid in result['structuredContent']['grids']}
        self.assertIn('Work Grid', names)

    def test_mcp_rejects_missing_token_on_post(self):
        response = self.mcp_rpc('tools/list', token=None)
        self.assertEqual(response.status_code, 401)

    def test_update_grid_sets_brief(self):
        response = self.post(
            'update_grid',
            {'grid_id': self.project.id, 'brief': 'Keep the hero frozen on scroll.'},
            token=self.raw_token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['brief'], 'Keep the hero frozen on scroll.')
        self.project.refresh_from_db()
        self.assertEqual(self.project.brief, 'Keep the hero frozen on scroll.')
        activity = TaskActivity.objects.get(action='updated the brief')
        self.assertEqual(activity.agent, 'Grok Bot')

    def test_update_task_owner_and_needs_review(self):
        response = self.post(
            'update_task',
            {
                'task_id': self.task.id,
                'owner': 'agent',
                'needs_review': True,
            },
            token=self.raw_token,
        )
        self.assertEqual(response.status_code, 200)
        task = response.json()['task']
        self.assertEqual(task['owner'], 'agent')
        self.assertTrue(task['needs_review'])
        self.task.refresh_from_db()
        self.assertEqual(self.task.owner, Task.OWNER_AGENT)
        self.assertTrue(self.task.needs_review)
        actions = list(
            TaskActivity.objects.filter(task=self.task).values_list('action', flat=True)
        )
        self.assertIn('handed to agent', actions)
        self.assertIn('marked for review', actions)
        self.assertNotIn('updated', actions)

    def test_delete_task_keeps_activity_text(self):
        response = self.post('delete_task', {'task_id': self.task.id}, token=self.raw_token)
        self.assertEqual(response.status_code, 200)
        activity = TaskActivity.objects.get(action='deleted')
        self.assertEqual(activity.agent, 'Grok Bot')
        self.assertEqual(activity.task_text, 'Write tests')
        self.assertIsNone(activity.task_id)

    def test_get_grid_includes_recent_activity(self):
        self.post(
            'add_task',
            {
                'grid_id': self.project.id,
                'row_id': self.row.id,
                'column_id': self.column.id,
                'text': 'Draft the stamp spec',
                'needs_review': True,
            },
            token=self.raw_token,
        )
        response = self.post('get_grid', {'grid_id': self.project.id}, token=self.raw_token)
        activity = response.json()['activity']
        self.assertEqual(activity[0]['agent'], 'Grok Bot')
        self.assertEqual(activity[0]['action'], 'added')
        self.assertEqual(activity[0]['task'], 'Draft the stamp spec')
        self.assertIn('created_at', activity[0])

    def test_named_tokens_log_the_agent_that_made_the_change(self):
        ramble_token = PersonalAccessToken.issue_for_user(self.user, name='Ramble')
        research_token = PersonalAccessToken.issue_for_user(self.user, name='Research')

        self.post(
            'update_task',
            {'task_id': self.task.id, 'ticked': True},
            token=ramble_token,
        )
        self.post(
            'update_task',
            {'task_id': self.task.id, 'row_id': self.later_row.id},
            token=research_token,
        )

        actions = list(TaskActivity.objects.filter(task=self.task).values_list('agent', 'action'))
        self.assertIn(('Ramble', 'ticked'), actions)
        self.assertIn(('Research', 'moved to Later'), actions)
        self.assertTrue(PersonalAccessToken.objects.filter(user=self.user, name='Grok Bot').exists())

    def test_add_row_and_column_and_reorder(self):
        row_response = self.post(
            'add_row',
            {'grid_id': self.project.id, 'name': 'This month', 'after_row_id': self.row.id},
            token=self.raw_token,
        )
        self.assertEqual(row_response.status_code, 201)
        row_names = [row['name'] for row in row_response.json()['rows']]
        self.assertEqual(row_names, ['Today', 'This month', 'Later'])
        new_row_id = row_response.json()['row']['id']

        reorder_rows = self.post(
            'reorder_rows',
            {'grid_id': self.project.id, 'row_ids': [new_row_id, self.later_row.id, self.row.id]},
            token=self.raw_token,
        )
        self.assertEqual(reorder_rows.status_code, 200)
        self.assertEqual(
            [row['name'] for row in reorder_rows.json()['rows']],
            ['This month', 'Later', 'Today'],
        )

        column_response = self.post(
            'add_column',
            {
                'grid_id': self.project.id,
                'name': 'Design',
                'after_column_id': self.column.id,
            },
            token=self.raw_token,
        )
        self.assertEqual(column_response.status_code, 201)
        design_id = column_response.json()['column']['id']
        self.assertFalse(column_response.json()['column']['is_category_column'])

        next_week = ColumnHeader.objects.create(
            project=self.project, name='Next week', order=3
        )
        reorder_columns = self.post(
            'reorder_columns',
            {
                'grid_id': self.project.id,
                'column_ids': [design_id, next_week.id, self.column.id],
            },
            token=self.raw_token,
        )
        self.assertEqual(reorder_columns.status_code, 200)
        data_names = [
            column['name']
            for column in reorder_columns.json()['columns']
            if not column['is_category_column']
        ]
        self.assertEqual(data_names, ['Design', 'Next week', 'This week'])
        self.assertTrue(reorder_columns.json()['columns'][0]['is_category_column'])
        self.assertTrue(TaskActivity.objects.filter(action='added row This month').exists())
        self.assertTrue(TaskActivity.objects.filter(action='reordered columns').exists())

    def test_reorder_rows_rejects_partial_list(self):
        response = self.post(
            'reorder_rows',
            {'grid_id': self.project.id, 'row_ids': [self.row.id]},
            token=self.raw_token,
        )
        self.assertEqual(response.status_code, 400)

    def test_regenerating_one_agent_does_not_revoke_another(self):
        ramble_token = PersonalAccessToken.issue_for_user(self.user, name='Ramble')
        PersonalAccessToken.issue_for_user(self.user, name='Research')
        new_research = PersonalAccessToken.issue_for_user(self.user, name='Research')

        self.assertEqual(self.post('list_grids', token=ramble_token).status_code, 200)
        self.assertEqual(self.post('list_grids', token=self.raw_token).status_code, 200)
        self.assertEqual(self.post('list_grids', token=new_research).status_code, 200)


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

    def test_generate_named_token_from_settings(self):
        self.client.login(email='settings@example.com', password='testpass123')
        response = self.client.post(
            reverse('accounts:mcp_token_generate'),
            {'name': 'Ramble'},
        )
        self.assertRedirects(
            response,
            reverse('accounts:account_settings'),
            fetch_redirect_response=False,
        )
        token = PersonalAccessToken.objects.get(user=self.user, name='Ramble')
        self.assertEqual(self.client.session['new_mcp_token_name'], 'Ramble')
        settings_page = self.client.get(reverse('accounts:account_settings'))
        self.assertContains(settings_page, 'Ramble')
        self.assertContains(settings_page, token.token_prefix)

    def test_revoke_token_from_settings(self):
        PersonalAccessToken.issue_for_user(self.user, name='Ramble')
        PersonalAccessToken.issue_for_user(self.user, name='Research')
        ramble = PersonalAccessToken.objects.get(user=self.user, name='Ramble')
        research = PersonalAccessToken.objects.get(user=self.user, name='Research')
        self.client.login(email='settings@example.com', password='testpass123')
        response = self.client.post(
            reverse('accounts:mcp_token_revoke', kwargs={'token_id': ramble.pk})
        )
        self.assertRedirects(response, reverse('accounts:account_settings'))
        self.assertFalse(PersonalAccessToken.objects.filter(pk=ramble.pk).exists())
        self.assertTrue(PersonalAccessToken.objects.filter(pk=research.pk).exists())

    @override_settings(DEBUG=True, MCP_SERVER_PUBLIC_URL='')
    def test_settings_shows_localhost_mcp_url_in_development(self):
        self.client.login(email='settings@example.com', password='testpass123')
        response = self.client.get(reverse('accounts:account_settings'))
        self.assertContains(response, 'http://localhost:3001/mcp')

    @override_settings(
        DEBUG=False,
        MCP_SERVER_PUBLIC_URL='',
        ALLOWED_HOSTS=['www.meettoad.co.uk', 'testserver'],
    )
    def test_settings_shows_current_host_mcp_url_in_production(self):
        self.client.login(email='settings@example.com', password='testpass123')
        response = self.client.get(
            reverse('accounts:account_settings'),
            HTTP_HOST='www.meettoad.co.uk',
            secure=True,
        )
        self.assertContains(response, 'https://www.meettoad.co.uk/mcp')
        self.assertNotContains(response, 'http://localhost:3001/mcp')
