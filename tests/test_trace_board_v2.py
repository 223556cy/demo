import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from trace_board_v2 import (
    _bash_target,
    classify_bash_compound,
    parse_trace,
    project_graph,
    render_contract_mermaid,
    render_mermaid,
    validate_graph,
)


ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "hierarchical_trace.jsonl"


class GraphTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = parse_trace(FIXTURE)

    def nodes(self, kind):
        return [n for n in self.graph.nodes.values() if n.kind == kind]

    def node(self, kind, **attrs):
        matches = [
            node for node in self.nodes(kind)
            if all(node.attrs.get(key) == value for key, value in attrs.items())
        ]
        self.assertEqual(1, len(matches), (kind, attrs, matches))
        return matches[0]


class TestSkillRuns(GraphTestCase):
    def test_skill_runs_are_the_only_top_level_nodes(self):
        skills = sorted(self.nodes("SkillRun"), key=lambda node: node.start_index)
        self.assertEqual(
            ["aid-planning", "rq-parse", "mod-design"],
            [node.attrs["skill_name"] for node in skills],
        )
        self.assertTrue(all(node.parent_id is None for node in skills))
        self.assertNotIn("Workflow", {node.kind for node in self.graph.nodes.values()})
        self.assertNotIn("Stage", {node.kind for node in self.graph.nodes.values()})

    def test_nested_calls_are_same_level_with_invokes_edges(self):
        aid = self.node("SkillRun", skill_name="aid-planning")
        rq = self.node("SkillRun", skill_name="rq-parse")
        design = self.node("SkillRun", skill_name="mod-design")
        invokes = {(e.source, e.target) for e in self.graph.edges if e.kind == "invokes"}
        self.assertIn((aid.id, rq.id), invokes)
        self.assertIn((aid.id, design.id), invokes)
        self.assertEqual(aid.id, rq.attrs["caller_skill_id"])
        self.assertEqual(aid.id, design.attrs["caller_skill_id"])

    def test_attribution_switch_resumes_original_skill_run(self):
        aid = self.node("SkillRun", skill_name="aid-planning")
        self.assertGreaterEqual(len(aid.attrs["activity_intervals"]), 2)
        self.assertEqual(1, len([n for n in self.nodes("SkillRun") if n.attrs["skill_name"] == "aid-planning"]))

    def test_meta_skill_text_is_not_a_node_or_decision(self):
        labels = "\n".join(node.label for node in self.graph.nodes.values())
        self.assertNotIn("Base directory for this skill", labels)
        self.assertNotIn("Skill instructions for rq-parse", labels)


class TestSemanticTasks(GraphTestCase):
    def test_tasks_are_semantic_children_of_skills(self):
        skills = {node.id for node in self.nodes("SkillRun")}
        tasks = self.nodes("Task")
        self.assertTrue(tasks)
        self.assertTrue(all(task.parent_id in skills for task in tasks))
        self.assertTrue(all(task.attrs["inference_confidence"] in {"high", "medium", "low"} for task in tasks))
        self.assertTrue(all(task.attrs["boundary_reason"] for task in tasks))

    def test_expected_task_modes_are_inferred(self):
        modes = {task.attrs["semantic_mode"] for task in self.nodes("Task")}
        self.assertTrue({"inspect-input", "produce-artifact", "validate", "recover-error"}.issubset(modes))

    def test_write_targets_create_distinct_tasks(self):
        proposal_tasks = [
            task for task in self.nodes("Task")
            if task.attrs["semantic_mode"] in {"produce-artifact", "recover-error"}
            and task.attrs.get("target_scope") == "proposal.md"
        ]
        design_tasks = [
            task for task in self.nodes("Task")
            if task.attrs["semantic_mode"] == "produce-artifact"
            and task.attrs.get("target_scope") == "delta-design.md"
        ]
        self.assertGreaterEqual(len(proposal_tasks), 2)
        self.assertEqual(1, len(design_tasks))

    def test_raw_thought_is_task_detail_not_node(self):
        self.assertFalse(self.nodes("Thought"))
        raw = "\n".join(str(task.attrs.get("raw_thought", "")) for task in self.nodes("Task"))
        self.assertIn("Generate proposal.md", raw)


