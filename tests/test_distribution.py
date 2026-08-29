import json
import re
import struct
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
MANIFEST = ROOT / "extras/quickshell/manifest.json"


class DistributionReadinessTests(unittest.TestCase):
    def test_readme_has_first_run_sections_in_public_order(self):
        text = README.read_text()
        headings = [
            "# Hermarchy for Omarchy",
            "## What Hermarchy is",
            "## What it looks like",
            "## Cyan is semantic, not decorative",
            "## Install the base theme",
            "## Optional agent-aware integration",
            "## Requirements",
            "## Update",
            "## Uninstall or disable",
            "## Troubleshooting",
            "## Architecture and safety boundaries",
            "## Gallery",
            "## Development and testing",
        ]
        positions = [text.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("omarchy theme install https://github.com/archer-clawbot/omarchy-hermarchy-theme.git", text)
        self.assertIn("omarchy theme update", text)
        self.assertIn("omarchy theme remove hermarchy", text)
        self.assertIn("omarchy plugin disable io.github.archer-clawbot.hermarchy-agent", text)
        self.assertIn("The base theme does not install Hermes", text)

    def test_public_release_metadata_is_neutral_and_versioned(self):
        manifest = json.loads(MANIFEST.read_text())
        self.assertEqual(manifest["version"], "1.0.0")
        self.assertEqual(manifest["author"], "Hermarchy contributors")
        changelog = (ROOT / "CHANGELOG.md").read_text()
        self.assertIn("## v1.0.0", changelog)
        self.assertIn("Base theme", changelog)
        self.assertIn("Optional agent integration", changelog)
        self.assertIn("Known limitations", changelog)
        compatibility = (ROOT / "docs/COMPATIBILITY.md").read_text()
        self.assertIn("| Omarchy | `4.0.1-1` |", compatibility)
        self.assertIn("| Quickshell | `0.3.1-1` |", compatibility)

    def test_public_facing_text_has_no_development_machine_values(self):
        public_files = [
            README,
            ROOT / "CHANGELOG.md",
            ROOT / "docs/COMPATIBILITY.md",
            ROOT / "docs/INSTALLATION.md",
            ROOT / "extras/quickshell/README.md",
            ROOT / "extras/agent-integration/README.md",
            ROOT / "extras/waybar/README.md",
            MANIFEST,
        ]
        for path in public_files:
            text = path.read_text()
            self.assertNotRegex(text, r"/home/[A-Za-z0-9._-]+")
            self.assertNotRegex(
                text,
                r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            )
            self.assertNotRegex(text, r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY")

    def test_required_public_screenshots_and_preview_dimensions(self):
        required = [
            "desktop-overview.png",
            "launcher.png",
            "terminal-editor.png",
            "agent-executing.png",
            "agent-waiting.png",
            "agent-completed.png",
        ]
        for name in required:
            self.assertTrue((ROOT / "docs/screenshots" / name).is_file(), name)
        self.assertEqual(self.png_dimensions(ROOT / "preview.png"), (1920, 1080))
        identify = subprocess.run(
            ["identify", "-format", "%w %h", str(ROOT / "gallery-preview.webp")],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        self.assertEqual(identify.stdout, "1200 675")

    def test_all_relative_markdown_links_resolve(self):
        markdown_files = [ROOT / path for path in subprocess.check_output(
            ["git", "ls-files", "*.md"], cwd=ROOT, text=True
        ).splitlines()]
        markdown_files.extend(path for path in (ROOT / "docs").glob("*.md") if path not in markdown_files)
        link_pattern = re.compile(r"!?\[[^]]*\]\(([^)]+)\)")
        for document in markdown_files:
            text = document.read_text()
            for raw_target in link_pattern.findall(text):
                target = raw_target.split("#", 1)[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (document.parent / target).resolve()
                self.assertTrue(resolved.exists(), f"broken link in {document.relative_to(ROOT)}: {raw_target}")

    @staticmethod
    def png_dimensions(path):
        data = path.read_bytes()[:24]
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            raise AssertionError(f"not a PNG: {path}")
        return struct.unpack(">II", data[16:24])


if __name__ == "__main__":
    unittest.main()
