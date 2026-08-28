#!/usr/bin/env python3
import contextlib
import io
import json
import os
import re
import runpy
import sqlite3
import subprocess
import tempfile
import types
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "extras/agent-integration/hermarchy-agent-state"
SCHEMA = ROOT / "extras/agent-integration/agent-state.schema.json"


class AgentStateContractTests(unittest.TestCase):
    def test_schema_enforces_strict_rfc3339_timestamp_pattern(self):
        schema = json.loads(SCHEMA.read_text())
        observed_pattern = schema["properties"]["observedAt"]["pattern"]
        activity_pattern = schema["properties"]["activity"]["properties"]["lastActivityAt"]["pattern"]

        self.assertEqual(observed_pattern, activity_pattern)
        self.assertIsNotNone(re.fullmatch(observed_pattern, "2033-05-18T03:33:20Z"))
        self.assertIsNone(re.fullmatch(observed_pattern, "2033-05-18 03:33:20+00:00"))

    def test_session_query_bounds_text_at_sql_projection(self):
        namespace = runpy.run_path(str(COLLECTOR))

        class Cursor:
            def fetchone(self):
                return None

        class Connection:
            def __init__(self):
                self.row_factory = None
                self.query = ""
                self.parameters = ()

            def execute(self, query, parameters=()):
                self.query = query
                self.parameters = parameters
                return Cursor()

        connection = Connection()
        namespace["latest_session"](connection)

        self.assertGreaterEqual(connection.query.count("substr("), 6)
        self.assertIn("CASE WHEN typeof(started_at)", connection.query)
        self.assertIn("CASE WHEN typeof(ended_at)", connection.query)
        self.assertIn("CASE WHEN typeof(last_activity_at)", connection.query)
        self.assertIn("started_at_type", connection.query)
        self.assertIn("ended_at_type", connection.query)
        self.assertIn("last_activity_at_type", connection.query)
        self.assertTrue(connection.parameters)
        self.assertTrue(all(isinstance(value, int) for value in connection.parameters))

    def test_database_connection_enforces_read_only_mode(self):
        namespace = runpy.run_path(str(COLLECTOR))
        with mock.patch.object(namespace["sqlite3"], "connect") as connect:
            namespace["open_read_only_database"](Path("/tmp/state db.sqlite"))

        connect.assert_called_once()
        args, kwargs = connect.call_args
        self.assertTrue(args[0].startswith("file:"))
        self.assertTrue(args[0].endswith("?mode=ro"))
        self.assertTrue(kwargs["uri"])

    def make_db(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "state.db"
        con = sqlite3.connect(path)
        con.executescript(
            """
            CREATE TABLE sessions (
              id TEXT PRIMARY KEY,
              title TEXT,
              model TEXT,
              billing_provider TEXT,
              started_at REAL NOT NULL,
              ended_at REAL,
              end_reason TEXT,
              last_activity_at REAL,
              last_activity_description TEXT,
              hidden INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE async_delegations (
              delegation_id TEXT PRIMARY KEY,
              origin_session TEXT NOT NULL,
              state TEXT NOT NULL
            );
            """
        )
        con.close()
        return path

    def collect(self, db, *extra, env=None):
        result = subprocess.run(
            [
                str(COLLECTOR),
                "collect",
                "--db",
                str(db),
                "--now",
                "2000000000",
                "--gateway-state",
                "inactive",
                "--node",
                "test-node",
                *extra,
            ],
            text=True,
            capture_output=True,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_empty_database_emits_idle_contract(self):
        state = self.collect(self.make_db())

        self.assertEqual(state["schemaVersion"], 1)
        self.assertEqual(state["state"], "idle")
        self.assertEqual(state["signal"], "muted")
        self.assertEqual(state["node"], "test-node")
        self.assertEqual(state["gateway"]["state"], "inactive")
        self.assertIsNone(state["activity"]["sessionId"])
        self.assertEqual(state["source"]["adapter"], "hermes-local")
        self.assertEqual(state["source"]["confidence"], "observed")

    def test_recent_open_session_emits_executing(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                """INSERT INTO sessions
                   (id,title,model,billing_provider,started_at,last_activity_at,last_activity_description)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    "session-1",
                    "Build telemetry",
                    "gpt-5.6-sol",
                    "openai-codex",
                    1999999900,
                    1999999980,
                    "Running tests",
                ),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "executing")
        self.assertEqual(state["signal"], "cyan")
        self.assertEqual(state["activity"]["sessionId"], "session-1")
        self.assertEqual(state["activity"]["task"], "Build telemetry")
        self.assertEqual(state["runtime"]["model"], "gpt-5.6-sol")
        self.assertEqual(state["source"]["confidence"], "inferred")

    def test_recent_successful_end_emits_completed(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                """INSERT INTO sessions
                   (id,title,started_at,last_activity_at,ended_at,end_reason)
                   VALUES (?,?,?,?,?,?)""",
                ("session-2", "Finished task", 1999999800, 1999999970, 1999999980, "completed"),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "completed")
        self.assertEqual(state["signal"], "green")
        self.assertEqual(state["source"]["confidence"], "observed")

    def test_explicit_failure_end_emits_failed(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                """INSERT INTO sessions
                   (id,title,started_at,last_activity_at,ended_at,end_reason)
                   VALUES (?,?,?,?,?,?)""",
                ("session-3", "Broken task", 1999999800, 1999999970, 1999999980, "tool_error"),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "failed")
        self.assertEqual(state["signal"], "red")
        self.assertEqual(state["activity"]["endReason"], "tool_error")

    def test_fresh_runtime_snapshot_can_emit_waiting(self):
        db = self.make_db()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        runtime_state = Path(tmp.name) / "runtime.json"
        runtime_state.write_text(
            json.dumps(
                {
                    "state": "waiting",
                    "updatedAt": 1999999990,
                    "task": "Approve package update",
                    "detail": "Human input required",
                }
            )
        )

        state = self.collect(db, "--runtime-state", str(runtime_state))

        self.assertEqual(state["state"], "waiting")
        self.assertEqual(state["signal"], "amber")
        self.assertEqual(state["activity"]["task"], "Approve package update")
        self.assertEqual(state["activity"]["detail"], "Human input required")
        self.assertEqual(state["source"]["confidence"], "explicit")

    def test_stale_runtime_snapshot_is_ignored(self):
        db = self.make_db()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        runtime_state = Path(tmp.name) / "runtime.json"
        runtime_state.write_text(
            json.dumps(
                {
                    "state": "waiting",
                    "updatedAt": 1999999000,
                    "task": "Expired approval",
                }
            )
        )

        state = self.collect(db, "--runtime-state", str(runtime_state))

        self.assertEqual(state["state"], "idle")
        self.assertEqual(state["signal"], "muted")
        self.assertEqual(state["source"]["confidence"], "observed")

    def test_missing_agent_emits_unavailable(self):
        state = self.collect(self.make_db(), "--agent-available", "no")

        self.assertEqual(state["state"], "unavailable")
        self.assertEqual(state["signal"], "muted")
        self.assertEqual(state["source"]["confidence"], "observed")

    def test_unreadable_database_emits_unknown(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Path(tmp.name) / "state.db"
        db.write_text("not a sqlite database")

        state = self.collect(db, "--agent-available", "yes")

        self.assertEqual(state["state"], "unknown")
        self.assertEqual(state["signal"], "muted")
        self.assertEqual(state["source"]["confidence"], "unknown")

    def test_validator_accepts_collector_output(self):
        state = self.collect(self.make_db())
        result = subprocess.run(
            [str(COLLECTOR), "validate", "-"],
            input=json.dumps(state),
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "valid")

    def test_validator_rejects_state_signal_mismatch(self):
        state = self.collect(self.make_db())
        state["state"] = "waiting"
        state["signal"] = "cyan"
        result = subprocess.run(
            [str(COLLECTOR), "validate", "-"],
            input=json.dumps(state),
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("signal must be amber for waiting", result.stderr)

    def test_gateway_state_is_observed_from_systemd(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        systemctl = Path(tmp.name) / "systemctl"
        systemctl.write_text("#!/bin/sh\nprintf 'active\\n'\n")
        systemctl.chmod(0o755)
        env = dict(os.environ)
        env["PATH"] = f"{tmp.name}:{env['PATH']}"

        state = self.collect(
            self.make_db(),
            "--gateway-state",
            "auto",
            env=env,
        )

        self.assertEqual(state["gateway"]["state"], "active")

    def test_active_delegation_keeps_session_executing(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                """INSERT INTO sessions
                   (id,title,started_at,last_activity_at)
                   VALUES (?,?,?,?)""",
                ("session-4", "Delegated task", 1999998000, 1999999000),
            )
            con.execute(
                """INSERT INTO async_delegations
                   (delegation_id,origin_session,state)
                   VALUES (?,?,?)""",
                ("worker-1", "session-4", "running"),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "executing")
        self.assertEqual(state["signal"], "cyan")
        self.assertEqual(state["activity"]["activeWorkers"], 1)
        self.assertEqual(state["source"]["confidence"], "observed")

    def test_hermes_home_selects_profile_database(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        home = Path(tmp.name)
        db = home / "state.db"
        con = sqlite3.connect(db)
        con.executescript(
            """
            CREATE TABLE sessions (
              id TEXT PRIMARY KEY, title TEXT, model TEXT, billing_provider TEXT,
              started_at REAL NOT NULL, ended_at REAL, end_reason TEXT,
              last_activity_at REAL, last_activity_description TEXT,
              hidden INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE async_delegations (
              delegation_id TEXT PRIMARY KEY, origin_session TEXT NOT NULL,
              state TEXT NOT NULL
            );
            INSERT INTO sessions
              (id,title,started_at,last_activity_at)
              VALUES ('profile-session','Profile task',1999999900,1999999990);
            """
        )
        con.close()
        env = dict(os.environ)
        env["HERMES_HOME"] = str(home)
        result = subprocess.run(
            [
                str(COLLECTOR), "collect", "--now", "2000000000",
                "--gateway-state", "inactive", "--agent-available", "yes",
            ],
            text=True,
            capture_output=True,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(result.stdout)

        self.assertEqual(state["activity"]["sessionId"], "profile-session")
        self.assertEqual(state["state"], "executing")

    def validate_payload(self, payload):
        return subprocess.run(
            [str(COLLECTOR), "validate", "-"],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
        )

    def test_validator_rejects_non_object_without_traceback(self):
        result = self.validate_payload([])

        self.assertEqual(result.returncode, 1)
        self.assertIn("top level must be object", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_validator_rejects_wrong_nested_type_without_traceback(self):
        state = self.collect(self.make_db())
        state["source"] = []
        result = self.validate_payload(state)

        self.assertEqual(result.returncode, 1)
        self.assertIn("source must be object", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_validator_rejects_unknown_gateway_state(self):
        state = self.collect(self.make_db())
        state["gateway"]["state"] = "banana"
        result = self.validate_payload(state)

        self.assertEqual(result.returncode, 1)
        self.assertIn("gateway.state is not recognized", result.stderr)

    def test_unknown_gateway_override_is_sanitized(self):
        state = self.collect(self.make_db(), "--gateway-state", "banana")

        self.assertEqual(state["gateway"]["state"], "unknown")

    def test_validator_rejects_invalid_activity_timestamp(self):
        state = self.collect(self.make_db())
        state["activity"]["lastActivityAt"] = "yesterday"
        result = self.validate_payload(state)

        self.assertEqual(result.returncode, 1)
        self.assertIn("activity.lastActivityAt must be date-time or null", result.stderr)

    def test_validator_rejects_non_string_enums_without_traceback(self):
        state = self.collect(self.make_db())
        for path in ("state", "gateway.state"):
            with self.subTest(path=path):
                candidate = json.loads(json.dumps(state))
                if path == "state":
                    candidate["state"] = []
                else:
                    candidate["gateway"]["state"] = []
                result = self.validate_payload(candidate)
                self.assertEqual(result.returncode, 1)
                self.assertNotIn("Traceback", result.stderr)

    def test_ambiguous_terminal_reason_never_emits_completed(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                """INSERT INTO sessions
                   (id,title,started_at,last_activity_at,ended_at,end_reason)
                   VALUES (?,?,?,?,?,?)""",
                ("session-5", "Closed shell", 1999999800, 1999999970, 1999999980, "cli_close"),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "unknown")
        self.assertEqual(state["signal"], "muted")

    def test_future_database_timestamp_fails_closed(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                """INSERT INTO sessions
                   (id,title,started_at,last_activity_at)
                   VALUES (?,?,?,?)""",
                ("session-6", "Future task", 1999999900, 2000000100),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "unknown")
        self.assertEqual(state["signal"], "muted")

    def test_non_numeric_database_timestamp_fails_closed(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                """INSERT INTO sessions
                   (id,title,started_at,last_activity_at)
                   VALUES (?,?,?,?)""",
                ("session-7", "Invalid time", 1999999900, "soon"),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "unknown")
        self.assertEqual(state["source"]["confidence"], "unknown")

    def test_worker_from_non_latest_session_keeps_agent_executing(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                "INSERT INTO sessions (id,title,started_at,last_activity_at) VALUES (?,?,?,?)",
                ("worker-parent", "Background task", 1999997000, 1999998000),
            )
            con.execute(
                "INSERT INTO sessions (id,title,started_at,last_activity_at) VALUES (?,?,?,?)",
                ("latest", "Latest idle session", 1999998500, 1999999000),
            )
            con.execute(
                "INSERT INTO async_delegations (delegation_id,origin_session,state) VALUES (?,?,?)",
                ("worker-2", "worker-parent", "running"),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "executing")
        self.assertEqual(state["activity"]["activeWorkers"], 1)
        self.assertEqual(state["source"]["confidence"], "observed")

    def test_malformed_runtime_snapshot_is_ignored(self):
        db = self.make_db()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        runtime_state = Path(tmp.name) / "runtime.json"
        runtime_state.write_text(
            json.dumps(
                {
                    "state": "waiting",
                    "updatedAt": 1999999990,
                    "task": 123,
                    "detail": "Human input required",
                }
            )
        )

        state = self.collect(db, "--runtime-state", str(runtime_state))

        self.assertEqual(state["state"], "idle")
        self.assertIsNone(state["activity"]["task"])

    def test_boolean_schema_version_is_rejected(self):
        state = self.collect(self.make_db())
        state["schemaVersion"] = True
        result = self.validate_payload(state)

        self.assertEqual(result.returncode, 1)
        self.assertIn("schemaVersion must be 1", result.stderr)

    def test_validator_rejects_oversized_file_and_stdin(self):
        oversized = b" " * 70000
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        payload = Path(tmp.name) / "oversized.json"
        payload.write_bytes(oversized)

        file_result = subprocess.run(
            [str(COLLECTOR), "validate", str(payload)],
            text=True,
            capture_output=True,
        )
        stdin_result = subprocess.run(
            [str(COLLECTOR), "validate", "-"],
            input=oversized,
            capture_output=True,
        )

        self.assertEqual(file_result.returncode, 1)
        self.assertIn("input exceeds", file_result.stderr)
        self.assertEqual(stdin_result.returncode, 1)
        self.assertIn(b"input exceeds", stdin_result.stderr)

    def test_validator_rejects_excessive_nesting_without_traceback(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        payload = Path(tmp.name) / "nested.json"
        payload.write_text("[]")
        namespace = runpy.run_path(str(COLLECTOR))
        stderr = io.StringIO()

        with mock.patch.object(
            namespace["json"], "loads", side_effect=RecursionError("too deep")
        ), mock.patch.object(namespace["sys"], "stderr", stderr):
            result = namespace["validate"](types.SimpleNamespace(path=str(payload)))

        self.assertEqual(result, 1)
        self.assertIn("invalid JSON", stderr.getvalue())

    def test_validator_rejects_invalid_utf8_without_traceback(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        payload = Path(tmp.name) / "invalid.json"
        payload.write_bytes(b"\xff")

        result = subprocess.run(
            [str(COLLECTOR), "validate", str(payload)],
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid JSON", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_null_session_description_remains_null(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                """INSERT INTO sessions
                   (id,title,started_at,last_activity_at,last_activity_description)
                   VALUES (?,?,?,?,?)""",
                ("null-detail", "Null detail", 1999999900, 1999999990, None),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "executing")
        self.assertIsNone(state["activity"]["lastActivity"])

    def test_non_text_session_storage_fails_closed_before_coercion(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Path(tmp.name) / "wrong-types.db"
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.executescript(
                """
                CREATE TABLE sessions (
                  id INTEGER PRIMARY KEY,
                  title INTEGER,
                  model TEXT,
                  billing_provider TEXT,
                  started_at REAL NOT NULL,
                  ended_at REAL,
                  end_reason TEXT,
                  last_activity_at REAL,
                  last_activity_description TEXT,
                  hidden INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE async_delegations (
                  delegation_id TEXT PRIMARY KEY,
                  origin_session TEXT NOT NULL,
                  state TEXT NOT NULL
                );
                """
            )
            con.execute(
                "INSERT INTO sessions (id,title,started_at,last_activity_at) VALUES (?,?,?,?)",
                (123, 456, 1999999900, 1999999990),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "unknown")
        self.assertIsNone(state["activity"]["sessionId"])
        self.assertIsNone(state["activity"]["task"])

    def test_inconsistent_session_chronology_fails_closed(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                """INSERT INTO sessions
                   (id,title,started_at,last_activity_at,ended_at,end_reason)
                   VALUES (?,?,?,?,?,?)""",
                ("bad-order", "Invalid chronology", 1999999990, 1999999980, 1999999970, "completed"),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "unknown")
        self.assertEqual(state["signal"], "muted")
        self.assertIsNone(state["activity"]["sessionId"])

    def test_invalid_session_discards_worker_count(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                "INSERT INTO sessions (id,title,started_at,last_activity_at) VALUES (?,?,?,?)",
                ("future-session", "Invalid future", 1999999900, 2000000100),
            )
            con.execute(
                "INSERT INTO async_delegations (delegation_id,origin_session,state) VALUES (?,?,?)",
                ("worker-invalid-session", "future-session", "running"),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "unknown")
        self.assertEqual(state["signal"], "muted")
        self.assertEqual(state["activity"]["activeWorkers"], 0)
        self.assertEqual(state["source"]["confidence"], "unknown")

    def test_invalid_worker_data_discards_all_database_fields(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                """INSERT INTO sessions
                   (id,title,model,billing_provider,started_at,last_activity_at,last_activity_description)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    "secret-session",
                    "DB task",
                    "model-x",
                    "provider-x",
                    1999999900,
                    1999999990,
                    "DB detail",
                ),
            )
            con.execute(
                "INSERT INTO async_delegations (delegation_id,origin_session,state) VALUES (?,?,?)",
                ("invalid-worker", "secret-session", "unrecognized"),
            )
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        runtime_state = Path(tmp.name) / "runtime.json"
        runtime_state.write_text(
            json.dumps({"state": "waiting", "updatedAt": 1999999990, "detail": "Runtime detail"})
        )

        state = self.collect(db, "--runtime-state", str(runtime_state))

        self.assertEqual(state["state"], "waiting")
        self.assertIsNone(state["activity"]["sessionId"])
        self.assertIsNone(state["activity"]["lastActivity"])
        self.assertIsNone(state["runtime"]["model"])
        self.assertIsNone(state["runtime"]["provider"])

    def test_blob_delegation_state_fails_closed(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                "INSERT INTO async_delegations (delegation_id,origin_session,state) VALUES (?,?,?)",
                ("blob-worker", "parent", sqlite3.Binary(b"running")),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "unknown")
        self.assertEqual(state["signal"], "muted")
        self.assertEqual(state["source"]["confidence"], "unknown")

    def test_validator_rejects_non_rfc3339_datetime(self):
        state = self.collect(self.make_db())
        state["observedAt"] = "2033-05-18 03:33:20+00:00"
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        payload = Path(tmp.name) / "state.json"
        payload.write_text(json.dumps(state))

        result = subprocess.run(
            [str(COLLECTOR), "validate", str(payload)],
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("observedAt must be date-time", result.stderr)

    def test_non_exact_success_reason_never_emits_green(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                """INSERT INTO sessions
                   (id,title,started_at,last_activity_at,ended_at,end_reason)
                   VALUES (?,?,?,?,?,?)""",
                ("uppercase", "Uppercase reason", 1999999900, 1999999980, 1999999990, "COMPLETED"),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "unknown")
        self.assertEqual(state["signal"], "muted")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        payload = Path(tmp.name) / "state.json"
        payload.write_text(json.dumps(state))
        result = subprocess.run(
            [str(COLLECTOR), "validate", str(payload)], text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_runtime_terminal_state_requires_allowlisted_reason(self):
        db = self.make_db()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        runtime_state = Path(tmp.name) / "runtime.json"

        for terminal_state in ("completed", "failed"):
            with self.subTest(state=terminal_state):
                runtime_state.write_text(
                    json.dumps({"state": terminal_state, "updatedAt": 1999999990})
                )
                state = self.collect(db, "--runtime-state", str(runtime_state))
                self.assertEqual(state["state"], "idle")
                self.assertEqual(state["signal"], "muted")

        for terminal_state, reason, signal in (
            ("completed", "completed", "green"),
            ("failed", "tool_error", "red"),
        ):
            with self.subTest(state=terminal_state, reason=reason):
                runtime_state.write_text(
                    json.dumps(
                        {
                            "state": terminal_state,
                            "updatedAt": 1999999990,
                            "endReason": reason,
                        }
                    )
                )
                state = self.collect(db, "--runtime-state", str(runtime_state))
                self.assertEqual(state["state"], terminal_state)
                self.assertEqual(state["signal"], signal)
                self.assertEqual(state["activity"]["endReason"], reason)

    def test_validator_rejects_unhashable_terminal_reason_without_traceback(self):
        for state_name, signal_name in (("completed", "green"), ("failed", "red")):
            with self.subTest(state=state_name):
                state = self.collect(self.make_db())
                state["state"] = state_name
                state["signal"] = signal_name
                state["activity"]["endReason"] = []
                tmp = tempfile.TemporaryDirectory()
                self.addCleanup(tmp.cleanup)
                payload = Path(tmp.name) / "state.json"
                payload.write_text(json.dumps(state))

                result = subprocess.run(
                    [str(COLLECTOR), "validate", str(payload)],
                    text=True,
                    capture_output=True,
                )

                self.assertEqual(result.returncode, 1)
                self.assertIn("activity.endReason", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_validator_requires_allowlisted_terminal_reason(self):
        for state_name, signal_name, invalid_reason in (
            ("completed", "green", None),
            ("failed", "red", "error_recovered"),
        ):
            with self.subTest(state=state_name):
                state = self.collect(self.make_db())
                state["state"] = state_name
                state["signal"] = signal_name
                state["activity"]["endReason"] = invalid_reason
                tmp = tempfile.TemporaryDirectory()
                self.addCleanup(tmp.cleanup)
                payload = Path(tmp.name) / "state.json"
                payload.write_text(json.dumps(state))

                result = subprocess.run(
                    [str(COLLECTOR), "validate", str(payload)],
                    text=True,
                    capture_output=True,
                )

                self.assertEqual(result.returncode, 1)
                self.assertIn("activity.endReason is not valid for", result.stderr)

    def test_validator_accepts_integral_float_worker_count(self):
        state = self.collect(self.make_db())
        state["activity"]["activeWorkers"] = 1.0
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        payload = Path(tmp.name) / "state.json"
        payload.write_text(json.dumps(state))

        result = subprocess.run(
            [str(COLLECTOR), "validate", str(payload)],
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_worker_collection_uses_bounded_scalar_queries(self):
        namespace = runpy.run_path(str(COLLECTOR))

        class ScalarCursor:
            def __init__(self, row):
                self.row = row

            def fetchone(self):
                return self.row

        class Connection:
            def __init__(self):
                self.calls = []

            def execute(self, query, parameters=()):
                self.calls.append((query, parameters))
                if "SELECT 1" in query:
                    return ScalarCursor(None)
                if "count(*)" in query:
                    return ScalarCursor((7,))
                raise AssertionError(query)

        connection = Connection()
        count = namespace["active_worker_count"](connection)

        self.assertEqual(count, 7)
        self.assertEqual(len(connection.calls), 2)
        self.assertTrue(all("fetchall" not in query.lower() for query, _ in connection.calls))
        self.assertTrue(all(parameters for _, parameters in connection.calls))

    def test_active_worker_overrides_agent_unavailable(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                "INSERT INTO async_delegations (delegation_id,origin_session,state) VALUES (?,?,?)",
                ("worker-unavailable", "parent", "running"),
            )

        state = self.collect(db, "--agent-available", "no")

        self.assertEqual(state["state"], "executing")
        self.assertEqual(state["signal"], "cyan")
        self.assertEqual(state["activity"]["activeWorkers"], 1)
        self.assertEqual(state["source"]["confidence"], "observed")
        self.assertFalse(state["agent"]["available"])

    def test_active_worker_overrides_runtime_snapshot_state(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                "INSERT INTO async_delegations (delegation_id,origin_session,state) VALUES (?,?,?)",
                ("worker-precedence", "parent", "running"),
            )
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        runtime_state = Path(tmp.name) / "runtime.json"

        snapshots = (
            {"state": "idle", "updatedAt": 1999999990},
            {"state": "waiting", "updatedAt": 1999999990},
            {"state": "completed", "updatedAt": 1999999990, "endReason": "completed"},
            {"state": "failed", "updatedAt": 1999999990, "endReason": "tool_error"},
        )
        for snapshot in snapshots:
            with self.subTest(snapshot=snapshot):
                runtime_state.write_text(json.dumps(snapshot))
                state = self.collect(db, "--runtime-state", str(runtime_state))
                self.assertEqual(state["state"], "executing")
                self.assertEqual(state["signal"], "cyan")
                self.assertEqual(state["activity"]["activeWorkers"], 1)
                self.assertEqual(state["source"]["confidence"], "observed")

    def test_worker_without_visible_session_still_executes(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                "INSERT INTO async_delegations (delegation_id,origin_session,state) VALUES (?,?,?)",
                ("orphan-worker", "hidden-parent", "running"),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "executing")
        self.assertEqual(state["signal"], "cyan")
        self.assertEqual(state["activity"]["activeWorkers"], 1)

    def test_unrepresentable_database_timestamp_fails_closed(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                "INSERT INTO sessions (id,title,started_at,last_activity_at) VALUES (?,?,?,?)",
                ("huge-time", "Invalid time", 1e300, 1e300),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "unknown")
        self.assertEqual(state["source"]["confidence"], "unknown")

    def test_non_finite_now_is_rejected_without_traceback(self):
        result = subprocess.run(
            [str(COLLECTOR), "collect", "--now", "nan"],
            text=True,
            capture_output=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("finite timestamp", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_future_terminal_timestamp_fails_closed(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                """INSERT INTO sessions
                   (id,title,started_at,last_activity_at,ended_at,end_reason)
                   VALUES (?,?,?,?,?,?)""",
                ("future-end", "Future completion", 1999999900, 1999999990, 2000000004, "completed"),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "unknown")
        self.assertEqual(state["signal"], "muted")

    def test_non_failure_terminal_reasons_never_emit_red(self):
        for reason in ("error_recovered", "not_failed", "without_exception"):
            with self.subTest(reason=reason):
                db = self.make_db()
                with contextlib.closing(sqlite3.connect(db)) as con, con:
                    con.execute(
                        """INSERT INTO sessions
                           (id,title,started_at,last_activity_at,ended_at,end_reason)
                           VALUES (?,?,?,?,?,?)""",
                        (reason, "Recovered", 1999999900, 1999999980, 1999999990, reason),
                    )
                state = self.collect(db)
                self.assertEqual(state["state"], "unknown")
                self.assertEqual(state["signal"], "muted")

    def test_blob_session_text_fails_closed(self):
        db = self.make_db()
        with contextlib.closing(sqlite3.connect(db)) as con, con:
            con.execute(
                "INSERT INTO sessions (id,title,started_at,last_activity_at) VALUES (?,?,?,?)",
                ("blob-title", sqlite3.Binary(b"binary"), 1999999900, 1999999990),
            )

        state = self.collect(db)

        self.assertEqual(state["state"], "unknown")
        self.assertEqual(state["source"]["confidence"], "unknown")

    def test_runtime_parser_ignores_recursion_error(self):
        namespace = runpy.run_path(str(COLLECTOR))
        with mock.patch.object(
            namespace["json"], "loads", side_effect=RecursionError("too deep")
        ), mock.patch.dict(
            namespace["read_runtime_candidate"].__globals__,
            {"read_bounded_regular_file": lambda path, maximum: b"[]"},
        ):
            candidate = namespace["read_runtime_candidate"](Path("runtime.json"))

        self.assertIsNone(candidate)

    def test_runtime_fifo_is_ignored_without_blocking(self):
        db = self.make_db()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        runtime_state = Path(tmp.name) / "runtime.fifo"
        os.mkfifo(runtime_state)

        result = subprocess.run(
            [
                str(COLLECTOR),
                "collect",
                "--db",
                str(db),
                "--now",
                "2000000000",
                "--gateway-state",
                "inactive",
                "--node",
                "test-node",
                "--runtime-state",
                str(runtime_state),
            ],
            text=True,
            capture_output=True,
            timeout=2,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["state"], "idle")

    def test_oversized_runtime_snapshot_is_ignored(self):
        db = self.make_db()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        runtime_state = Path(tmp.name) / "runtime.json"
        runtime_state.write_text(
            json.dumps({"state": "waiting", "updatedAt": 1999999990, "task": "x" * 20000})
        )

        state = self.collect(db, "--runtime-state", str(runtime_state))

        self.assertEqual(state["state"], "idle")

    def test_oversized_gateway_output_is_sanitized(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        systemctl = Path(tmp.name) / "systemctl"
        systemctl.write_text("#!/bin/sh\nprintf 'active'\nprintf '%0100000d' 0\n")
        systemctl.chmod(0o755)
        env = dict(os.environ)
        env["PATH"] = f"{tmp.name}:{env['PATH']}"

        state = self.collect(self.make_db(), "--gateway-state", "auto", env=env)

        self.assertEqual(state["gateway"]["state"], "unknown")


if __name__ == "__main__":
    unittest.main()