class TestDecisionsAndTools(GraphTestCase):
    def test_decisions_drive_tool_calls_inside_same_task(self):
        drives = [edge for edge in self.graph.edges if edge.kind == "drives"]
        self.assertTrue(drives)
        for edge in drives:
            decision = self.graph.nodes[edge.source]
            tool = self.graph.nodes[edge.target]
            self.assertEqual("Decision", decision.kind)
            self.assertEqual("ToolCall", tool.kind)
            self.assertEqual(decision.parent_id, tool.parent_id)

    def test_tool_calls_belong_to_task_and_skill(self):
        tasks = {node.id: node for node in self.nodes("Task")}
        for tool in self.nodes("ToolCall"):
            self.assertIn(tool.parent_id, tasks)
            self.assertEqual(tasks[tool.parent_id].parent_id, tool.attrs["skill_run_id"])

    def test_compound_bash_classification_ignores_leading_cd(self):
        result = classify_bash_compound("cd D:/workspace && python -m pytest tests/test_x.py")
        self.assertEqual("VALIDATE", result.classification)
        self.assertEqual(2, len(result.subcommands))


class TestErrorsAndObservations(GraphTestCase):
    def test_test_failure_is_an_important_standalone_error(self):
        error = self.node("Error", category="TestFailure")
        self.assertEqual("important", error.attrs["severity"])
        failed_tool = self.graph.nodes[error.attrs["tool_call_id"]]
        self.assertEqual("test-1", failed_tool.attrs["tool_use_id"])
        edges = {(edge.source, edge.target, edge.kind) for edge in self.graph.edges}
        result = self.graph.nodes[failed_tool.attrs["result_node_id"]]
        self.assertIn((failed_tool.id, result.id, "yields"), edges)
        self.assertIn((result.id, error.id, "fails_with"), edges)

    def test_error_triggers_recovery_task(self):
        error = self.node("Error", category="TestFailure")
        recovery = [task for task in self.nodes("Task") if task.attrs["semantic_mode"] == "recover-error"]
        self.assertEqual(1, len(recovery))
        self.assertIn(
            (error.id, recovery[0].id),
            {(edge.source, edge.target) for edge in self.graph.edges if edge.kind == "triggers"},
        )

    def test_successful_validation_creates_passed_observation(self):
        observations = [
            node for node in self.nodes("Observation")
            if node.attrs.get("status") == "passed" and node.attrs.get("category") == "ValidationResult"
        ]
        self.assertEqual(1, len(observations))


class TestArtifacts(GraphTestCase):
    def test_write_and_edit_create_versioned_contract_artifacts(self):
        proposal = self.graph.artifacts["specs/proposal.md"]
        design = self.graph.artifacts["specs/delta-design.md"]
        self.assertEqual([1, 2], [version.version for version in proposal])
        self.assertEqual([1], [version.version for version in design])
        self.assertTrue(all(version.is_contract for version in proposal + design))

    def test_artifact_nodes_record_skill_task_and_tool_provenance(self):
        proposal_v1 = self.graph.artifacts["specs/proposal.md"][0]
        node = self.graph.nodes[proposal_v1.node_id]
        self.assertEqual("ArtifactVersion", node.kind)
        self.assertTrue(proposal_v1.producer_skill_run_id)
        self.assertTrue(proposal_v1.producer_task_id)
        self.assertTrue(proposal_v1.producer_tool_call_id)

    def test_edit_consumes_previous_version_and_supersedes_it(self):
        proposal = self.graph.artifacts["specs/proposal.md"]
        edges = {(edge.source, edge.target, edge.kind) for edge in self.graph.edges}
        self.assertIn((proposal[0].node_id, proposal[1].node_id, "supersedes"), edges)
        edit_tool = self.node("ToolCall", tool_use_id="edit-1")
        self.assertIn((proposal[0].node_id, edit_tool.id, "consumes"), edges)

    def test_cross_skill_read_consumes_latest_version(self):
        proposal_v2 = self.graph.artifacts["specs/proposal.md"][1]
        read = self.node("ToolCall", tool_use_id="read-2")
        self.assertIn(
            (proposal_v2.node_id, read.id, "consumes"),
            {(edge.source, edge.target, edge.kind) for edge in self.graph.edges},
        )


