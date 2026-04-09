"""SQLite-based checkpoint persistence for workflow execution.

Stores step-level execution state so workflows can resume after
interruption. Each workflow run gets a unique run_id, and step
states are updated as they progress.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from typing import TYPE_CHECKING

from .types import StepState, StepStatus

if TYPE_CHECKING:
    from pathlib import Path


class CheckpointStore:
    """Persistent workflow checkpoint backed by SQLite.

    Parameters
    ----------
    db_path
        Path to the SQLite database file. Use ``:memory:`` for testing.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                workflow_name TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                completed INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS step_states (
                run_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                output TEXT DEFAULT '',
                exit_code INTEGER DEFAULT -1,
                duration_ms INTEGER DEFAULT 0,
                attempt INTEGER DEFAULT 0,
                error TEXT DEFAULT '',
                PRIMARY KEY (run_id, step_id),
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            );
        """)
        self._conn.commit()

    def create_run(self, workflow_name: str) -> str:
        """Create a new run and return its unique ID."""
        run_id = uuid.uuid4().hex[:12]
        self._conn.execute(
            "INSERT INTO runs (run_id, workflow_name) VALUES (?, ?)",
            (run_id, workflow_name),
        )
        self._conn.commit()
        return run_id

    def save_step(self, run_id: str, state: StepState) -> None:
        """Upsert a step's execution state."""
        self._conn.execute(
            """INSERT INTO step_states (run_id, step_id, status, output, exit_code,
               duration_ms, attempt, error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (run_id, step_id) DO UPDATE SET
               status=excluded.status, output=excluded.output,
               exit_code=excluded.exit_code, duration_ms=excluded.duration_ms,
               attempt=excluded.attempt, error=excluded.error""",
            (
                run_id,
                state.step_id,
                state.status.value,
                state.output,
                state.exit_code,
                state.duration_ms,
                state.attempt,
                state.error,
            ),
        )
        self._conn.commit()

    def load_steps(self, run_id: str) -> dict[str, StepState]:
        """Load all step states for a run."""
        cursor = self._conn.execute(
            "SELECT step_id, status, output, exit_code, duration_ms, attempt, error "
            "FROM step_states WHERE run_id = ?",
            (run_id,),
        )
        steps: dict[str, StepState] = {}
        for row in cursor:
            steps[row[0]] = StepState(
                step_id=row[0],
                status=StepStatus(row[1]),
                output=row[2],
                exit_code=row[3],
                duration_ms=row[4],
                attempt=row[5],
                error=row[6],
            )
        return steps

    def mark_completed(self, run_id: str) -> None:
        """Mark a run as completed."""
        self._conn.execute(
            "UPDATE runs SET completed = 1 WHERE run_id = ?",
            (run_id,),
        )
        self._conn.commit()

    def get_incomplete_run(self, workflow_name: str) -> str | None:
        """Find the most recent incomplete run for a workflow, or None."""
        cursor = self._conn.execute(
            "SELECT run_id FROM runs WHERE workflow_name = ? AND completed = 0 "
            "ORDER BY created_at DESC LIMIT 1",
            (workflow_name,),
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def export_run(self, run_id: str) -> str:
        """Export a run's step states as JSON."""
        steps = self.load_steps(run_id)
        return json.dumps(
            {sid: s.to_dict() for sid, s in steps.items()},
            indent=2,
        )

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
