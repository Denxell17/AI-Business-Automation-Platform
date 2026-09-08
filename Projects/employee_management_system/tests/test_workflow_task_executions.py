from contextlib import closing
import re
import sqlite3
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from database import load_user_account_by_username, load_workflow_task_executions
from user_service import register_user_account
from web_app import create_web_application
from workflow_service import (
    create_workflow, create_workflow_task, update_workflow,
    start_workflow_execution, finish_workflow_execution_record,
    finish_workflow_task_execution_record,
)


class TestWorkflowTaskExecutions(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.db = Path(directory.name) / "tasks.db"
        for role in ("admin", "viewer"):
            register_user_account(role, "SecurePassword123!", role, self.db)
        self.admin = load_user_account_by_username("admin", self.db)
        self.viewer = load_user_account_by_username("viewer", self.db)
        self.assertTrue(create_workflow(self.admin, "WF", "Workflow", "", "draft", self.db))
        for position in (2, 1):
            self.assertTrue(create_workflow_task(
                self.admin, f"TASK-{position}", "WF", position,
                f"Snapshot {position}", "", "manual", True, self.db,
            ))
        self.assertTrue(update_workflow(self.admin, "WF", "Workflow", "", "active", self.db))
        self.run = start_workflow_execution(self.admin, "WF", self.db)
        self.tasks = self.load_tasks()
        self.client = TestClient(create_web_application(
            database_file=self.db, session_secret="task-execution-tests",
        ))
        self.addCleanup(self.client.close)
        logger = patch("web_app.log_activity")
        self.log = logger.start()
        self.addCleanup(logger.stop)
        self.url = (f"/workflows/WF/executions/{self.run['execution_id']}"
                    f"/tasks/{self.tasks[0]['task_execution_id']}/finish")

    def load_tasks(self):
        return load_workflow_task_executions(self.run["execution_id"], self.db)

    def finish(self, **changes):
        arguments = dict(
            current_user=self.admin, workflow_id="WF", execution_id=self.run["execution_id"],
            task_execution_id=self.tasks[0]["task_execution_id"], status="completed",
            result_summary="Done", database_file=self.db,
        )
        arguments.update(changes)
        return finish_workflow_task_execution_record(**arguments)

    def sign_in(self, username="admin"):
        self.client.post("/login", data={"username": username, "password": "SecurePassword123!"})
        page = self.client.get("/workflows/WF")
        self.log.reset_mock()
        match = re.search(r'name="csrf_token"\s+value="([^"]+)"', page.text)
        return match.group(1) if match else ""

    def post(self, token, **changes):
        data = dict(csrf_token=token, status="completed", result_summary="Done")
        data.update(changes)
        return self.client.post(self.url, data=data, follow_redirects=False)

    def test_normalized_outcomes_preserve_snapshots_and_are_terminal(self):
        self.assertEqual([task["sequence_number"] for task in self.tasks], [1, 2])
        self.assertEqual(load_workflow_task_executions("missing", self.db), [])
        self.assertTrue(self.finish(workflow_id=" wf ", status=" COMPLETED ", result_summary=" Done "))
        self.assertTrue(self.finish(task_execution_id=self.tasks[1]["task_execution_id"], status="failed"))
        saved = self.load_tasks()
        for original, task, status in zip(self.tasks, saved, ("completed", "failed")):
            self.assertEqual(task["status"], status)
            self.assertEqual(task["result_summary"], "Done")
            self.assertIsNotNone(datetime.fromisoformat(task["finished_at"]).tzinfo)
            for key in ("task_id", "task_title", "sequence_number", "started_at", "execution_id"):
                self.assertEqual(task[key], original[key])
        self.assertFalse(self.finish(status="failed"))
        self.assertEqual(self.load_tasks(), saved)

    def test_invalid_input_and_parent_mismatches_do_not_write(self):
        second_run = start_workflow_execution(self.admin, "WF", self.db)
        for changes in (
            {"status": "running"}, {"status": "unknown"}, {"status": None},
            {"result_summary": " "}, {"result_summary": 2}, {"workflow_id": ""},
            {"workflow_id": "OTHER"}, {"execution_id": second_run["execution_id"]},
            {"task_execution_id": "missing"},
        ):
            with self.subTest(changes=changes):
                self.assertFalse(self.finish(**changes))
        self.assertEqual(self.load_tasks(), self.tasks)

    def test_terminal_parent_rejects_task_updates(self):
        self.assertTrue(finish_workflow_execution_record(
            self.admin, self.run["execution_id"], "failed", "Stopped", self.db,
        ))
        self.assertFalse(self.finish())
        self.assertEqual(self.load_tasks(), self.tasks)
        self.sign_in()
        self.assertNotIn("Mark task completed", self.client.get("/workflows/WF").text)

    def test_service_revalidates_identity_activity_role_and_permission(self):
        for user in (self.viewer, dict(self.admin, is_active=False),
                     dict(self.admin, user_id=self.viewer["user_id"]),
                     dict(self.admin, username="missing")):
            self.assertFalse(self.finish(current_user=user))
        with patch("workflow_service.user_has_permission", return_value=False):
            self.assertFalse(self.finish())
        for assignment in ("is_active = 0", "is_active = 1, role = 'viewer'"):
            with closing(sqlite3.connect(self.db)) as connection, connection:
                connection.execute(f"UPDATE users SET {assignment} WHERE username = 'admin'")
            self.assertFalse(self.finish())
        self.assertEqual(self.load_tasks(), self.tasks)

    def test_browser_success_logs_and_displays_escaped_outcome(self):
        token = self.sign_in()
        page = self.client.get("/workflows/WF")
        self.assertIn("Task outcomes", page.text)
        self.assertIn(f'for="result-{self.tasks[0]["task_execution_id"]}"', page.text)
        self.assertIn("<legend>Update outcome: Snapshot 1</legend>", page.text)
        response = self.post(token, result_summary="<script>private</script>", status="failed")
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "http://testserver/workflows/WF")
        self.log.assert_called_once()
        self.assertIn("was failed by user admin", self.log.call_args.args[0])
        self.assertNotIn("private", self.log.call_args.args[0])
        page = self.client.get(response.headers["location"])
        self.assertIn("Status: Failed", page.text)
        self.assertIn("&lt;script&gt;private&lt;/script&gt;", page.text)
        self.assertNotIn(self.url, page.text)
        self.log.reset_mock()
        self.assertEqual(self.post(token).status_code, 400)
        self.log.assert_not_called()

    def test_anonymous_viewer_and_missing_permission_are_rejected_before_service(self):
        with patch("web_app.finish_workflow_task_execution_record") as service:
            self.assertEqual(self.post("bad").status_code, 303)
            self.sign_in("viewer")
            page = self.client.get("/workflows/WF")
            self.assertIn("Snapshot 1", page.text)
            self.assertNotIn("Mark task completed", page.text)
            self.assertEqual(self.post("bad").status_code, 403)
            self.assertIn("access denied", self.log.call_args.args[0])
            self.sign_in()
            with patch("web_app.user_has_permission", return_value=False):
                self.assertEqual(self.post("bad").status_code, 403)
            service.assert_not_called()

    def test_csrf_missing_invalid_and_other_session_tokens_are_rejected(self):
        old_token = self.sign_in()
        self.client.cookies.clear()
        self.sign_in()
        with patch("web_app.finish_workflow_task_execution_record") as service:
            for token in ("", "invalid", old_token):
                self.assertEqual(self.post(token).status_code, 403)
                self.assertIn("CSRF validation failed", self.log.call_args.args[0])
            service.assert_not_called()
        self.assertEqual(self.load_tasks(), self.tasks)

    def test_revoked_browser_account_cannot_update(self):
        token = self.sign_in()
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("UPDATE users SET is_active = 0 WHERE username = 'admin'")
        with patch("web_app.finish_workflow_task_execution_record") as service:
            self.assertEqual(self.post(token).status_code, 303)
            service.assert_not_called()

    def test_browser_validation_scope_and_storage_errors_are_safe(self):
        token = self.sign_in()
        self.assertEqual(self.client.get(self.url).status_code, 405)
        for data in ({"status": "unknown"}, {"result_summary": " "}):
            self.assertEqual(self.post(token, **data).status_code, 400)
        response = self.client.post(self.url.replace("/WF/", "/OTHER/"), data={
            "csrf_token": token, "status": "completed", "result_summary": "Done",
        })
        self.assertEqual(response.status_code, 400)
        with patch("web_app.finish_workflow_task_execution_record", side_effect=sqlite3.OperationalError("secret.db")):
            response = self.post(token)
            self.assertEqual(response.status_code, 500)
            self.assertNotIn("secret.db", response.text)
        with patch("web_app.load_workflow_task_executions", side_effect=sqlite3.OperationalError("secret.db")):
            response = self.client.get("/workflows/WF")
            self.assertEqual(response.status_code, 500)
            self.assertNotIn("secret.db", response.text)
        self.log.assert_not_called()
        self.assertEqual(self.load_tasks(), self.tasks)

    def test_repository_rolls_back_failed_write(self):
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("""CREATE TRIGGER reject_task_finish
                BEFORE UPDATE ON workflow_task_executions
                BEGIN SELECT RAISE(ABORT, 'test failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.finish()
        self.assertEqual(self.load_tasks(), self.tasks)