class TestProjectionAndMermaid(GraphTestCase):
    def test_base_graph_has_no_dangling_edges_or_then_edges(self):
        validate_graph(self.graph)
        self.assertNotIn("then", {edge.kind for edge in self.graph.edges})
        self.assertNotIn("sequential", {edge.kind for edge in self.graph.edges})

    def test_macro_keeps_skills_tasks_latest_contracts_and_important_errors(self):
        projection = project_graph(self.graph, "macro")
        kinds = {node.kind for node in projection.nodes.values()}
        self.assertTrue({"SkillRun", "Task", "ArtifactVersion", "Error"}.issubset(kinds))
        proposal_ids = {version.node_id for version in self.graph.artifacts["specs/proposal.md"]}
        self.assertIn(self.graph.artifacts["specs/proposal.md"][-1].node_id, projection.nodes)
        self.assertEqual(1, len(proposal_ids & set(projection.nodes)))
        self.assertTrue(all(edge.source in projection.nodes and edge.target in projection.nodes for edge in projection.edges))

    def test_micro_contains_every_base_node(self):
        projection = project_graph(self.graph, "micro")
        self.assertEqual(set(self.graph.nodes), set(projection.nodes))

    def test_hidden_endpoints_are_rolled_up_with_provenance(self):
        projection = project_graph(self.graph, "macro")
        derived = [edge for edge in projection.edges if edge.derived]
        self.assertTrue(derived)
        self.assertTrue(any(edge.via for edge in derived))

    def test_mermaid_defines_all_rendered_edge_endpoints(self):
        projection = project_graph(self.graph, "macro")
        mermaid = render_mermaid(projection)
        # The %%{init}%% directive (theme + htmlLabels) precedes the diagram header.
        self.assertTrue(mermaid.startswith("%%{init:"))
        self.assertIn("graph LR", mermaid)
        self.assertIn("aid-planning", mermaid)
        self.assertIn("proposal.md", mermaid)
        self.assertNotIn("|then|", mermaid)

    def test_macro_mermaid_groups_every_skill_as_subgraph(self):
        projection = project_graph(self.graph, "macro")
        mermaid = render_mermaid(projection)
        import re
        skill_names = [
            node.attrs.get("skill_name")
            for node in self.graph.nodes.values()
            if node.kind == "SkillRun"
        ]
        for skill_name in skill_names:
            self.assertIn(f'["🧩 {skill_name}"]', mermaid)

    def test_macro_mermaid_excludes_unselected_skills(self):
        projection = project_graph(self.graph, "macro")
        skill_names = [
            node.attrs.get("skill_name")
            for node in self.graph.nodes.values()
            if node.kind == "SkillRun"
        ]
        if len(skill_names) < 2:
            self.skipTest("Need at least two SkillRun nodes to test filter")
        target = skill_names[-1]
        mermaid = render_mermaid(projection, skill_filter={target})
        self.assertIn(f'["🧩 {target}"]', mermaid)
        for name in skill_names[:-1]:
            self.assertNotIn(f'["🧩 {name}"]', mermaid)


