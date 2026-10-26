from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import tool4d


class Tool4DRunnerTests(unittest.TestCase):
    def run_case(self, source, exit_code, artifact):
        workspaces = []

        def execute(command, **kwargs):
            project = Path(next(s.removeprefix("--project=") for s in command
                                if s.startswith("--project=")))
            workspace = project.parent.parent
            workspaces.append(workspace)
            if artifact is not None:
                (workspace / "agent-test.txt").write_text(artifact, encoding="utf-8")
            return subprocess.CompletedProcess(command, exit_code, stdout="", stderr="")

        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("sys.argv", ["tool4d.py", str(source), "--compile"]), \
                patch("tool4d.find_tool4d", return_value="fake-tool4d"), \
                patch("tool4d.subprocess.run", side_effect=execute), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                tool4d.main()
            finally:
                self.assertTrue(workspaces)
                self.assertTrue(all(not p.exists() for p in workspaces))
        return stdout.getvalue()

    def project(self, root):
        source = root / "demo"
        (source / "Project").mkdir(parents=True)
        (source / "Project/Test.4DProject").write_text("{}", encoding="utf-8")
        return source

    def test_nonzero_runtime_exit_cannot_be_hidden_by_an_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.project(Path(directory))
            with self.assertRaisesRegex(SystemExit, "status 3"):
                self.run_case(source, 3, "success-shaped stale output")
            self.assertFalse((source / "agent-test.txt").exists())

    def test_zero_exit_still_requires_the_output_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(SystemExit, "produced no agent-test.txt"):
                self.run_case(self.project(Path(directory)), 0, None)

    def test_success_prints_this_runs_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.run_case(self.project(Path(directory)), 0, "PASS"), "PASS\n")


if __name__ == "__main__":
    unittest.main()
