import json

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from pages.models import Project, RowHeader, ColumnHeader, Task, TaskNote
from .models import (
    DecisionEntry,
    DecisionReview,
    PersonalAccessToken,
    MCPRequestLog,
    TaskActivity,
    user_has_agent_access,
)

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
                'create_grid',
                'get_grid',
                'update_grid',
                'add_task',
                'update_task',
                'delete_task',
                'add_row',
                'add_column',
                'reorder_rows',
                'reorder_columns',
                'rename_row',
                'rename_column',
                'delete_row',
                'delete_column',
                'log_request',
                'log_decision',
                'list_decisions',
                'get_decision',
            },
        )

    def test_create_grid_with_rows_columns_and_brief(self):
        response = self.post(
            'create_grid',
            {
                'name': 'My Stamp',
                'brief': 'Clinic listings. Never invent fees.',
                'rows': ['Twenty-preview test', 'Launch'],
                'columns': ['Setup & infra', 'Data & extraction'],
            },
            token=self.raw_token,
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body['ok'])
        self.assertEqual(body['name'], 'My Stamp')
        self.assertEqual(body['brief'], 'Clinic listings. Never invent fees.')
        self.assertEqual(
            [row['name'] for row in body['rows']],
            ['Twenty-preview test', 'Launch'],
        )
        data_columns = [
            column['name'] for column in body['columns'] if not column['is_category_column']
        ]
        self.assertEqual(data_columns, ['Setup & infra', 'Data & extraction'])
        self.assertTrue(body['columns'][0]['is_category_column'])
        self.assertEqual(body['tasks'], [])
        self.assertTrue(
            Project.objects.filter(pk=body['id'], user=self.user, name='My Stamp').exists()
        )
        self.assertTrue(TaskActivity.objects.filter(action='created grid My Stamp').exists())

    def test_create_grid_defaults_and_free_tier_limit(self):
        response = self.post('create_grid', {'name': 'Scratch'}, token=self.raw_token)
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual([row['name'] for row in body['rows']], ['To do'])
        data_columns = [
            column['name'] for column in body['columns'] if not column['is_category_column']
        ]
        self.assertEqual(data_columns, ['Scratch'])

        self.user.tier = 'free'
        self.user.save(update_fields=['tier'])
        blocked = self.post('create_grid', {'name': 'Too many'}, token=self.raw_token)
        self.assertEqual(blocked.status_code, 403)

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

    def test_rename_and_delete_rows_and_columns(self):
        renamed_row = self.post(
            'rename_row',
            {'row_id': self.later_row.id, 'name': 'Someday'},
            token=self.raw_token,
        )
        self.assertEqual(renamed_row.status_code, 200)
        self.assertEqual(renamed_row.json()['row']['name'], 'Someday')

        renamed_column = self.post(
            'rename_column',
            {'column_id': self.column.id, 'name': 'Now'},
            token=self.raw_token,
        )
        self.assertEqual(renamed_column.status_code, 200)
        self.assertEqual(renamed_column.json()['column']['name'], 'Now')

        extra_column = ColumnHeader.objects.create(
            project=self.project, name='Drop me', order=2
        )
        deleted_column = self.post(
            'delete_column',
            {'column_id': extra_column.id},
            token=self.raw_token,
        )
        self.assertEqual(deleted_column.status_code, 200)
        self.assertFalse(ColumnHeader.objects.filter(pk=extra_column.id).exists())

        deleted_row = self.post(
            'delete_row',
            {'row_id': self.later_row.id},
            token=self.raw_token,
        )
        self.assertEqual(deleted_row.status_code, 200)
        self.assertFalse(RowHeader.objects.filter(pk=self.later_row.id).exists())
        self.assertTrue(Task.objects.filter(pk=self.task.id).exists())
        self.assertTrue(TaskActivity.objects.filter(action='renamed row to Someday').exists())
        self.assertTrue(TaskActivity.objects.filter(action='deleted column Drop me').exists())

        blocked = self.post(
            'delete_column',
            {'column_id': self.category.id},
            token=self.raw_token,
        )
        self.assertEqual(blocked.status_code, 400)

        other = self.post(
            'rename_row',
            {
                'row_id': self.other_task.row_header_id,
                'name': 'Nope',
            },
            token=self.raw_token,
        )
        self.assertEqual(other.status_code, 404)

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

    def test_settings_explains_that_a_token_turns_on_the_decision_log(self):
        self.client.login(email='settings@example.com', password='testpass123')
        response = self.client.get(reverse('accounts:account_settings'))
        self.assertContains(
            response,
            'Creating a token turns on the agent decision log for your grids.',
        )


class DecisionLogTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='decisions@example.com',
            first_name='Tom',
            last_name='Barratt',
            password='testpass123',
            email_verified=True,
        )
        self.no_token_user = User.objects.create_user(
            email='notoken@example.com',
            first_name='No',
            last_name='Token',
            password='testpass123',
            email_verified=True,
        )
        self.raw_token = PersonalAccessToken.issue_for_user(self.user, name='Ramble Notes')
        self.token = PersonalAccessToken.objects.get(user=self.user, name='Ramble Notes')
        self.project = Project.objects.create(name='Work Grid', user=self.user)
        self.column = ColumnHeader.objects.create(
            project=self.project, name='This week', order=1
        )
        self.row = RowHeader.objects.create(project=self.project, name='Today', order=0)
        self.task = Task.objects.create(
            project=self.project,
            row_header=self.row,
            column_header=self.column,
            text='Write the stamp spec',
        )
        self.other_project = Project.objects.create(
            name='Other Grid', user=self.no_token_user
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

    def log_decision(self, extra=None, token=None):
        payload = {
            'grid_id': self.project.id,
            'task_id': self.task.id,
            'request': 'Should we freeze the hero?',
            'action_summary': 'Compared scroll options',
            'decision': 'Keep the hero frozen on scroll',
            'rationale': 'Matches the Ramble positioning',
            'sources': ['https://example.com/spec'],
            'requested_by': 'Tom',
        }
        if extra:
            payload.update(extra)
        return self.post('log_decision', payload, token=token if token is not None else self.raw_token)

    def test_user_without_token_has_no_access_and_gets_404(self):
        self.assertFalse(user_has_agent_access(self.no_token_user))
        self.client.login(email='notoken@example.com', password='testpass123')
        grid = Project.objects.create(name='Bare', user=self.no_token_user)
        task = Task.objects.create(
            project=grid,
            row_header=RowHeader.objects.create(project=grid, name='R', order=0),
            column_header=ColumnHeader.objects.create(project=grid, name='C', order=1),
            text='A task',
        )
        self.assertEqual(self.client.get(reverse('pages:decision_log')).status_code, 404)
        self.assertEqual(
            self.client.get(reverse('pages:grid_decision_log', kwargs={'pk': grid.pk})).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(reverse('pages:task_decision_log', kwargs={'task_pk': task.pk})).status_code,
            404,
        )
        list_page = self.client.get(reverse('pages:project_list'))
        self.assertNotContains(list_page, 'Decision log')
        grid_page = self.client.get(reverse('pages:project_grid', kwargs={'pk': grid.pk}))
        self.assertNotContains(grid_page, 'Decision log')
        self.assertNotContains(grid_page, 'Decisions')

    def test_creating_a_token_shows_the_decision_log(self):
        self.client.login(email='notoken@example.com', password='testpass123')
        PersonalAccessToken.issue_for_user(self.no_token_user, name='Grok Bot')
        self.assertTrue(user_has_agent_access(self.no_token_user))
        grid = Project.objects.create(name='Now live', user=self.no_token_user)
        response = self.client.get(reverse('pages:decision_log'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Decision log')
        grid_page = self.client.get(reverse('pages:project_grid', kwargs={'pk': grid.pk}))
        self.assertContains(grid_page, 'Decision log')

    def test_revoking_all_tokens_hides_ui_but_keeps_entries(self):
        logged = self.log_decision()
        self.assertEqual(logged.status_code, 201)
        entry_id = logged.json()['id']
        self.assertTrue(DecisionEntry.objects.filter(pk=entry_id).exists())

        self.client.login(email='decisions@example.com', password='testpass123')
        visible = self.client.get(reverse('pages:decision_log'))
        self.assertEqual(visible.status_code, 200)
        self.assertContains(visible, 'Keep the hero frozen on scroll')

        self.token.delete()
        self.assertFalse(user_has_agent_access(self.user))
        hidden = self.client.get(reverse('pages:decision_log'))
        self.assertEqual(hidden.status_code, 404)
        nav = self.client.get(reverse('pages:project_list'))
        self.assertNotContains(nav, 'Decision log')
        entry = DecisionEntry.objects.get(pk=entry_id)
        self.assertEqual(entry.decision, 'Keep the hero frozen on scroll')
        self.assertIsNone(entry.token_id)

        PersonalAccessToken.issue_for_user(self.user, name='Ramble Notes')
        shown_again = self.client.get(reverse('pages:decision_log'))
        self.assertEqual(shown_again.status_code, 200)
        self.assertContains(shown_again, 'Keep the hero frozen on scroll')

    def test_log_decision_returns_id_and_created_at_and_sets_needs_review(self):
        response = self.log_decision()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertIn('id', body)
        self.assertIn('created_at', body)
        self.assertEqual(body['agent_name'], 'Ramble Notes')
        self.assertEqual(body['requested_by'], 'Tom')
        self.assertEqual(body['status'], DecisionEntry.STATUS_PENDING)
        self.assertEqual(body['sources'], ['https://example.com/spec'])
        self.task.refresh_from_db()
        self.assertTrue(self.task.needs_review)
        entry = DecisionEntry.objects.get(pk=body['id'])
        self.assertEqual(entry.token_id, self.token.id)
        self.assertEqual(entry.task_id_snapshot, self.task.id)
        self.assertEqual(entry.task_text_snapshot, 'Write the stamp spec')

    def test_mcp_tools_return_ids_and_reject_unknown_fields(self):
        created = self.mcp_rpc(
            'tools/call',
            {
                'name': 'log_decision',
                'arguments': {
                    'grid_id': self.project.id,
                    'request': 'Ship it?',
                    'action_summary': 'Checked the brief',
                    'decision': 'Ship on Friday',
                    'requested_by': 'Tom',
                },
            },
            token=self.raw_token,
        )
        self.assertEqual(created.status_code, 200)
        result = created.json()['result']
        self.assertFalse(result['isError'])
        self.assertIn('id', result['structuredContent'])
        self.assertIn('created_at', result['structuredContent'])
        decision_id = result['structuredContent']['id']

        unknown = self.mcp_rpc(
            'tools/call',
            {
                'name': 'log_decision',
                'arguments': {
                    'grid_id': self.project.id,
                    'request': 'Ship it?',
                    'action_summary': 'Checked the brief',
                    'decision': 'Ship on Friday',
                    'secret_note': 'drop this',
                },
            },
            token=self.raw_token,
        )
        unknown_result = unknown.json()['result']
        self.assertTrue(unknown_result['isError'])
        self.assertIn('Unknown field', unknown_result['structuredContent']['error'])

        listed = self.post(
            'list_decisions',
            {'grid_id': self.project.id, 'unexpected': True},
            token=self.raw_token,
        )
        self.assertEqual(listed.status_code, 400)

        fetched = self.post('get_decision', {'decision_id': decision_id}, token=self.raw_token)
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()['id'], decision_id)
        self.assertIn('reviews', fetched.json())
        self.assertIn('supersede_chain', fetched.json())

    def test_entries_cannot_be_edited_or_deleted_through_api_or_admin(self):
        body = self.log_decision().json()
        entry = DecisionEntry.objects.get(pk=body['id'])
        original = entry.decision
        entry.decision = 'tamper via save'
        with self.assertRaises(ValueError):
            entry.save()
        entry.refresh_from_db()
        self.assertEqual(entry.decision, original)
        with self.assertRaises(ValueError):
            entry.delete()
        self.assertTrue(DecisionEntry.objects.filter(pk=entry.pk).exists())

        from django.contrib.admin.sites import site
        from django.test import RequestFactory
        from mcp_api.admin import DecisionEntryAdmin, DecisionReviewAdmin

        factory = RequestFactory()
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            password='testpass123',
        )
        request = factory.get('/admin/')
        request.user = admin_user
        entry_admin = DecisionEntryAdmin(DecisionEntry, site)
        review_admin = DecisionReviewAdmin(DecisionReview, site)
        self.assertFalse(entry_admin.has_add_permission(request))
        self.assertFalse(entry_admin.has_change_permission(request, entry))
        self.assertFalse(entry_admin.has_delete_permission(request, entry))
        self.assertFalse(review_admin.has_add_permission(request))
        self.assertFalse(review_admin.has_change_permission(request))
        self.assertFalse(review_admin.has_delete_permission(request))

    def test_review_creates_event_and_changes_only_status_fields(self):
        body = self.log_decision().json()
        entry = DecisionEntry.objects.get(pk=body['id'])
        before = {
            field.attname: getattr(entry, field.attname)
            for field in DecisionEntry._meta.concrete_fields
        }
        self.client.login(email='decisions@example.com', password='testpass123')
        response = self.client.post(
            reverse('pages:decision_review', kwargs={'decision_id': entry.pk}),
            {'status': 'approved', 'comment': 'Looks right', 'next': reverse('pages:decision_log')},
        )
        self.assertEqual(response.status_code, 302)
        entry.refresh_from_db()
        after = {
            field.attname: getattr(entry, field.attname)
            for field in DecisionEntry._meta.concrete_fields
        }
        changed = {name for name, value in after.items() if before[name] != value}
        self.assertEqual(changed, {'status', 'reviewer', 'reviewed_at', 'review_comment'})
        self.assertEqual(entry.status, DecisionEntry.STATUS_APPROVED)
        self.assertEqual(entry.reviewer, 'Tom Barratt')
        self.assertEqual(entry.review_comment, 'Looks right')
        review = DecisionReview.objects.get(entry=entry)
        self.assertEqual(review.old_status, DecisionEntry.STATUS_PENDING)
        self.assertEqual(review.new_status, DecisionEntry.STATUS_APPROVED)
        self.assertEqual(review.comment, 'Looks right')
        self.assertEqual(review.actor, 'Tom Barratt')
        self.task.refresh_from_db()
        self.assertFalse(self.task.needs_review)
        self.assertEqual(self.task.owner, Task.OWNER_YOU)

    def test_deleting_a_task_keeps_entries_with_snapshots(self):
        body = self.log_decision().json()
        task_id = self.task.id
        self.post('delete_task', {'task_id': task_id}, token=self.raw_token)
        self.assertFalse(Task.objects.filter(pk=task_id).exists())
        entry = DecisionEntry.objects.get(pk=body['id'])
        self.assertIsNone(entry.task_id)
        self.assertEqual(entry.task_id_snapshot, task_id)
        self.assertEqual(entry.task_text_snapshot, 'Write the stamp spec')
        listed = self.post(
            'list_decisions',
            {'task_id': task_id},
            token=self.raw_token,
        )
        self.assertEqual(listed.json()['decisions'][0]['id'], entry.id)

    def test_hash_chain_verifies_and_detects_tampering(self):
        first = self.log_decision().json()
        second = self.log_decision({
            'request': 'Second call',
            'decision': 'Leave the fees as documented',
            'supersedes': first['id'],
        }).json()
        from mcp_api.services import verify_decision_chain
        intact = verify_decision_chain(self.user)
        self.assertTrue(intact['ok'])
        self.assertEqual(intact['checked'], 2)
        first_entry = DecisionEntry.objects.get(pk=first['id'])
        self.assertEqual(first_entry.status, DecisionEntry.STATUS_SUPERSEDED)
        self.assertEqual(second['prev_hash'], first['entry_hash'])
        self.assertNotEqual(second['entry_hash'], first['entry_hash'])

        DecisionEntry.objects.filter(pk=second['id']).update(decision='tampered in the database')
        broken = verify_decision_chain(self.user)
        self.assertFalse(broken['ok'])
        self.assertEqual(broken['broken'][0]['id'], second['id'])

        self.client.login(email='decisions@example.com', password='testpass123')
        verify = self.client.post(reverse('pages:decision_log_verify'))
        self.assertRedirects(
            verify,
            reverse('pages:decision_log'),
            fetch_redirect_response=False,
        )
        page = self.client.get(reverse('pages:decision_log'))
        self.assertContains(page, 'Chain broken')

    def test_passed_agent_name_is_stored(self):
        response = self.log_decision({'agent': 'Toad'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['agent_name'], 'Toad')

    def test_csv_export_requires_agent_access(self):
        self.log_decision()
        self.client.login(email='notoken@example.com', password='testpass123')
        self.assertEqual(self.client.get(reverse('pages:decision_log_export')).status_code, 404)
        self.client.login(email='decisions@example.com', password='testpass123')
        csv_response = self.client.get(reverse('pages:decision_log_export'))
        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response['Content-Type'], 'text/csv')
        self.assertIn(b'Keep the hero frozen on scroll', csv_response.content)