class TestRealShapeRegressions(unittest.TestCase):
    def parse_records(self, records):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            return parse_trace(path)

    @staticmethod
    def skill_records(name="sample-skill", skill_id="skill-1"):
        return [
            {
                "type": "assistant",
                "cwd": "D:/workspace",
                "message": {"role": "assistant", "content": [{
                    "type": "tool_use", "id": skill_id, "name": "Skill",
                    "input": {"skill": name, "args": ""},
                }]},
            },
            {
                "type": "user",
                "cwd": "D:/workspace",
                "message": {"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": skill_id,
                    "content": f"Launching skill: {name}", "is_error": False,
                }]},
            },
        ]

    def test_validation_classifier_uses_command_verb_not_path_words(self):
        self.assertEqual("INFO", classify_bash_compound("ls tests/").classification)
        self.assertEqual("ACTION", classify_bash_compound("mkdir -p tests").classification)
        self.assertEqual("INFO", classify_bash_compound("cat test.py").classification)
        self.assertEqual("VERSION_CONTROL", classify_bash_compound("git add tests/x.py").classification)
        self.assertEqual("VALIDATE", classify_bash_compound("python -m pytest tests/x.py").classification)

    def test_compound_split_does_not_split_quoted_operators(self):
        result = classify_bash_compound("grep -E 'a|b' file.txt && echo done")
        self.assertEqual(("grep -E 'a|b' file.txt", "echo done"), result.subcommands)

    def test_bash_target_uses_last_file_argument(self):
        self.assertEqual("b.py", _bash_target("python a.py b.py", "ACTION"))

    def test_list_tool_result_extracts_text_and_elides_images(self):
        records = self.skill_records()
        records.extend([
            {
                "type": "assistant", "cwd": "D:/workspace", "attributionSkill": "sample-skill",
                "message": {"role": "assistant", "content": [
                    {"type": "thinking", "thinking": "Inspect mixed tool output."}
                ]},
            },
            {
                "type": "assistant", "cwd": "D:/workspace", "attributionSkill": "sample-skill",
                "message": {"role": "assistant", "content": [{
                    "type": "tool_use", "id": "tool-1", "name": "Bash",
                    "input": {"command": "python inspect.py"},
                }]},
            },
            {
                "type": "user", "cwd": "D:/workspace",
                "message": {"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": "tool-1", "is_error": False,
                    "content": [
                        {"type": "text", "text": "inspection complete"},
                        {"type": "image", "source": {"data": "SECRET_BASE64"}},
                    ],
                }]},
            },
        ])
        graph = self.parse_records(records)
        tool = next(node for node in graph.nodes.values() if node.kind == "ToolCall")
        self.assertEqual("inspection complete\n[image omitted]", tool.attrs["result"])
        self.assertNotIn("SECRET_BASE64", tool.attrs["result"])

    def test_pre_skill_tool_calls_are_reported_as_diagnostics(self):
        records = [{
            "type": "assistant", "cwd": "D:/workspace",
            "message": {"role": "assistant", "content": [{
                "type": "tool_use", "id": "pre-1", "name": "Bash",
                "input": {"command": "pwd"},
            }]},
        }]
        records.extend(self.skill_records())
        graph = self.parse_records(records)
        self.assertTrue(any("unattributed tool" in item for item in graph.diagnostics))

    def test_same_basename_different_paths_create_distinct_tasks(self):
        records = self.skill_records()
        for number, path in enumerate(("src/a/index.ts", "src/b/index.ts"), 1):
            records.extend([
                {
                    "type": "assistant", "cwd": "D:/workspace", "attributionSkill": "sample-skill",
                    "message": {"role": "assistant", "content": [
                        {"type": "thinking", "thinking": f"Produce {path}."}
                    ]},
                },
                {
                    "type": "assistant", "cwd": "D:/workspace", "attributionSkill": "sample-skill",
                    "message": {"role": "assistant", "content": [{
                        "type": "tool_use", "id": f"write-{number}", "name": "Write",
                        "input": {"file_path": f"D:/workspace/{path}", "content": "x"},
                    }]},
                },
                {
                    "type": "user", "cwd": "D:/workspace",
                    "message": {"role": "user", "content": [{
                        "type": "tool_result", "tool_use_id": f"write-{number}",
                        "content": "ok", "is_error": False,
                    }]},
                },
            ])
        graph = self.parse_records(records)
        tasks = [node for node in graph.nodes.values() if node.kind == "Task"]
        self.assertEqual(2, len(tasks))

    def test_unrecovered_terminal_error_is_critical(self):
        records = self.skill_records()
        records.extend([
            {
                "type": "assistant", "cwd": "D:/workspace", "attributionSkill": "sample-skill",
                "message": {"role": "assistant", "content": [
                    {"type": "thinking", "thinking": "Run final tests."},
                    {"type": "tool_use", "id": "test-final", "name": "Bash",
                     "input": {"command": "python -m pytest tests/final.py"}},
                ]},
            },
            {
                "type": "user", "cwd": "D:/workspace",
                "message": {"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": "test-final", "is_error": True,
                    "content": "FAILED AssertionError: final failure",
                }]},
            },
        ])
        graph = self.parse_records(records)
        error = next(node for node in graph.nodes.values() if node.kind == "Error")
        self.assertEqual("critical", error.attrs["severity"])

    def test_resolution_never_targets_error_parent(self):
        graph = parse_trace(FIXTURE)
        for edge in graph.edges:
            if edge.kind not in {"triggers", "resolves"}:
                continue
            error = graph.nodes[edge.source]
            self.assertNotEqual(error.parent_id, edge.target)

    def test_multiple_unrecovered_errors_all_become_critical(self):
        records = self.skill_records()
        for number in (1, 2):
            records.extend([
                {
                    "type": "assistant", "cwd": "D:/workspace", "attributionSkill": "sample-skill",
                    "message": {"role": "assistant", "content": [{
                        "type": "tool_use", "id": f"failure-{number}", "name": "Bash",
                        "input": {"command": "python -m pytest tests/final.py"},
                    }]},
                },
                {
                    "type": "user", "cwd": "D:/workspace",
                    "message": {"role": "user", "content": [{
                        "type": "tool_result", "tool_use_id": f"failure-{number}",
                        "is_error": True, "content": f"FAILED AssertionError: failure {number}",
                    }]},
                },
            ])
        graph = self.parse_records(records)
        errors = [node for node in graph.nodes.values() if node.kind == "Error"]
        self.assertEqual(2, len(errors))
        self.assertTrue(all(error.attrs["severity"] == "critical" for error in errors))

    def test_windows_and_wrapper_validation_commands_are_detected(self):
        self.assertEqual("VALIDATE", classify_bash_compound(r"C:\\Python\\python.exe -m pytest").classification)
        self.assertEqual("VALIDATE", classify_bash_compound("npm run test:unit").classification)
        self.assertEqual("VALIDATE", classify_bash_compound("./gradlew test").classification)
        self.assertEqual("VALIDATE", classify_bash_compound('bash -c "pytest -q"').classification)

    def test_newline_separates_shell_commands(self):
        result = classify_bash_compound("cd D:/workspace\nnpm test")
        self.assertEqual("VALIDATE", result.classification)
        self.assertEqual(("cd D:/workspace", "npm test"), result.subcommands)

    def test_diagnostics_are_available_for_ui_details(self):
        records = [{
            "type": "assistant", "cwd": "D:/workspace",
            "message": {"role": "assistant", "content": [{
                "type": "tool_use", "id": "pre-1", "name": "Bash",
                "input": {"command": "pwd"},
            }]},
        }]
        graph = self.parse_records(records)
        self.assertTrue(graph.diagnostics)

    def test_import_does_not_execute_streamlit_page(self):
        result = subprocess.run(
            [sys.executable, "-c", "import trace_board_v2; assert callable(trace_board_v2.main)"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("missing ScriptRunContext", result.stderr)


class TestLevelTwoAndResults(unittest.TestCase):
    def parse_records(self, records):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            return parse_trace(path)

    def test_taskcreate_and_taskupdate_share_one_level_two_task(self):
        records = [
            {
                "type": "assistant", "cwd": "D:/workspace",
                "message": {"role": "assistant", "content": [{
                    "type": "tool_use", "id": "task-create-1", "name": "TaskCreate",
                    "input": {"subject": "PLANNING: aid-planning", "description": "Produce proposal.md"},
                }]},
            },
            {
                "type": "user", "cwd": "D:/workspace",
                "message": {"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": "task-create-1",
                    "content": "Task #1 created", "is_error": False,
                }]},
                "toolUseResult": {"task": {"id": "1", "subject": "PLANNING: aid-planning"}},
            },
            {
                "type": "assistant", "cwd": "D:/workspace",
                "message": {"role": "assistant", "content": [{
                    "type": "tool_use", "id": "skill-1", "name": "Skill",
                    "input": {"skill": "aid-planning", "args": ""},
                }]},
            },
            {
                "type": "user", "cwd": "D:/workspace",
                "message": {"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": "skill-1",
                    "content": "Launching skill", "is_error": False,
                }]},
            },
            {
                "type": "assistant", "cwd": "D:/workspace",
                "attributionSkill": "aid-planning",
                "message": {"role": "assistant", "content": [{
                    "type": "tool_use", "id": "task-update-1", "name": "TaskUpdate",
                    "input": {"taskId": "1", "status": "in_progress"},
                }]},
            },
            {
                "type": "user", "cwd": "D:/workspace",
                "message": {"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": "task-update-1",
                    "content": "Updated task", "is_error": False,
                }]},
                "toolUseResult": {"taskId": "1", "status": "in_progress"},
            },
            {
                "type": "assistant", "cwd": "D:/workspace",
                "attributionSkill": "aid-planning",
                "message": {"role": "assistant", "content": [{
                    "type": "tool_use", "id": "task-update-2", "name": "TaskUpdate",
                    "input": {"taskId": "1", "status": "completed"},
                }]},
            },
            {
                "type": "user", "cwd": "D:/workspace",
                "message": {"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": "task-update-2",
                    "content": "Updated task", "is_error": False,
                }]},
                "toolUseResult": {"taskId": "1", "status": "completed"},
            },
        ]
        graph = self.parse_records(records)
        tasks = [node for node in graph.nodes.values() if node.kind == "Task"]
        self.assertEqual(1, len(tasks))
        self.assertEqual("explicit", tasks[0].attrs["source"])
        self.assertEqual("completed", tasks[0].status)
        self.assertEqual(["pending", "in_progress", "completed"], [event["status"] for event in tasks[0].attrs["lifecycle"]])
        skill = next(node for node in graph.nodes.values() if node.kind == "SkillRun")
        self.assertEqual(skill.id, tasks[0].parent_id)

    def test_result_is_child_of_tool_call_and_error_is_child_of_result(self):
        graph = parse_trace(FIXTURE)
        failed_tool = next(node for node in graph.nodes.values() if node.kind == "ToolCall" and node.attrs["tool_use_id"] == "test-1")
        result = next(node for node in graph.nodes.values() if node.kind == "Result" and node.attrs["tool_call_id"] == failed_tool.id)
        error = next(node for node in graph.nodes.values() if node.kind == "Error" and node.attrs["tool_call_id"] == failed_tool.id)
        self.assertEqual(failed_tool.id, result.parent_id)
        self.assertEqual(result.id, error.parent_id)
        self.assertIn((failed_tool.id, result.id), {(edge.source, edge.target) for edge in graph.edges if edge.kind == "yields"})
        self.assertIn((result.id, error.id), {(edge.source, edge.target) for edge in graph.edges if edge.kind == "fails_with"})

    def test_result_informs_following_decision(self):
        graph = parse_trace(FIXTURE)
        result = next(node for node in graph.nodes.values() if node.kind == "Result" and node.attrs.get("tool_use_id") == "test-1")
        decision = next(node for node in graph.nodes.values() if node.kind == "Decision" and "Fix proposal" in node.label)
        self.assertIn((result.id, decision.id), {(edge.source, edge.target) for edge in graph.edges if edge.kind == "informs"})

    def test_human_feedback_is_level_two_but_tool_result_is_not_human(self):
        records = [{
            "type": "user", "cwd": "D:/workspace",
            "message": {"role": "user", "content": "Initial goal"},
        }]
        records.extend([
            {
                "type": "assistant", "cwd": "D:/workspace",
                "message": {"role": "assistant", "content": [{
                    "type": "tool_use", "id": "skill-1", "name": "Skill",
                    "input": {"skill": "sample-skill", "args": ""},
                }]},
            },
            {
                "type": "user", "cwd": "D:/workspace",
                "message": {"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": "skill-1", "content": "launched", "is_error": False,
                }]},
            },
            {
                "type": "user", "cwd": "D:/workspace",
                "message": {"role": "user", "content": "Please correct the requirement."},
            },
        ])
        graph = self.parse_records(records)
        feedback = [node for node in graph.nodes.values() if node.kind == "HumanInteraction"]
        self.assertEqual(1, len(feedback))
        skill = next(node for node in graph.nodes.values() if node.kind == "SkillRun")
        self.assertEqual(skill.id, feedback[0].parent_id)
        self.assertNotIn("HumanInteraction", [node.kind for node in graph.nodes.values() if node.attrs.get("tool_use_id")])

    def test_artifact_is_second_level_owned_by_skill(self):
        graph = parse_trace(FIXTURE)
        version = graph.artifacts["specs/proposal.md"][0]
        artifact = graph.nodes[version.node_id]
        self.assertEqual("SkillRun", graph.nodes[artifact.parent_id].kind)


class TestImportSafety(unittest.TestCase):
    def test_import_does_not_execute_streamlit_page(self):
        result = subprocess.run(
            [sys.executable, "-c", "import trace_board_v2; assert callable(trace_board_v2.main)"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("missing ScriptRunContext", result.stderr)


if __name__ == "__main__":
    unittest.main()
