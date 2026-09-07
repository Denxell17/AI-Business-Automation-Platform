import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    initialize_database,
    insert_user_account,
    insert_workflow,
    insert_workflow_task,
    load_user_account_by_username,
    load_workflow_tasks,
)


class TestWorkflowTasks(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database_file = Path(directory.name) / "tasks.db"
        self.assertTrue(insert_user_account(
            "admin", "test-hash", "admin", self.database_file,
        ))
        user = load_user_account_by_username("admin", self.database_file)
        for workflow_id in ("WF-001", "WF-002"):
            self.assertTrue(insert_workflow({
                "workflow_id": workflow_id,
                "name": "Onboarding",
                "description": "",
                "status": "draft",
                "created_by_user_id": user["user_id"],
                "created_at": "2026-09-07T00:00:00+00:00",
                "updated_at": "2026-09-07T00:00:00+00:00",
            }, self.database_file))
        self.task = {
            "task_id": "WFT-001",
            "workflow_id": "WF-001",
            "sequence_number": 1,
            "title": "Confirm documents",
            "instructions": "Review the employee's documents.",
            "task_type": "manual",
            "is_required": True,
            "created_at": "2026-09-07T00:00:00+00:00",
            "updated_at": "2026-09-07T00:00:00+00:00",
        }

    def test_round_trip_preserves_fields_and_boolean(self):
        for required in (True, False):
            with self.subTest(required=required):
                task = dict(self.task, task_id=f"TASK-{required}",
                            sequence_number=1 if required else 2,
                            is_required=required)
                self.assertTrue(insert_workflow_task(task, self.database_file))
                saved = load_workflow_tasks("WF-001", self.database_file)[-1]
                self.assertEqual(saved, task)
                self.assertIs(saved["is_required"], required)

    def test_tasks_are_ordered_and_scoped_to_workflow(self):
        second = dict(self.task, task_id="SECOND", sequence_number=2)
        other = dict(self.task, task_id="OTHER", workflow_id="WF-002")
        for task in (second, other, self.task):
            self.assertTrue(insert_workflow_task(task, self.database_file))
        self.assertEqual(load_workflow_tasks("WF-001", self.database_file),
                         [self.task, second])
        self.assertEqual(load_workflow_tasks("WF-002", self.database_file),
                         [other])

    def test_empty_and_unknown_workflows_return_empty_list(self):
        for workflow_id in ("WF-001", "MISSING", "' OR 1=1 --"):
            self.assertEqual(load_workflow_tasks(workflow_id, self.database_file), [])

    def test_invalid_records_are_rejected_without_saving(self):
        invalid_fields = [
            {"task_id": ""}, {"task_id": "   "}, {"task_id": None},
            {"workflow_id": "MISSING"},
            {"sequence_number": 0}, {"sequence_number": -1},
            {"sequence_number": 1.5},
            {"title": "   "}, {"task_type": "email"}, {"is_required": 2},
        ]
        for fields in invalid_fields:
            with self.subTest(fields=fields):
                self.assertFalse(insert_workflow_task(
                    dict(self.task, **fields), self.database_file,
                ))
                self.assertEqual(load_workflow_tasks("WF-001", self.database_file), [])

    def test_duplicate_id_and_sequence_preserve_original(self):
        self.assertTrue(insert_workflow_task(self.task, self.database_file))
        for fields in ({"sequence_number": 2}, {"task_id": "NEW-ID"}):
            self.assertFalse(insert_workflow_task(
                dict(self.task, **fields), self.database_file,
            ))
        self.assertEqual(load_workflow_tasks("WF-001", self.database_file), [self.task])

    def test_reinitialization_preserves_tasks(self):
        self.assertTrue(insert_workflow_task(self.task, self.database_file))
        initialize_database(self.database_file)
        self.assertEqual(load_workflow_tasks("WF-001", self.database_file), [self.task])
