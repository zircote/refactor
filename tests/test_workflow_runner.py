"""Tests for the workflow runner module.

Covers DAG construction, cycle detection, topological ordering, executor
with bash steps, checkpoint persistence, dry-run mode, retry, trigger
rules, and workflow loading.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from scripts.workflow_runner import (
    CheckpointStore,
    CyclicDependencyError,
    WorkflowDAG,
    WorkflowExecutor,
    WorkflowValidationError,
)
from scripts.workflow_runner.loader import load_workflow
from scripts.workflow_runner.types import NodeDefinition, StepStatus, TriggerRule

# ---------------------------------------------------------------------------
# DAG construction
# ---------------------------------------------------------------------------


class TestWorkflowDAG:
    """Tests for DAG construction and topological sorting."""

    def test_simple_linear_dag(self) -> None:
        nodes: list[NodeDefinition] = [
            {"node_id": "a", "bash": "echo a"},
            {"node_id": "b", "bash": "echo b", "depends_on": ["a"]},
            {"node_id": "c", "bash": "echo c", "depends_on": ["b"]},
        ]
        dag = WorkflowDAG(nodes)
        order = dag.topological_order()
        assert order.index("a") < order.index("b") < order.index("c")

    def test_parallel_nodes(self) -> None:
        nodes: list[NodeDefinition] = [
            {"node_id": "root", "bash": "echo root"},
            {"node_id": "a", "bash": "echo a", "depends_on": ["root"]},
            {"node_id": "b", "bash": "echo b", "depends_on": ["root"]},
            {"node_id": "join", "bash": "echo join", "depends_on": ["a", "b"]},
        ]
        dag = WorkflowDAG(nodes)
        layers = dag.get_layers()
        assert layers[0] == ["root"]
        assert sorted(layers[1]) == ["a", "b"]
        assert layers[2] == ["join"]

    def test_cycle_detection(self) -> None:
        nodes: list[NodeDefinition] = [
            {"node_id": "a", "bash": "echo a", "depends_on": ["b"]},
            {"node_id": "b", "bash": "echo b", "depends_on": ["a"]},
        ]
        dag = WorkflowDAG(nodes)
        with pytest.raises(CyclicDependencyError):
            dag.get_layers()

    def test_duplicate_id_rejected(self) -> None:
        nodes: list[NodeDefinition] = [
            {"node_id": "a", "bash": "echo a"},
            {"node_id": "a", "bash": "echo a2"},
        ]
        with pytest.raises(WorkflowValidationError, match="duplicate"):
            WorkflowDAG(nodes)

    def test_missing_dependency_rejected(self) -> None:
        nodes: list[NodeDefinition] = [
            {"node_id": "a", "bash": "echo a", "depends_on": ["missing"]},
        ]
        with pytest.raises(WorkflowValidationError, match="unknown node"):
            WorkflowDAG(nodes)

    def test_missing_id_rejected(self) -> None:
        nodes: list[NodeDefinition] = [
            {"bash": "echo a"},  # type: ignore[typeddict-item]
        ]
        with pytest.raises(WorkflowValidationError, match="validation failed"):
            WorkflowDAG(nodes)

    def test_single_node(self) -> None:
        nodes: list[NodeDefinition] = [{"node_id": "only", "bash": "echo only"}]
        dag = WorkflowDAG(nodes)
        assert dag.get_layers() == [["only"]]
        assert len(dag) == 1
        assert "only" in dag

    def test_node_ids_preserves_order(self) -> None:
        nodes: list[NodeDefinition] = [
            {"node_id": "c", "bash": "echo c"},
            {"node_id": "a", "bash": "echo a"},
            {"node_id": "b", "bash": "echo b"},
        ]
        dag = WorkflowDAG(nodes)
        assert dag.node_ids == ["c", "a", "b"]

    def test_get_node(self) -> None:
        nodes: list[NodeDefinition] = [{"node_id": "x", "bash": "echo x"}]
        dag = WorkflowDAG(nodes)
        assert dag.get_node("x")["bash"] == "echo x"

    def test_layers_cached(self) -> None:
        nodes: list[NodeDefinition] = [{"node_id": "a", "bash": "echo a"}]
        dag = WorkflowDAG(nodes)
        layers1 = dag.get_layers()
        layers2 = dag.get_layers()
        assert layers1 is layers2


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------


class TestWorkflowExecutor:
    """Tests for workflow execution."""

    def test_execute_bash_steps(self) -> None:
        nodes: list[NodeDefinition] = [
            {"node_id": "greet", "bash": "echo hello"},
            {"node_id": "count", "bash": "echo world", "depends_on": ["greet"]},
        ]
        dag = WorkflowDAG(nodes, workflow_name="test")
        executor = WorkflowExecutor(dag)
        results = executor.run()
        assert results["greet"].status == StepStatus.COMPLETED
        assert results["count"].status == StepStatus.COMPLETED
        assert "hello" in results["greet"].output
        assert "world" in results["count"].output

    def test_dry_run(self) -> None:
        nodes: list[NodeDefinition] = [
            {"node_id": "a", "bash": "echo a"},
            {"node_id": "b", "bash": "exit 1", "depends_on": ["a"]},
        ]
        dag = WorkflowDAG(nodes, workflow_name="test")
        executor = WorkflowExecutor(dag, dry_run=True)
        results = executor.run()
        assert all(s.status == StepStatus.COMPLETED for s in results.values())
        assert results["b"].output == "[dry-run] skipped"

    def test_failed_step_skips_dependents(self) -> None:
        nodes: list[NodeDefinition] = [
            {"node_id": "fail", "bash": "exit 1"},
            {"node_id": "after", "bash": "echo ok", "depends_on": ["fail"]},
        ]
        dag = WorkflowDAG(nodes, workflow_name="test")
        executor = WorkflowExecutor(dag)
        results = executor.run()
        assert results["fail"].status == StepStatus.FAILED
        assert results["after"].status == StepStatus.SKIPPED

    def test_retry_on_failure(self) -> None:
        nodes: list[NodeDefinition] = [
            {
                "node_id": "flaky",
                "bash": "exit 1",
                "retry": {"max_attempts": 2, "delay_ms": 0},
            },
        ]
        dag = WorkflowDAG(nodes, workflow_name="test")
        executor = WorkflowExecutor(dag)
        results = executor.run()
        assert results["flaky"].status == StepStatus.FAILED
        assert results["flaky"].attempt == 2

    def test_skill_node_completes(self) -> None:
        nodes: list[NodeDefinition] = [
            {"node_id": "explore", "skill": "refactor:code-explorer"},
        ]
        dag = WorkflowDAG(nodes, workflow_name="test")
        executor = WorkflowExecutor(dag)
        results = executor.run()
        assert results["explore"].status == StepStatus.COMPLETED
        assert "[skill]" in results["explore"].output

    def test_trigger_rule_all_done(self) -> None:
        nodes: list[NodeDefinition] = [
            {"node_id": "a", "bash": "exit 1"},
            {"node_id": "b", "bash": "echo ok"},
            {
                "node_id": "join",
                "bash": "echo joined",
                "depends_on": ["a", "b"],
                "trigger_rule": "all_done",
            },
        ]
        dag = WorkflowDAG(nodes, workflow_name="test")
        executor = WorkflowExecutor(dag)
        results = executor.run()
        assert results["a"].status == StepStatus.FAILED
        assert results["join"].status == StepStatus.COMPLETED

    def test_trigger_rule_one_success(self) -> None:
        nodes: list[NodeDefinition] = [
            {"node_id": "a", "bash": "exit 1"},
            {"node_id": "b", "bash": "echo ok"},
            {
                "node_id": "join",
                "bash": "echo joined",
                "depends_on": ["a", "b"],
                "trigger_rule": "one_success",
            },
        ]
        dag = WorkflowDAG(nodes, workflow_name="test")
        executor = WorkflowExecutor(dag)
        results = executor.run()
        assert results["join"].status == StepStatus.COMPLETED

    def test_step_callback(self) -> None:
        completed: list[str] = []
        nodes: list[NodeDefinition] = [
            {"node_id": "a", "bash": "echo a"},
            {"node_id": "b", "bash": "echo b"},
        ]
        dag = WorkflowDAG(nodes, workflow_name="test")
        executor = WorkflowExecutor(dag, on_step_complete=lambda s: completed.append(s.step_id))
        executor.run()
        assert set(completed) == {"a", "b"}

    def test_timeout_marks_failure(self) -> None:
        nodes: list[NodeDefinition] = [
            {"node_id": "slow", "bash": "sleep 10", "timeout_ms": 100},
        ]
        dag = WorkflowDAG(nodes, workflow_name="test")
        executor = WorkflowExecutor(dag)
        results = executor.run()
        assert results["slow"].status == StepStatus.FAILED
        assert "timeout" in results["slow"].error

    def test_max_attempts_zero_still_runs(self) -> None:
        """max_attempts=0 should be clamped to 1, not silently skip."""
        nodes: list[NodeDefinition] = [
            {
                "node_id": "zero",
                "bash": "echo ran",
                "retry": {"max_attempts": 0, "delay_ms": 0},
            },
        ]
        dag = WorkflowDAG(nodes, workflow_name="test")
        executor = WorkflowExecutor(dag)
        results = executor.run()
        # Should have actually executed, not stayed PENDING
        assert results["zero"].status == StepStatus.COMPLETED
        assert results["zero"].attempt == 1

    def test_negative_max_attempts_still_runs(self) -> None:
        nodes: list[NodeDefinition] = [
            {
                "node_id": "neg",
                "bash": "echo ran",
                "retry": {"max_attempts": -5, "delay_ms": -100},
            },
        ]
        dag = WorkflowDAG(nodes, workflow_name="test")
        executor = WorkflowExecutor(dag)
        results = executor.run()
        assert results["neg"].status == StepStatus.COMPLETED


# ---------------------------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------------------------


class TestCheckpointStore:
    """Tests for SQLite checkpoint persistence."""

    def test_create_and_load(self) -> None:
        with CheckpointStore() as store:
            run_id = store.create_run("test-workflow")
            assert isinstance(run_id, str)
            assert len(run_id) == 12

    def test_save_and_load_steps(self) -> None:
        from scripts.workflow_runner.types import StepState

        with CheckpointStore() as store:
            run_id = store.create_run("test")
            state = StepState(
                step_id="step1", status=StepStatus.COMPLETED, output="ok", exit_code=0
            )
            store.save_step(run_id, state)

            loaded = store.load_steps(run_id)
            assert "step1" in loaded
            assert loaded["step1"].status == StepStatus.COMPLETED
            assert loaded["step1"].output == "ok"

    def test_upsert_step(self) -> None:
        from scripts.workflow_runner.types import StepState

        with CheckpointStore() as store:
            run_id = store.create_run("test")
            state = StepState(step_id="s", status=StepStatus.RUNNING)
            store.save_step(run_id, state)

            state.status = StepStatus.COMPLETED
            state.output = "done"
            store.save_step(run_id, state)

            loaded = store.load_steps(run_id)
            assert loaded["s"].status == StepStatus.COMPLETED

    def test_get_incomplete_run(self) -> None:
        with CheckpointStore() as store:
            run_id = store.create_run("wf")
            assert store.get_incomplete_run("wf") == run_id
            store.mark_completed(run_id)
            assert store.get_incomplete_run("wf") is None

    def test_export_run(self) -> None:
        from scripts.workflow_runner.types import StepState

        with CheckpointStore() as store:
            run_id = store.create_run("wf")
            store.save_step(run_id, StepState(step_id="a", status=StepStatus.COMPLETED))
            exported = json.loads(store.export_run(run_id))
            assert "a" in exported
            assert exported["a"]["status"] == "completed"

    def test_resume_execution(self) -> None:
        """Simulate crash recovery: run 2 of 3 steps, then resume."""
        from scripts.workflow_runner.types import StepState

        nodes: list[NodeDefinition] = [
            {"node_id": "a", "bash": "echo a"},
            {"node_id": "b", "bash": "echo b", "depends_on": ["a"]},
            {"node_id": "c", "bash": "echo c", "depends_on": ["b"]},
        ]
        with CheckpointStore() as store:
            dag = WorkflowDAG(nodes, workflow_name="resume-test")
            run_id = store.create_run("resume-test")

            store.save_step(
                run_id,
                StepState(step_id="a", status=StepStatus.COMPLETED, output="a-out", exit_code=0),
            )
            store.save_step(
                run_id,
                StepState(step_id="b", status=StepStatus.COMPLETED, output="b-out", exit_code=0),
            )
            store.save_step(
                run_id,
                StepState(step_id="c", status=StepStatus.PENDING),
            )

            executor = WorkflowExecutor(dag, store=store)
            results = executor.run(resume_run_id=run_id)

            assert results["a"].output == "a-out"
            assert results["b"].output == "b-out"
            assert results["c"].status == StepStatus.COMPLETED
            assert "c" in results["c"].output

    def test_file_based_store(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        with CheckpointStore(db_path) as store:
            run_id = store.create_run("file-test")

        with CheckpointStore(db_path) as store2:
            assert store2.get_incomplete_run("file-test") == run_id

    def test_context_manager(self) -> None:
        with CheckpointStore() as store:
            store.create_run("ctx-test")
        # Connection should be closed after exiting context


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


class TestLoader:
    """Tests for workflow file loading."""

    def test_load_json_workflow(self, tmp_path: Path) -> None:
        wf = {
            "name": "test",
            "nodes": [
                {"id": "a", "bash": "echo a"},
                {"id": "b", "bash": "echo b", "depends_on": ["a"]},
            ],
        }
        path = tmp_path / "test.json"
        path.write_text(json.dumps(wf))
        dag = load_workflow(path)
        assert len(dag) == 2
        assert dag.topological_order() == ["a", "b"]

    def test_load_yaml_workflow(self, tmp_path: Path) -> None:
        pytest.importorskip("yaml")
        content = textwrap.dedent("""\
            name: yaml-test
            nodes:
              - id: first
                bash: "echo first"
              - id: second
                skill: "refactor:code-explorer"
                depends_on: [first]
        """)
        path = tmp_path / "test.yaml"
        path.write_text(content)
        dag = load_workflow(path)
        assert len(dag) == 2

    def test_load_nonexistent_file(self) -> None:
        with pytest.raises(WorkflowValidationError, match="not found"):
            load_workflow("/nonexistent/path.json")

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{invalid")
        with pytest.raises((json.JSONDecodeError, WorkflowValidationError)):
            load_workflow(path)

    def test_load_missing_name(self, tmp_path: Path) -> None:
        path = tmp_path / "no-name.json"
        path.write_text(json.dumps({"nodes": [{"id": "a", "bash": "echo"}]}))
        with pytest.raises(WorkflowValidationError, match="name"):
            load_workflow(path)

    def test_load_missing_nodes(self, tmp_path: Path) -> None:
        path = tmp_path / "no-nodes.json"
        path.write_text(json.dumps({"name": "test"}))
        with pytest.raises(WorkflowValidationError, match="nodes"):
            load_workflow(path)

    def test_load_node_without_bash_or_skill(self, tmp_path: Path) -> None:
        path = tmp_path / "no-action.json"
        path.write_text(json.dumps({"name": "t", "nodes": [{"id": "a"}]}))
        with pytest.raises(WorkflowValidationError, match="bash.*skill"):
            load_workflow(path)

    def test_load_unsupported_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "test.toml"
        path.write_text("")
        with pytest.raises(WorkflowValidationError, match="unsupported"):
            load_workflow(path)

    def test_load_invalid_timeout_ms(self, tmp_path: Path) -> None:
        path = tmp_path / "bad-int.json"
        path.write_text(
            json.dumps(
                {"name": "t", "nodes": [{"id": "a", "bash": "echo", "timeout_ms": "not-a-number"}]}
            )
        )
        with pytest.raises(WorkflowValidationError, match="timeout_ms must be an integer"):
            load_workflow(path)

    def test_load_invalid_max_turns(self, tmp_path: Path) -> None:
        path = tmp_path / "bad-turns.json"
        path.write_text(
            json.dumps({"name": "t", "nodes": [{"id": "a", "skill": "x", "max_turns": "abc"}]})
        )
        with pytest.raises(WorkflowValidationError, match="max_turns must be an integer"):
            load_workflow(path)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class TestTypes:
    """Tests for type definitions and enums."""

    def test_step_status_values(self) -> None:
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.COMPLETED.value == "completed"

    def test_trigger_rule_values(self) -> None:
        assert TriggerRule.ALL_SUCCESS.value == "all_success"
        assert TriggerRule.ALL_DONE.value == "all_done"
        assert TriggerRule.ONE_SUCCESS.value == "one_success"

    def test_step_state_to_dict(self) -> None:
        from scripts.workflow_runner.types import StepState

        state = StepState(step_id="x", status=StepStatus.COMPLETED, output="ok", exit_code=0)
        d = state.to_dict()
        assert d["step_id"] == "x"
        assert d["status"] == "completed"


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


class TestProperties:
    """Property-based tests using hypothesis."""

    @given(
        st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
                min_size=1,
                max_size=10,
            ),
            min_size=1,
            max_size=20,
            unique=True,
        )
    )
    @settings(max_examples=50)
    def test_independent_nodes_single_layer(self, ids: list[str]) -> None:
        """Independent nodes (no deps) should all be in layer 0."""
        nodes: list[NodeDefinition] = [{"node_id": nid, "bash": f"echo {nid}"} for nid in ids]
        dag = WorkflowDAG(nodes)
        layers = dag.get_layers()
        assert len(layers) == 1
        assert sorted(layers[0]) == sorted(ids)

    @given(
        st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
                min_size=1,
                max_size=10,
            ),
            min_size=2,
            max_size=10,
            unique=True,
        )
    )
    @settings(max_examples=50)
    def test_linear_chain_produces_n_layers(self, ids: list[str]) -> None:
        """A linear chain of n nodes should produce n layers."""
        nodes: list[NodeDefinition] = [{"node_id": ids[0], "bash": f"echo {ids[0]}"}]
        for i in range(1, len(ids)):
            nodes.append({"node_id": ids[i], "bash": f"echo {ids[i]}", "depends_on": [ids[i - 1]]})
        dag = WorkflowDAG(nodes)
        layers = dag.get_layers()
        assert len(layers) == len(ids)
