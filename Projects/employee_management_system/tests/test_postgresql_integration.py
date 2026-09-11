import os
import re
import unittest
from unittest.mock import patch
from uuid import uuid4

import psycopg
from fastapi.testclient import TestClient

from database import (
    claim_workflow_schedule_occurrence,
    insert_agent_template,
    insert_employee,
    insert_user_account,
    insert_workflow,
    insert_workflow_execution,
    insert_workflow_schedule,
    insert_workflow_task,
    insert_workflow_task_executions,
    load_agent_template_by_id,
    load_agent_templates_from_database,
    load_employees_from_database,
    load_user_account_by_username,
    load_workflow_by_id,
    load_workflow_executions,
    load_workflow_schedule_occurrences,
    load_workflow_schedules,
    load_workflow_task_executions,
    load_workflow_tasks,
)
from user_service import register_user_account
from web_app import create_web_application


TEST_DATABASE_URL = os.environ.get(
    "ABAP_TEST_DATABASE_URL",
    "",
).strip()

TEST_TIMESTAMP = "2026-09-10T00:00:00+00:00"


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "ABAP_TEST_DATABASE_URL is required for live PostgreSQL tests.",
)
class TestLivePostgresqlIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.environment = patch.dict(
            os.environ,
            {
                "DATABASE_BACKEND": "postgresql",
                "DATABASE_URL": TEST_DATABASE_URL,
            },
        )
        cls.environment.start()

    @classmethod
    def tearDownClass(cls):
        cls.environment.stop()

    def setUp(self):
        suffix = uuid4().hex[:12]

        self.username = f"day143_{suffix}"
        self.agent_template_id = f"AGENT-{suffix}"
        self.employee_id = f"EMP-{suffix}"
        self.workflow_id = f"WF-{suffix}"
        self.task_id = f"TASK-{suffix}"
        self.execution_id = f"RUN-{suffix}"
        self.task_execution_id = f"TASK-RUN-{suffix}"
        self.schedule_id = f"SCHEDULE-{suffix}"
        self.occurrence_id = f"OCCURRENCE-{suffix}"

    def tearDown(self):
        with psycopg.connect(TEST_DATABASE_URL) as connection:
            connection.execute(
                """
                DELETE FROM workflow_task_executions
                WHERE task_execution_id = %s
                """,
                (self.task_execution_id,),
            )
            connection.execute(
                """
                DELETE FROM workflow_executions
                WHERE execution_id = %s
                """,
                (self.execution_id,),
            )
            connection.execute(
                """
                DELETE FROM workflow_schedule_occurrences
                WHERE occurrence_id = %s
                """,
                (self.occurrence_id,),
            )
            connection.execute(
                """
                DELETE FROM workflow_schedules
                WHERE schedule_id = %s
                """,
                (self.schedule_id,),
            )
            connection.execute(
                """
                DELETE FROM workflow_tasks
                WHERE task_id = %s
                """,
                (self.task_id,),
            )
            connection.execute(
                """
                DELETE FROM workflows
                WHERE workflow_id = %s
                """,
                (self.workflow_id,),
            )
            connection.execute(
                """
                DELETE FROM employees
                WHERE employee_id = %s
                """,
                (self.employee_id,),
            )
            connection.execute(
                """
                DELETE FROM agent_templates
                WHERE UPPER(agent_template_id) = UPPER(%s)
                """,
                (self.agent_template_id,),
            )
            connection.execute(
                """
                DELETE FROM users
                WHERE username = %s
                """,
                (self.username,),
            )

    def test_agent_template_browser_round_trip_uses_live_postgresql(
        self,
    ):
        password = "Day145PostgresqlPassword123!"
        template_name = (
            f"Day 145 Browser Agent {self.agent_template_id}"
        )

        self.assertTrue(
            register_user_account(
                self.username,
                password,
                "admin",
            )
        )

        application = create_web_application(
            session_secret=(
                "day-145-live-postgresql-browser-test"
            ),
        )

        with TestClient(application) as client:
            login_response = client.post(
                "/login",
                data={
                    "username": self.username,
                    "password": password,
                },
                follow_redirects=False,
            )

            self.assertEqual(
                login_response.status_code,
                303,
            )

            form_response = client.get(
                "/agent-templates/new"
            )

            self.assertEqual(
                form_response.status_code,
                200,
            )

            token_match = re.search(
                r'name="csrf_token"\s+value="([^"]+)"',
                form_response.text,
            )
            self.assertIsNotNone(token_match)

            if token_match is None:
                self.fail(
                    "Live PostgreSQL form did not contain "
                    "a CSRF token."
                )

            csrf_token = token_match.group(1)

            create_response = client.post(
                "/agent-templates/new",
                data={
                    "csrf_token": csrf_token,
                    "agent_template_id": (
                        self.agent_template_id
                    ),
                    "name": template_name,
                    "description": (
                        "Created through the live PostgreSQL "
                        "browser integration test."
                    ),
                    "system_prompt": (
                        "Assist the user clearly and protect "
                        "private business information."
                    ),
                    "model_name": "gpt-5.6-terra",
                    "status": "draft",
                },
                follow_redirects=False,
            )

            self.assertEqual(
                create_response.status_code,
                303,
            )
            self.assertEqual(
                create_response.headers["location"],
                "http://testserver/agent-templates",
            )

            directory_response = client.get(
                "/agent-templates"
            )

            self.assertEqual(
                directory_response.status_code,
                200,
            )
            self.assertIn(
                self.agent_template_id.upper(),
                directory_response.text,
            )
            self.assertIn(
                template_name,
                directory_response.text,
            )
            self.assertIn(
                "gpt-5.6-terra",
                directory_response.text,
            )
            self.assertIn(
                "Draft",
                directory_response.text,
            )
            self.assertNotIn(
                "Assist the user clearly and protect "
                "private business information.",
                directory_response.text,
            )
            edit_form_response = client.get(
                (
                    "/agent-templates/"
                    f"{self.agent_template_id}/edit"
                )
            )

            self.assertEqual(
                edit_form_response.status_code,
                200,
            )

            edit_token_match = re.search(
                r'name="csrf_token"\s+value="([^"]+)"',
                edit_form_response.text,
            )
            self.assertIsNotNone(edit_token_match)

            if edit_token_match is None:
                self.fail(
                    "Live PostgreSQL edit form did not "
                    "contain a CSRF token."
                )

            edit_csrf_token = edit_token_match.group(1)
            updated_name = (
                "Day 146 Active Agent "
                f"{self.agent_template_id.upper()}"
            )
            updated_system_prompt = (
                "Use the reviewed Day 146 instructions."
            )

            edit_response = client.post(
                (
                    "/agent-templates/"
                    f"{self.agent_template_id}/edit"
                ),
                data={
                    "csrf_token": edit_csrf_token,
                    "expected_status": "draft",
                    "name": updated_name,
                    "description": (
                        "Updated through the live PostgreSQL "
                        "browser lifecycle test."
                    ),
                    "system_prompt": updated_system_prompt,
                    "model_name": "gpt-6-astra",
                    "status": "active",
                },
                follow_redirects=False,
            )

            self.assertEqual(
                edit_response.status_code,
                303,
            )
            self.assertEqual(
                edit_response.headers["location"],
                (
                    "http://testserver/agent-templates/"
                    f"{self.agent_template_id.upper()}"
                ),
            )

            stored_template = load_agent_template_by_id(
                self.agent_template_id.upper()
            )

            self.assertIsNotNone(stored_template)

            if stored_template is None:
                self.fail(
                    "The live PostgreSQL browser update "
                    "was not stored."
                )

            self.assertEqual(
                stored_template["name"],
                updated_name,
            )
            self.assertEqual(
                stored_template["system_prompt"],
                updated_system_prompt,
            )
            self.assertEqual(
                stored_template["model_name"],
                "gpt-6-astra",
            )
            self.assertEqual(
                stored_template["status"],
                "active",
            )

            detail_response = client.get(
                (
                    "/agent-templates/"
                    f"{self.agent_template_id}"
                )
            )

            self.assertEqual(
                detail_response.status_code,
                200,
            )
            self.assertIn(
                updated_name,
                detail_response.text,
            )
            self.assertIn(
                updated_system_prompt,
                detail_response.text,
            )
            self.assertIn(
                "gpt-6-astra",
                detail_response.text,
            )
            self.assertIn(
                "Active",
                detail_response.text,
            )

    def test_repository_round_trip_uses_live_postgresql(self):
        self.assertTrue(
            insert_user_account(
                self.username,
                "day143_protected_password_hash",
                "admin",
            )
        )

        account = load_user_account_by_username(
            self.username.upper()
        )

        self.assertIsNotNone(account)
        self.assertEqual(account["username"], self.username)
        self.assertTrue(account["is_active"])

        agent_template = {
            "agent_template_id": self.agent_template_id,
            "name": "Day 144 Agent Template",
            "description": (
                "Live PostgreSQL agent-template verification."
            ),
            "system_prompt": (
                "Assist the user clearly and protect private data."
            ),
            "model_name": "gpt-5.6-terra",
            "status": "draft",
            "created_by_user_id": account["user_id"],
            "created_at": TEST_TIMESTAMP,
            "updated_at": TEST_TIMESTAMP,
        }

        self.assertTrue(
            insert_agent_template(agent_template)
        )
        self.assertEqual(
            load_agent_template_by_id(
                self.agent_template_id
            ),
            agent_template,
        )

        stored_templates = (
            load_agent_templates_from_database()
        )

        self.assertIn(
            agent_template,
            stored_templates,
        )

        employee = {
            "employee_id": self.employee_id,
            "name": "Day 143 Employee",
            "department": "Engineering",
            "position": "Integration Tester",
            "country": "Philippines",
            "salary": 75000,
            "email": "day143@example.com",
            "phone_number": "+63-900-000-0143",
            "years_of_experience": 5,
            "company": "ABAP",
            "employment_status": "Active",
            "performance_score": 85,
        }

        self.assertTrue(insert_employee(employee))

        stored_employees = load_employees_from_database()
        stored_employee = next(
            record
            for record in stored_employees
            if record["employee_id"] == self.employee_id
        )

        self.assertEqual(stored_employee, employee)

        workflow = {
            "workflow_id": self.workflow_id,
            "name": "Day 143 PostgreSQL Workflow",
            "description": "Live PostgreSQL integration verification.",
            "status": "active",
            "created_by_user_id": account["user_id"],
            "created_at": TEST_TIMESTAMP,
            "updated_at": TEST_TIMESTAMP,
        }

        self.assertTrue(insert_workflow(workflow))
        self.assertEqual(
            load_workflow_by_id(self.workflow_id),
            workflow,
        )

        task = {
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "sequence_number": 1,
            "title": "Verify PostgreSQL",
            "instructions": "Confirm the live repository round trip.",
            "task_type": "manual",
            "is_required": True,
            "created_at": TEST_TIMESTAMP,
            "updated_at": TEST_TIMESTAMP,
        }

        self.assertTrue(insert_workflow_task(task))
        self.assertEqual(
            load_workflow_tasks(self.workflow_id),
            [task],
        )

        execution = {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "workflow_name": workflow["name"],
            "status": "running",
            "started_by_user_id": account["user_id"],
            "started_at": TEST_TIMESTAMP,
            "finished_at": None,
            "result_summary": "",
        }

        self.assertTrue(insert_workflow_execution(execution))
        self.assertEqual(
            load_workflow_executions(self.workflow_id),
            [execution],
        )

        task_execution = {
            "task_execution_id": self.task_execution_id,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "sequence_number": 1,
            "task_title": task["title"],
            "status": "running",
            "started_at": TEST_TIMESTAMP,
            "finished_at": None,
            "result_summary": "",
        }

        self.assertTrue(
            insert_workflow_task_executions(
                [task_execution]
            )
        )
        self.assertEqual(
            load_workflow_task_executions(
                self.execution_id
            ),
            [task_execution],
        )

        schedule = {
            "schedule_id": self.schedule_id,
            "workflow_id": self.workflow_id,
            "schedule_type": "manual",
            "scheduled_time": None,
            "day_of_week": None,
            "is_enabled": True,
            "created_by_user_id": account["user_id"],
            "created_at": TEST_TIMESTAMP,
            "updated_at": TEST_TIMESTAMP,
        }

        self.assertTrue(insert_workflow_schedule(schedule))
        self.assertEqual(
            load_workflow_schedules(self.workflow_id),
            [schedule],
        )

        occurrence = {
            "occurrence_id": self.occurrence_id,
            "schedule_id": self.schedule_id,
            "workflow_id": self.workflow_id,
            "scheduled_for_utc": TEST_TIMESTAMP,
            "claimed_at": TEST_TIMESTAMP,
        }

        self.assertTrue(
            claim_workflow_schedule_occurrence(occurrence)
        )
        self.assertFalse(
            claim_workflow_schedule_occurrence(occurrence)
        )
        self.assertEqual(
            load_workflow_schedule_occurrences(
                self.workflow_id
            ),
            [occurrence],
        )


if __name__ == "__main__":
    unittest.main()
