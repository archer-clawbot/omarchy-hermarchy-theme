import json
import os
import runpy
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "extras/quickshell"
INSTALLER = PLUGIN / "install.sh"
INSTALL_HELPER = PLUGIN / "scripts/hermarchy-plugin-install"
COLLECTOR = ROOT / "extras/agent-integration/hermarchy-agent-state"


class QuickshellPluginTests(unittest.TestCase):
    def test_manifest_is_a_single_restrained_bar_widget(self):
        manifest = json.loads((PLUGIN / "manifest.json").read_text())
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["id"], "io.github.archer-clawbot.hermarchy-agent")
        self.assertEqual(manifest["kinds"], ["bar-widget"])
        self.assertEqual(manifest["entryPoints"], {"barWidget": "BarWidget.qml"})
        self.assertFalse(manifest["barWidget"]["allowMultiple"])

    def test_reader_emits_only_a_collected_and_validated_record(self):
        result = subprocess.run(
            [str(PLUGIN / "scripts/hermarchy-state-read")],
            text=True,
            capture_output=True,
            env={**os.environ, "HERMARCHY_AGENT_STATE": str(COLLECTOR)},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        validate = subprocess.run(
            [str(COLLECTOR), "validate", "-"],
            input=result.stdout,
            text=True,
            capture_output=True,
        )
        self.assertEqual(validate.returncode, 0, validate.stderr)
        self.assertEqual(payload["schemaVersion"], 1)

    def test_reader_validates_and_emits_the_exact_collected_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / "collector"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "if sys.argv[1] == 'collect':\n"
                "    sys.stdout.buffer.write(b'{\\\"x\\\":1}\\n\\n')\n"
                "    raise SystemExit(0)\n"
                "if sys.argv[1:] == ['validate', '-']:\n"
                "    raise SystemExit(0 if sys.stdin.buffer.read() == b'{\\\"x\\\":1}\\n\\n' else 1)\n"
                "raise SystemExit(1)\n"
            )
            fake.chmod(0o755)
            result = subprocess.run(
                [str(PLUGIN / "scripts/hermarchy-state-read")],
                capture_output=True,
                env={**os.environ, "HERMARCHY_AGENT_STATE": str(fake)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, b'{"x":1}\n\n')

    def test_reader_bounds_collector_output_before_materializing_it(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / "collector"
            fake.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ $1 == collect ]]; then exec yes 0123456789; fi\n"
                "exit 0\n"
            )
            fake.chmod(0o755)
            result = subprocess.run(
                ["timeout", "--kill-after=1", "2", str(PLUGIN / "scripts/hermarchy-state-read")],
                text=True,
                capture_output=True,
                env={**os.environ, "HERMARCHY_AGENT_STATE": str(fake)},
            )
            self.assertNotEqual(result.returncode, 124, "reader hung while materializing unbounded stdout")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_reader_fails_closed_when_proc_tree_inspection_is_unavailable(self):
        namespace = runpy.run_path(str(PLUGIN / "scripts/hermarchy-state-read"))

        class FinishedProcess:
            def poll(self):
                return 0

        with mock.patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            tree_clean, _ = namespace["contain_process_tree"](FinishedProcess())

        self.assertFalse(tree_clean)

    def test_reader_contains_detached_collector_descendants_holding_stdout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake = root / "collector"
            pid_file = root / "child.pid"
            fake.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ $1 == collect ]]; then\n"
                "  setsid bash -c 'trap \"\" TERM; sleep 30' &\n"
                "  printf '%s' \"$!\" >\"$PID_FILE\"\n"
                "  exit 0\n"
                "fi\n"
                "exit 1\n"
            )
            fake.chmod(0o755)
            child_pid = None
            try:
                started = time.monotonic()
                result = subprocess.run(
                    ["timeout", "--kill-after=1", "8", str(PLUGIN / "scripts/hermarchy-state-read")],
                    text=True,
                    capture_output=True,
                    env={
                        **os.environ,
                        "HERMARCHY_AGENT_STATE": str(fake),
                        "PID_FILE": str(pid_file),
                    },
                )
                elapsed = time.monotonic() - started
                if pid_file.exists():
                    child_pid = int(pid_file.read_text())
                self.assertNotIn(result.returncode, (124, 137), "outer harness had to terminate the reader")
                self.assertLess(elapsed, 7.5)
                self.assertIsNotNone(child_pid)
                self.assertFalse(Path(f"/proc/{child_pid}").exists(), "collector descendant was orphaned")
            finally:
                if child_pid is not None and Path(f"/proc/{child_pid}").exists():
                    try:
                        os.killpg(child_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_reader_hard_kills_a_noncooperative_collector(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / "collector"
            fake.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ $1 == collect ]]; then trap '' TERM; while :; do sleep 1; done; fi\n"
                "exit 1\n"
            )
            fake.chmod(0o755)
            started = time.monotonic()
            result = subprocess.run(
                ["timeout", "--kill-after=1", "8", str(PLUGIN / "scripts/hermarchy-state-read")],
                text=True,
                capture_output=True,
                env={**os.environ, "HERMARCHY_AGENT_STATE": str(fake)},
            )
            elapsed = time.monotonic() - started
            self.assertNotIn(result.returncode, (124, 137), "outer harness had to terminate the reader")
            self.assertLess(elapsed, 7.5)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_reader_reaps_detached_validator_descendants_after_success(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake = root / "collector"
            pid_file = root / "child.pid"
            fake.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ $1 == collect ]]; then printf '{}'; exit 0; fi\n"
                "if [[ $1 == validate ]]; then\n"
                "  cat >/dev/null\n"
                "  setsid bash -c 'trap \"\" TERM; sleep 30' &\n"
                "  printf '%s' \"$!\" >\"$PID_FILE\"\n"
                "  exit 0\n"
                "fi\n"
                "exit 1\n"
            )
            fake.chmod(0o755)
            child_pid = None
            try:
                result = subprocess.run(
                    [str(PLUGIN / "scripts/hermarchy-state-read")],
                    text=True,
                    capture_output=True,
                    timeout=5,
                    env={
                        **os.environ,
                        "HERMARCHY_AGENT_STATE": str(fake),
                        "PID_FILE": str(pid_file),
                    },
                )
                if pid_file.exists():
                    child_pid = int(pid_file.read_text())
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIsNotNone(child_pid)
                self.assertFalse(Path(f"/proc/{child_pid}").exists(), "validator descendant was orphaned")
            finally:
                if child_pid is not None and Path(f"/proc/{child_pid}").exists():
                    try:
                        os.killpg(child_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_reader_times_out_validation_phase(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / "collector"
            fake.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ $1 == collect ]]; then printf '{}'; exit 0; fi\n"
                "if [[ $1 == validate ]]; then trap '' TERM; while :; do sleep 1; done; fi\n"
                "exit 1\n"
            )
            fake.chmod(0o755)
            started = time.monotonic()
            result = subprocess.run(
                ["timeout", "--kill-after=1", "4", str(PLUGIN / "scripts/hermarchy-state-read")],
                text=True,
                capture_output=True,
                env={**os.environ, "HERMARCHY_AGENT_STATE": str(fake)},
            )
            elapsed = time.monotonic() - started
            self.assertNotIn(result.returncode, (124, 137), "outer harness had to terminate the reader")
            self.assertLess(elapsed, 3.5)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_qml_surface_is_tiny_in_bar_and_rich_on_click(self):
        bar = (PLUGIN / "BarWidget.qml").read_text()
        panel = (PLUGIN / "Panel.qml").read_text()
        self.assertIn('moduleName: "io.github.archer-clawbot.hermarchy-agent"', bar)
        self.assertIn('text: root.indicator.label', bar)
        self.assertIn('text: root.indicator.suffix', bar)
        self.assertNotIn("activeModel", bar)
        self.assertIn("panel.fittedContentHeight(content.implicitHeight, Style.space(440))", panel)
        self.assertIn("elide: Text.ElideRight", panel)
        self.assertIn("maximumLineCount: 2", panel)
        self.assertIn("wrapMode: Text.WrapAnywhere", panel)
        self.assertNotIn("Text.ElideLeft", panel)
        self.assertIn("root.presentation.detail", panel)
        self.assertIn("root.presentation.provider", panel)
        self.assertIn("root.presentation.lastActivity", panel)
        self.assertIn("root.presentation.lastActivityAt", panel)
        self.assertNotIn("root.presentation.lastEvent", panel)
        self.assertIn("root.presentation.endReason", panel)
        self.assertIn("command: [root.readerPath]", panel)
        self.assertNotIn('command: ["bash", root.readerPath]', panel)
        for label in (
            "01 // AGENT", "TASK", "DETAIL", "MODEL", "PROVIDER", "WORKERS",
            "NODE", "GATEWAY", "LAST ACTIVITY", "ACTIVITY AT", "END REASON",
        ):
            self.assertIn(label, panel)
        for forbidden in ("TOKENS", "CONTEXT", "MEMORY", "SKILLS", "TOOLS", "UTILIZATION"):
            self.assertNotIn(forbidden, bar)
            self.assertNotIn(forbidden, panel)
        for color in ("#61D6FF", "#E2C275", "#86D993", "#E46E6E"):
            self.assertIn(color, panel)

    def test_installer_rejects_home_symlink_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            real_home = root / "real-home"
            real_home.mkdir()
            linked_home = root / "linked-home"
            linked_home.symlink_to(real_home, target_is_directory=True)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake = bin_dir / "omarchy"
            fake.write_text("#!/usr/bin/env bash\nexit 0\n")
            fake.chmod(0o755)

            result = subprocess.run(
                [str(INSTALLER), "--no-enable"],
                text=True,
                capture_output=True,
                env={
                    **os.environ,
                    "HOME": str(linked_home),
                    "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                },
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((real_home / ".local/bin/hermarchy-agent-state").exists())
            self.assertFalse((real_home / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent").exists())

    def test_installer_rejects_symlinked_plugin_destination_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            plugins = home / ".config/omarchy/plugins"
            plugins.mkdir(parents=True)
            target = root / "outside"
            target.mkdir()
            (plugins / "io.github.archer-clawbot.hermarchy-agent").symlink_to(target, target_is_directory=True)

            result = subprocess.run(
                [str(INSTALLER), "--no-enable"],
                text=True,
                capture_output=True,
                env={**os.environ, "HOME": str(home)},
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(target.iterdir()), [])

    def test_installer_does_not_follow_paths_replaced_after_staged_validation(self):
        for target in ("collector-parent", "plugin-scripts"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                home = root / "home"
                collector_parent = home / ".local/bin"
                plugin_scripts = home / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent/scripts"
                collector_parent.mkdir(parents=True)
                plugin_scripts.mkdir(parents=True)
                race_path = collector_parent if target == "collector-parent" else plugin_scripts
                outside = root / "outside"
                outside.mkdir()
                bin_dir = root / "bin"
                bin_dir.mkdir()
                fake = bin_dir / "omarchy"
                fake.write_text(
                    "#!/usr/bin/env bash\n"
                    "if [[ $1 == plugin && $2 == validate && ! -e $RACE_MARKER ]]; then\n"
                    "  rm -rf -- \"$RACE_PATH\"\n"
                    "  ln -s -- \"$OUTSIDE_PATH\" \"$RACE_PATH\"\n"
                    "  : >\"$RACE_MARKER\"\n"
                    "fi\n"
                    "exit 0\n"
                )
                fake.chmod(0o755)

                result = subprocess.run(
                    [str(INSTALLER), "--no-enable"],
                    text=True,
                    capture_output=True,
                    env={
                        **os.environ,
                        "HOME": str(home),
                        "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                        "RACE_PATH": str(race_path),
                        "OUTSIDE_PATH": str(outside),
                        "RACE_MARKER": str(root / "raced"),
                    },
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(list(outside.iterdir()), [])

    def test_installer_fails_before_writing_when_omarchy_validation_is_unavailable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            home.mkdir()
            bin_dir = root / "bin"
            bin_dir.mkdir()
            for command in ("bash", "dirname", "python3"):
                resolved = shutil.which(command)
                if resolved is None:
                    self.fail(f"required test command missing: {command}")
                (bin_dir / command).symlink_to(resolved)

            result = subprocess.run(
                [str(INSTALLER), "--no-enable"],
                text=True,
                capture_output=True,
                env={**os.environ, "HOME": str(home), "PATH": str(bin_dir)},
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((home / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent").exists())
            self.assertNotIn("Installed", result.stdout)

    def test_installer_validates_before_writing_destination_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            home.mkdir()
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake = bin_dir / "omarchy"
            fake.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ $1 == plugin && $2 == validate ]]; then exit 64; fi\n"
                "exit 0\n"
            )
            fake.chmod(0o755)

            result = subprocess.run(
                [str(INSTALLER), "--no-enable"],
                text=True,
                capture_output=True,
                env={
                    **os.environ,
                    "HOME": str(home),
                    "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                },
            )

            self.assertEqual(result.returncode, 64)
            self.assertFalse((home / ".local/bin/hermarchy-agent-state").exists())
            self.assertFalse((home / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent").exists())

    def test_installer_rolls_back_when_installed_destination_validation_fails(self):
        for preexisting in (False, True):
            with self.subTest(preexisting=preexisting), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                home = root / "home"
                home.mkdir()
                collector = home / ".local/bin/hermarchy-agent-state"
                plugin = home / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent"
                if preexisting:
                    collector.parent.mkdir(parents=True)
                    collector.write_bytes(b"previous collector\n")
                    plugin.mkdir(parents=True)
                    (plugin / "previous.txt").write_bytes(b"previous plugin\n")

                bin_dir = root / "bin"
                bin_dir.mkdir()
                fake = bin_dir / "omarchy"
                fake.write_text(
                    "#!/usr/bin/env bash\n"
                    "count=0\n"
                    "[[ -f $VALIDATE_COUNT ]] && count=$(<\"$VALIDATE_COUNT\")\n"
                    "count=$((count + 1))\n"
                    "printf '%s' \"$count\" >\"$VALIDATE_COUNT\"\n"
                    "if [[ $1 == plugin && $2 == validate && $count -eq 2 ]]; then exit 77; fi\n"
                    "exit 0\n"
                )
                fake.chmod(0o755)

                result = subprocess.run(
                    [str(INSTALLER), "--no-enable"],
                    text=True,
                    capture_output=True,
                    env={
                        **os.environ,
                        "HOME": str(home),
                        "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                        "VALIDATE_COUNT": str(root / "validate-count"),
                    },
                )

                self.assertEqual(result.returncode, 77, result.stderr)
                if preexisting:
                    self.assertEqual(collector.read_bytes(), b"previous collector\n")
                    self.assertEqual(
                        {path.relative_to(plugin): path.read_bytes() for path in plugin.rglob("*") if path.is_file()},
                        {Path("previous.txt"): b"previous plugin\n"},
                    )
                else:
                    self.assertFalse(collector.exists())
                    self.assertFalse(plugin.exists())

    def test_installer_rolls_back_artifacts_changed_during_installed_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            collector = home / ".local/bin/hermarchy-agent-state"
            plugin = home / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent"
            collector.parent.mkdir(parents=True)
            collector.write_bytes(b"previous collector\n")
            plugin.mkdir(parents=True)
            (plugin / "previous.txt").write_bytes(b"previous plugin\n")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake = bin_dir / "omarchy"
            fake.write_text(
                "#!/usr/bin/env bash\n"
                "count=0\n"
                "[[ -f $VALIDATE_COUNT ]] && count=$(<\"$VALIDATE_COUNT\")\n"
                "count=$((count + 1))\n"
                "printf '%s' \"$count\" >\"$VALIDATE_COUNT\"\n"
                "if [[ $count -eq 2 ]]; then\n"
                "  printf 'HOSTILE COLLECTOR\\n' >\"$HOME/.local/bin/hermarchy-agent-state\"\n"
                "  printf 'HOSTILE PLUGIN\\n' >\"$HOME/.config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent/Panel.qml\"\n"
                "fi\n"
                "exit 0\n"
            )
            fake.chmod(0o755)

            result = subprocess.run(
                [str(INSTALLER), "--no-enable"],
                text=True,
                capture_output=True,
                env={
                    **os.environ,
                    "HOME": str(home),
                    "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                    "VALIDATE_COUNT": str(root / "validate-count"),
                },
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(collector.read_bytes(), b"previous collector\n")
            self.assertEqual(
                {path.relative_to(plugin): path.read_bytes() for path in plugin.rglob("*") if path.is_file()},
                {Path("previous.txt"): b"previous plugin\n"},
            )

    def test_installer_rolls_back_byte_identical_collector_replacement_during_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            collector = home / ".local/bin/hermarchy-agent-state"
            plugin = home / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent"
            collector.parent.mkdir(parents=True)
            collector.write_bytes(b"previous collector\n")
            plugin.mkdir(parents=True)
            (plugin / "previous.txt").write_bytes(b"previous plugin\n")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake = bin_dir / "omarchy"
            fake.write_text(
                "#!/usr/bin/env bash\n"
                "count=0\n"
                "[[ -f $VALIDATE_COUNT ]] && count=$(<\"$VALIDATE_COUNT\")\n"
                "count=$((count + 1))\n"
                "printf '%s' \"$count\" >\"$VALIDATE_COUNT\"\n"
                "if [[ $count -eq 2 ]]; then\n"
                "  temporary=$HOME/.local/bin/replacement\n"
                "  cp -- \"$HOME/.local/bin/hermarchy-agent-state\" \"$temporary\"\n"
                "  rm -- \"$HOME/.local/bin/hermarchy-agent-state\"\n"
                "  mv -- \"$temporary\" \"$HOME/.local/bin/hermarchy-agent-state\"\n"
                "fi\n"
                "exit 0\n"
            )
            fake.chmod(0o755)

            result = subprocess.run(
                [str(INSTALLER), "--no-enable"],
                text=True,
                capture_output=True,
                env={
                    **os.environ,
                    "HOME": str(home),
                    "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                    "VALIDATE_COUNT": str(root / "validate-count"),
                },
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(collector.read_bytes(), b"previous collector\n")
            self.assertEqual(
                {path.relative_to(plugin): path.read_bytes() for path in plugin.rglob("*") if path.is_file()},
                {Path("previous.txt"): b"previous plugin\n"},
            )

    def test_installer_fails_if_local_ancestor_is_replaced_during_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            moved_local = root / "moved-local"
            collector = home / ".local/bin/hermarchy-agent-state"
            plugin = home / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent"
            collector.parent.mkdir(parents=True)
            collector.write_bytes(b"previous collector\n")
            plugin.mkdir(parents=True)
            (plugin / "previous.txt").write_bytes(b"previous plugin\n")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake = bin_dir / "omarchy"
            fake.write_text(
                "#!/usr/bin/env bash\n"
                "count=0\n"
                "[[ -f $VALIDATE_COUNT ]] && count=$(<\"$VALIDATE_COUNT\")\n"
                "count=$((count + 1))\n"
                "printf '%s' \"$count\" >\"$VALIDATE_COUNT\"\n"
                "if [[ $count -eq 2 ]]; then\n"
                "  mv -- \"$HOME/.local\" \"$MOVED_LOCAL\"\n"
                "  mkdir -- \"$HOME/.local\"\n"
                "fi\n"
                "exit 0\n"
            )
            fake.chmod(0o755)

            result = subprocess.run(
                [str(INSTALLER), "--no-enable"],
                text=True,
                capture_output=True,
                env={
                    **os.environ,
                    "HOME": str(home),
                    "MOVED_LOCAL": str(moved_local),
                    "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                    "VALIDATE_COUNT": str(root / "validate-count"),
                },
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list((home / ".local").iterdir()), [])
            self.assertEqual(
                (moved_local / "bin/hermarchy-agent-state").read_bytes(),
                b"previous collector\n",
            )
            self.assertEqual(
                {path.relative_to(plugin): path.read_bytes() for path in plugin.rglob("*") if path.is_file()},
                {Path("previous.txt"): b"previous plugin\n"},
            )

    def test_installer_detects_every_replaced_destination_ancestor(self):
        for relative in (
            ".local/bin",
            ".config",
            ".config/omarchy",
            ".config/omarchy/plugins",
        ):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                home = root / "home"
                collector = home / ".local/bin/hermarchy-agent-state"
                plugin = home / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent"
                collector.parent.mkdir(parents=True)
                collector.write_bytes(b"previous collector\n")
                plugin.mkdir(parents=True)
                (plugin / "previous.txt").write_bytes(b"previous plugin\n")
                target = home / relative
                moved = root / "moved-ancestor"
                bin_dir = root / "bin"
                bin_dir.mkdir()
                fake = bin_dir / "omarchy"
                fake.write_text(
                    "#!/usr/bin/env bash\n"
                    "count=0\n"
                    "[[ -f $VALIDATE_COUNT ]] && count=$(<\"$VALIDATE_COUNT\")\n"
                    "count=$((count + 1))\n"
                    "printf '%s' \"$count\" >\"$VALIDATE_COUNT\"\n"
                    "if [[ $count -eq 2 ]]; then\n"
                    "  mv -- \"$ANCESTOR_TARGET\" \"$MOVED_ANCESTOR\"\n"
                    "  mkdir -p -- \"$ANCESTOR_TARGET\"\n"
                    "fi\n"
                    "exit 0\n"
                )
                fake.chmod(0o755)

                result = subprocess.run(
                    [str(INSTALLER), "--no-enable"],
                    text=True,
                    capture_output=True,
                    env={
                        **os.environ,
                        "HOME": str(home),
                        "ANCESTOR_TARGET": str(target),
                        "MOVED_ANCESTOR": str(moved),
                        "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                        "VALIDATE_COUNT": str(root / "validate-count"),
                    },
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(
                    any(
                        path.is_file() and path.read_bytes() == b"previous collector\n"
                        for path in root.rglob("hermarchy-agent-state")
                    )
                )
                self.assertTrue(
                    any(
                        path.read_bytes() == b"previous plugin\n"
                        for path in root.rglob("previous.txt")
                    )
                )
                debris = [
                    path
                    for path in root.rglob("*")
                    if any(token in path.name for token in (".new.", ".backup.", ".failed."))
                ]
                self.assertEqual(debris, [])

    def test_installer_rolls_back_if_home_is_replaced_during_installed_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            moved_home = root / "moved-home"
            collector = home / ".local/bin/hermarchy-agent-state"
            plugin = home / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent"
            collector.parent.mkdir(parents=True)
            collector.write_bytes(b"previous collector\n")
            plugin.mkdir(parents=True)
            (plugin / "previous.txt").write_bytes(b"previous plugin\n")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake = bin_dir / "omarchy"
            fake.write_text(
                "#!/usr/bin/env bash\n"
                "count=0\n"
                "[[ -f $VALIDATE_COUNT ]] && count=$(<\"$VALIDATE_COUNT\")\n"
                "count=$((count + 1))\n"
                "printf '%s' \"$count\" >\"$VALIDATE_COUNT\"\n"
                "if [[ $count -eq 2 ]]; then\n"
                "  mv -- \"$HOME\" \"$MOVED_HOME\"\n"
                "  mkdir -- \"$HOME\"\n"
                "fi\n"
                "exit 0\n"
            )
            fake.chmod(0o755)

            result = subprocess.run(
                [str(INSTALLER), "--no-enable"],
                text=True,
                capture_output=True,
                env={
                    **os.environ,
                    "HOME": str(home),
                    "MOVED_HOME": str(moved_home),
                    "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                    "VALIDATE_COUNT": str(root / "validate-count"),
                },
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(home.iterdir()), [])
            self.assertEqual(
                (moved_home / ".local/bin/hermarchy-agent-state").read_bytes(),
                b"previous collector\n",
            )
            moved_plugin = moved_home / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent"
            self.assertEqual(
                {path.relative_to(moved_plugin): path.read_bytes() for path in moved_plugin.rglob("*") if path.is_file()},
                {Path("previous.txt"): b"previous plugin\n"},
            )

    def test_installer_rolls_back_when_atomic_swap_is_interrupted(self):
        namespace = runpy.run_path(str(INSTALL_HELPER))
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            collector = home / ".local/bin/hermarchy-agent-state"
            plugin = home / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent"
            collector.parent.mkdir(parents=True)
            collector.write_bytes(b"previous collector\n")
            plugin.mkdir(parents=True)
            (plugin / "previous.txt").write_bytes(b"previous plugin\n")
            payloads = {
                relative: (PLUGIN / relative).read_bytes()
                for relative in namespace["PLUGIN_FILES"]
            }
            original_rename = os.rename
            calls = 0

            def interrupted_rename(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 4:
                    raise OSError("injected swap interruption")
                return original_rename(*args, **kwargs)

            home_fd = os.open(home, os.O_RDONLY | os.O_DIRECTORY)
            try:
                with mock.patch.object(namespace["os"], "rename", side_effect=interrupted_rename):
                    with self.assertRaisesRegex(OSError, "injected swap interruption"):
                        namespace["install_transaction"](
                            home_fd,
                            b"replacement collector\n",
                            payloads,
                        )
            finally:
                os.close(home_fd)

            self.assertEqual(collector.read_bytes(), b"previous collector\n")
            self.assertEqual(
                {path.relative_to(plugin): path.read_bytes() for path in plugin.rglob("*") if path.is_file()},
                {Path("previous.txt"): b"previous plugin\n"},
            )

    def test_installer_rolls_back_if_swapped_collector_bytes_change(self):
        namespace = runpy.run_path(str(INSTALL_HELPER))
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            collector = home / ".local/bin/hermarchy-agent-state"
            plugin = home / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent"
            collector.parent.mkdir(parents=True)
            collector.write_bytes(b"previous collector\n")
            plugin.mkdir(parents=True)
            (plugin / "previous.txt").write_bytes(b"previous plugin\n")
            payloads = {
                relative: (PLUGIN / relative).read_bytes()
                for relative in namespace["PLUGIN_FILES"]
            }
            original_rename = os.rename
            calls = 0

            def tampering_rename(*args, **kwargs):
                nonlocal calls
                calls += 1
                result = original_rename(*args, **kwargs)
                if calls == 2:
                    descriptor = os.open(
                        namespace["COLLECTOR_NAME"],
                        os.O_WRONLY | os.O_TRUNC,
                        dir_fd=kwargs["dst_dir_fd"],
                    )
                    try:
                        os.write(descriptor, b"tampered collector\n")
                    finally:
                        os.close(descriptor)
                return result

            home_fd = os.open(home, os.O_RDONLY | os.O_DIRECTORY)
            try:
                with mock.patch.object(namespace["os"], "rename", side_effect=tampering_rename):
                    with self.assertRaisesRegex(
                        namespace["InstallError"], "collector bytes differ"
                    ):
                        namespace["install_transaction"](
                            home_fd,
                            b"replacement collector\n",
                            payloads,
                        )
            finally:
                os.close(home_fd)

            self.assertEqual(collector.read_bytes(), b"previous collector\n")
            self.assertEqual(
                {path.relative_to(plugin): path.read_bytes() for path in plugin.rglob("*") if path.is_file()},
                {Path("previous.txt"): b"previous plugin\n"},
            )

    def test_installer_rescans_before_enabling_new_plugin(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            home.mkdir()
            bin_dir = root / "bin"
            bin_dir.mkdir()
            log = root / "omarchy.log"
            fake = bin_dir / "omarchy"
            fake.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$*\" >> \"$OMARCHY_TEST_LOG\"\n")
            fake.chmod(0o755)
            result = subprocess.run(
                [str(INSTALLER)],
                text=True,
                capture_output=True,
                env={
                    **os.environ,
                    "HOME": str(home),
                    "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                    "OMARCHY_TEST_LOG": str(log),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = log.read_text().splitlines()
            self.assertEqual(calls[0].split()[:2], ["plugin", "validate"])
            self.assertIn("hermarchy-plugin.", calls[0])
            self.assertEqual(calls[1].split()[:2], ["plugin", "validate"])
            self.assertIn("hermarchy-installed.", calls[1])
            self.assertEqual(calls[2], "shell shell rescanPlugins")
            self.assertEqual(calls[3], "plugin enable io.github.archer-clawbot.hermarchy-agent --before omarchy.agents")

    def test_installer_repeat_ignores_hostile_tmpdir_and_leaves_no_transaction_debris(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            home.mkdir()
            outside = root / "outside"
            outside.mkdir()
            hostile_tmpdir = root / "tmpdir-link"
            hostile_tmpdir.symlink_to(outside, target_is_directory=True)
            unrelated = home / ".config/omarchy/plugins/example.unrelated"
            unrelated.mkdir(parents=True)
            marker = unrelated / "keep.txt"
            marker.write_bytes(b"keep\n")
            log = root / "omarchy.log"
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake = bin_dir / "omarchy"
            fake.write_text(
                "#!/usr/bin/env bash\n"
                "printf '%s\\n' \"$*\" >>\"$OMARCHY_TEST_LOG\"\n"
                "exit 0\n"
            )
            fake.chmod(0o755)
            environment = {
                **os.environ,
                "HOME": str(home),
                "TMPDIR": str(hostile_tmpdir),
                "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                "OMARCHY_TEST_LOG": str(log),
            }

            for _ in range(2):
                result = subprocess.run(
                    [str(INSTALLER), "--no-enable"],
                    text=True,
                    capture_output=True,
                    env=environment,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            self.assertEqual(marker.read_bytes(), b"keep\n")
            self.assertEqual(list(outside.iterdir()), [])
            calls = log.read_text().splitlines()
            self.assertEqual(len(calls), 4)
            self.assertTrue(all(call.startswith("plugin validate ") for call in calls))
            for parent in (
                home / ".local/bin",
                home / ".config/omarchy/plugins",
            ):
                debris = [
                    path.name
                    for path in parent.iterdir()
                    if any(token in path.name for token in (".new.", ".backup.", ".failed."))
                ]
                self.assertEqual(debris, [])

    def test_user_local_installer_never_writes_package_paths(self):
        source = INSTALLER.read_text() + INSTALL_HELPER.read_text()
        self.assertNotIn("/usr/share/omarchy/shell", source)
        self.assertNotIn('destination="/usr', source)
        self.assertIn('ensure_directory(home_fd, ".config")', source)
        self.assertIn('ensure_directory(omarchy_fd, "plugins")', source)

        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run(
                [str(INSTALLER), "--no-enable"],
                text=True,
                capture_output=True,
                env={**os.environ, "HOME": home},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            installed = Path(home) / ".config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent"
            self.assertTrue((installed / "manifest.json").is_file())
            self.assertTrue((installed / "BarWidget.qml").is_file())
            self.assertTrue((installed / "Panel.qml").is_file())
            self.assertTrue((Path(home) / ".local/bin/hermarchy-agent-state").is_file())


if __name__ == "__main__":
    unittest.main()
