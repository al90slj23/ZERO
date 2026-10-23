"""Portable bootstrap filesystem/config regressions; no network or real tools."""
import contextlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import types
import unittest
from unittest import mock
import tomllib
from urllib.parse import unquote, urlsplit

ZERO = Path(__file__).resolve().parents[4]
LOCAL = Path(".ai/L0#Execution/workflows/local")
BOOTSTRAP = LOCAL / "zero-bootstrap.py"
BACKUPS = Path(".ai/L0#Execution/backups")
CONFIG = Path(".codex/config.toml")
SOURCE_CONFIG = Path(".ai/L0#Execution/configs/zero-codex.toml")


def load_module(path):
    # Compile directly so inspecting a template never creates __pycache__ in it.
    module = types.ModuleType("zero_bootstrap_test_subject")
    module.__file__ = str(path)
    exec(compile(path.read_text(), str(path), "exec"), module.__dict__)
    return module


def inventory(root, exclude_backups=False):
    result = {}
    if not root.exists():
        return result
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if exclude_backups and (relative == BACKUPS or BACKUPS in relative.parents):
            continue
        mode = stat.S_IMODE(path.lstat().st_mode)
        if path.is_symlink(): value = ("symlink", mode, os.readlink(path))
        elif path.is_file(): value = ("file", mode, path.read_bytes())
        else: value = ("directory", mode)
        result[relative.as_posix()] = value
    return result


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="zero-bootstrap-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.source = self.base / "template source's"
        subject = load_module(ZERO / BOOTSTRAP)
        for origin, relative in subject.template_files(ZERO):
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origin, target)
        (self.source / "AGENTS.md").write_text("SOURCE_ONLY_DO_NOT_COPY\n")
        (self.source / "gogogo.sh").write_text("SOURCE_DEPLOYMENT_DO_NOT_COPY\n")
        self.target = self.base / "project"
        self.target.mkdir()

    def write(self, relative, text, mode=0o644):
        path = self.target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(mode)
        return path

    def run_cli(self, *extra, source=None, target=None):
        return subprocess.run([sys.executable, str((source or self.source) / BOOTSTRAP),
                               "--target", str(target or self.target), *extra],
                              text=True, capture_output=True, check=False)

    def prepared(self, *extra, **kwargs):
        result = self.run_cli("--prepare-only", *extra, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_new_project_idempotent_and_template_source_untouched(self):
        for name in (".ai/L3#Standards/inspirations/large.bin",
                     ".ai/L4#Changelog/old-history.md",
                     ".ai/L0#Execution/specs/completed/old.md",
                     ".ai/L5#Knowledge/.generated/private-cache",
                     ".ai/L0#Execution/backups/old/snapshot.tar"):
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("excluded source material")
        source_before = inventory(self.source)
        state = self.prepared()
        self.assertFalse(state["runtime_ready"])
        self.assertTrue(state["project_adaptation_pending"])
        self.assertIsNone(state["backup"])
        self.assertNotIn("SOURCE_ONLY_DO_NOT_COPY", (self.target / "AGENTS.md").read_text())
        self.assertFalse((self.target / "gogogo.sh").exists())
        self.assertFalse((self.target / ".ai/L3#Standards/inspirations").exists())
        self.assertFalse((self.target / ".ai/L4#Changelog/old-history.md").exists())
        self.assertFalse((self.target / ".ai/L5#Knowledge/.generated").exists())
        self.assertEqual((self.target / ".ai/L5#Knowledge/.gitignore").read_text(), ".generated/\n")
        guide = (self.target / ".ai/L1#Overview/guide.md").read_text()
        self.assertIn("zero-project-facts.md", guide)
        self.assertIn("zero-template-guide.md", guide)
        before = inventory(self.target)
        # The imported copy remains usable after removing the downloaded source.
        result = subprocess.run(["/bin/bash", str(self.target / LOCAL / "zero-bootstrap.sh"),
                                 "--prepare-only"], cwd=self.target, text=True,
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        repeated = json.loads(result.stdout)
        self.assertEqual(repeated["changed_files"], 0)
        self.assertIsNone(repeated["backup"])
        self.assertEqual(inventory(self.target), before)
        self.assertEqual(inventory(self.source), source_before)

    def test_existing_project_documents_and_codex_options_are_preserved(self):
        self.write(".ai/L1#Overview/guide.md", "Project rules prevail\n")
        differing = ".ai/L3#Standards/standards/00.meta-01.core.md"
        self.write(differing, "Existing project standard\n")
        original_agents = "# Existing Agent guide\nRetain these project instructions.\n"
        self.write("AGENTS.md", original_agents, 0o640)
        original_config = 'model = "project-model"\n\n[mcp_servers.other]\ncommand = "existing-tool"\nargs = ["keep-me"]\n'
        self.write(CONFIG, original_config, 0o600)
        self.write(".gitignore", "existing-output/\n", 0o640)
        first = self.prepared()
        self.assertIn(differing, first["preserved_differing_templates"])
        self.assertEqual((self.target / differing).read_text(), "Existing project standard\n")
        self.assertEqual((self.target / ".ai/L1#Overview/guide.md").read_text(), "Project rules prevail\n")
        self.assertTrue((self.target / "AGENTS.md").read_text().startswith(original_agents))
        config = tomllib.loads((self.target / CONFIG).read_text())
        self.assertEqual(config["model"], "project-model")
        self.assertEqual(config["mcp_servers"]["other"]["args"], ["keep-me"])
        self.assertEqual(set(config["mcp_servers"]), {"other", "zero_qmd", "zero_codegraph"})
        self.assertTrue((self.target / CONFIG).is_symlink())
        self.assertEqual(os.readlink(self.target / CONFIG), "../.ai/L0#Execution/configs/zero-codex.toml")
        self.assertEqual(stat.S_IMODE((self.target / SOURCE_CONFIG).stat().st_mode), 0o600)
        backups = list((self.target / BACKUPS).iterdir())
        before = inventory(self.target)
        repeated = self.prepared()
        self.assertEqual(repeated["changed_files"], 0)
        self.assertIsNone(repeated["backup"])
        self.assertEqual(list((self.target / BACKUPS).iterdir()), backups)
        self.assertEqual(inventory(self.target), before)

    def test_backup_restores_original_contents_modes_and_symlinks(self):
        guide = self.write(".ai/L1#Overview/guide.md", "Original project guide\n", 0o640)
        self.write(".ai/legacy-codex.toml", 'model = "original"\n', 0o600)
        self.write(".ai/legacy-ignore", "old-ignore/\n", 0o640)
        (self.target / "AGENTS.md").symlink_to(guide.relative_to(self.target))
        (self.target / ".gitignore").symlink_to(".ai/legacy-ignore")
        (self.target / ".codex").mkdir()
        (self.target / ".codex").chmod(0o700)
        (self.target / CONFIG).symlink_to("../.ai/legacy-codex.toml")
        self.write(".codegraph/codegraph.db", "original legacy graph contents", 0o600)
        (self.target / ".codegraph").chmod(0o700)
        before = inventory(self.target)
        state = self.prepared()
        saved = Path(state["backup"])
        manifest = json.loads((saved / "manifest.json").read_text())
        self.assertEqual(manifest["format"], "zero-bootstrap-backup-v1")
        graph_entry = next(entry for entry in manifest["entries"] if entry["path"] == ".codegraph")
        self.assertEqual(graph_entry["kind"], "directory")
        self.assertTrue(all("resolved_snapshot" in entry for entry in manifest["entries"]
                            if entry.get("kind") == "symlink"))
        restored = self.base / "restored"
        restored.mkdir()
        with tarfile.open(saved / "snapshot.tar") as archive:
            self.assertFalse(any(name.startswith(str(BACKUPS)) for name in archive.getnames()))
            archive.extractall(restored, filter="fully_trusted")
        observed = inventory(restored)
        # .codex is an archive-created parent; its preexisting mode is unchanged.
        for relative, value in before.items():
            self.assertEqual(observed[relative], value, relative)
        self.assertEqual((self.target / ".ai/legacy-codex.toml").read_text(), 'model = "original"\n')
        self.assertEqual((self.target / ".ai/legacy-ignore").read_text(), "old-ignore/\n")
        self.assertNotIn(".ai/L0#Execution", observed, "backup creation must not invent original directories")

    def test_existing_backups_are_excluded_from_new_snapshot(self):
        self.write(".ai/notes.md", "notes")
        self.write(str(BACKUPS / "earlier/snapshot.tar"), "prior backup")
        saved = Path(self.prepared()["backup"])
        with tarfile.open(saved / "snapshot.tar") as archive:
            self.assertFalse(any(name == str(BACKUPS) or name.startswith(str(BACKUPS) + "/")
                                 for name in archive.getnames()))
        self.assertEqual((self.target / BACKUPS / "earlier/snapshot.tar").read_text(), "prior backup")

    def test_conflicting_mcp_server_fails_before_backup_or_mutation(self):
        self.write(".ai/notes.md", "private project facts")
        self.write(CONFIG, '[mcp_servers.zero_qmd]\ncommand = "different-owner"\n')
        before = inventory(self.target)
        result = self.run_cli("--prepare-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflicts", result.stderr)
        self.assertEqual(inventory(self.target), before)

    def test_conflicting_runtime_template_fails_without_changes(self):
        self.write(str(LOCAL / "retrieval-indexes.sh"), "existing custom runtime\n")
        before = inventory(self.target)
        result = self.run_cli("--prepare-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Required runtime file differs", result.stderr)
        self.assertEqual(inventory(self.target), before)

    def test_unsafe_parent_alias_rejected_without_touching_external_data(self):
        external = self.base / "external"
        external.mkdir()
        (external / "keep").write_text("untouched")
        (self.target / ".ai").symlink_to(external)
        before, outside = inventory(self.target), inventory(external)
        result = self.run_cli("--prepare-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsafe parent", result.stderr)
        self.assertEqual(inventory(self.target), before)
        self.assertEqual(inventory(external), outside)

    def test_home_and_filesystem_root_are_rejected_before_planning(self):
        subject = load_module(self.source / BOOTSTRAP)
        before = inventory(self.base)
        for target in (str(self.target), "/"):
            with self.subTest(target=target), \
                    mock.patch.object(subject.Path, "home", return_value=self.target), \
                    mock.patch.object(sys, "argv", ["bootstrap", "--target", target, "--prepare-only"]), \
                    mock.patch.object(subject, "plan") as planning, \
                    self.assertRaises(subject.BootstrapError):
                subject.main()
            planning.assert_not_called()
            self.assertEqual(inventory(self.base), before)

    def test_runtime_tools_cache_and_lock_aliases_fail_without_changes(self):
        for relative, directory in (("tools", True), ("cache", True), ("qmd/refresh.lock", False)):
            with self.subTest(relative=relative):
                target = self.base / ("unsafe-" + relative.replace("/", "-"))
                target.mkdir()
                external = self.base / ("external-" + relative.replace("/", "-"))
                if directory:
                    external.mkdir()
                    (external / "keep").write_text("outside content")
                else:
                    external.write_text("outside lock content")
                alias = target / ".ai/L5#Knowledge/.generated" / relative
                alias.parent.mkdir(parents=True, exist_ok=True)
                alias.symlink_to(external)
                before = inventory(target)
                outside = inventory(external) if directory else external.read_bytes()
                result = self.run_cli("--prepare-only", target=target)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(inventory(target), before)
                self.assertEqual(inventory(external) if directory else external.read_bytes(), outside)

    def test_regular_node_modules_bin_executable_links_are_allowed(self):
        bins = self.target / ".ai/L5#Knowledge/.generated/tools/node_modules/.bin"
        bins.mkdir(parents=True)
        for relative in ("@tobilu/qmd/bin/qmd", "@colbymchenry/codegraph/bin/codegraph"):
            executable = bins.parent / relative
            executable.parent.mkdir(parents=True, exist_ok=True)
            executable.write_text("fixture executable")
        (bins / "qmd").symlink_to("../@tobilu/qmd/bin/qmd")
        (bins / "codegraph").symlink_to("../@colbymchenry/codegraph/bin/codegraph")
        self.prepared()
        self.assertTrue((bins / "qmd").is_symlink())

    def test_existing_graph_alias_backup_preserves_link_without_duplicate_store(self):
        store = ".ai/L5#Knowledge/.generated/codegraph/codegraph.db"
        self.write(store, "existing graph")
        (self.target / ".codegraph").symlink_to(".ai/L5#Knowledge/.generated/codegraph")
        saved = Path(self.prepared()["backup"])
        manifest = json.loads((saved / "manifest.json").read_text())
        entry = next(entry for entry in manifest["entries"] if entry["path"] == ".codegraph")
        self.assertEqual(entry["kind"], "symlink")
        self.assertNotIn("resolved_snapshot", entry)
        with tarfile.open(saved / "snapshot.tar") as archive:
            self.assertEqual(archive.getnames().count(store), 1)
            self.assertFalse(any(name.startswith(".codegraph/") for name in archive.getnames()))

    def test_spaces_apostrophes_and_client_none(self):
        target = self.base / "project's path with spaces"
        target.mkdir()
        self.prepared(target=target)
        config = tomllib.loads((target / CONFIG).read_text())
        for name, action in (("zero_qmd", "qmd-mcp"), ("zero_codegraph", "codegraph-mcp")):
            self.assertEqual(config["mcp_servers"][name]["cwd"], str(target))
            self.assertEqual(config["mcp_servers"][name]["args"], [str(target / LOCAL / "retrieval-indexes.sh"), action])
        existing = self.write(CONFIG, "invalid TOML stays outside client=none\n")
        self.prepared("--client", "none")
        self.assertEqual(existing.read_text(), "invalid TOML stays outside client=none\n")
        self.assertFalse(existing.is_symlink())
        self.assertFalse((self.target / SOURCE_CONFIG).exists())

    def test_full_mode_calls_only_adapter_init_and_reports_semantic_work_pending(self):
        subject = load_module(self.source / BOOTSTRAP)
        output = io.StringIO()
        with mock.patch.object(sys, "argv", ["bootstrap", "--target", str(self.target)]), \
                mock.patch.object(subject.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as call, \
                contextlib.redirect_stdout(output):
            self.assertEqual(subject.main(), 0)
        call.assert_called_once_with(["/bin/bash", str(self.target / LOCAL / "retrieval-indexes.sh"), "init"],
                                     cwd=self.target, stdout=sys.stderr, check=False)
        state = json.loads(output.getvalue())
        self.assertTrue(state["runtime_ready"])
        self.assertTrue(state["project_adaptation_pending"])
        self.assertTrue(self.prepared()["runtime_ready"], "prepare-only must not erase previous readiness")

    def test_adaptation_status_is_derived_from_completed_task_file(self):
        self.prepared()
        tasks = self.target / ".ai/L0#Execution/specs/active/zero-onboarding/00.spec-03.tasks.md"
        tasks.write_text(tasks.read_text().replace("Status: project_adaptation_pending", "Status: completed")
                         .replace("- [ ]", "- [x]"))
        state = self.prepared()
        self.assertFalse(state["project_adaptation_pending"])
        self.assertEqual(self.prepared()["changed_files"], 0)

    def test_completed_spec_archive_remains_owner_without_respawning_active(self):
        self.prepared()
        active = self.target / ".ai/L0#Execution/specs/active/zero-onboarding"
        completed = self.target / ".ai/L0#Execution/specs/completed/zero-onboarding"
        index = self.target / ".ai/L2#Index/zero-onboarding.md"
        def assert_navigation(owner):
            link = re.search(r"\[Authoritative adaptation tasks\]\(([^)]+)\)", index.read_text()).group(1)
            self.assertIn("%23", link)
            self.assertEqual(urlsplit(link).fragment, "")
            destination = (index.parent / unquote(urlsplit(link).path)).resolve()
            self.assertEqual(destination, owner / "00.spec-03.tasks.md")
            self.assertTrue(destination.is_file())
        assert_navigation(active)
        tasks = active / "00.spec-03.tasks.md"
        tasks.write_text(tasks.read_text().replace("Status: project_adaptation_pending", "Status: completed")
                         .replace("- [ ]", "- [x]"))
        completed.parent.mkdir(parents=True)
        shutil.move(active, completed)
        facts = self.target / ".ai/L1#Overview/zero-project-facts.md"
        old_facts = facts.read_bytes()
        state = self.prepared()
        self.assertFalse(state["project_adaptation_pending"])
        self.assertFalse(active.exists())
        self.assertEqual(facts.read_bytes(), old_facts)
        actual = ".ai/L0#Execution/specs/completed/zero-onboarding/00.spec-03.tasks.md"
        self.assertIn(actual, (self.target / "AGENTS.md").read_text())
        self.assertIn("completed/zero-onboarding", (self.target / ".ai/L2#Index/zero-onboarding.md").read_text())
        assert_navigation(completed)
        self.assertEqual(self.prepared()["changed_files"], 0)

    def test_two_onboarding_owners_are_rejected_before_backup_or_changes(self):
        self.prepared()
        active = self.target / ".ai/L0#Execution/specs/active/zero-onboarding"
        completed = self.target / ".ai/L0#Execution/specs/completed/zero-onboarding"
        shutil.copytree(active, completed)
        before = inventory(self.target)
        result = self.run_cli("--prepare-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("both active and completed", result.stderr)
        self.assertEqual(inventory(self.target), before)

    def test_json_cannot_claim_adaptation_complete_with_pending_tasks(self):
        self.prepared()
        state_file = self.target / ".ai/L0#Execution/configs/zero-bootstrap-state.json"
        state = json.loads(state_file.read_text())
        state["project_adaptation_pending"] = False
        state_file.write_text(json.dumps(state))
        self.assertTrue(self.prepared()["project_adaptation_pending"])
        tasks = self.target / ".ai/L0#Execution/specs/active/zero-onboarding/00.spec-03.tasks.md"
        tasks.write_text(tasks.read_text().replace("Status: project_adaptation_pending", "Status: completed"))
        self.assertTrue(self.prepared()["project_adaptation_pending"], "unchecked tasks still prevent closure")
        tasks.write_text("Status: completed\n\n1. [ ] ordered task still pending\n")
        self.assertTrue(self.prepared()["project_adaptation_pending"])

    def test_runtime_progress_stays_off_structured_stdout(self):
        subject = load_module(self.source / BOOTSTRAP)
        output, errors = io.StringIO(), io.StringIO()
        def noisy_init(*args, **kwargs):
            kwargs["stdout"].write("QMD/CodeGraph progress noise\n")
            return subprocess.CompletedProcess([], 0)
        with mock.patch.object(sys, "argv", ["bootstrap", "--target", str(self.target)]), \
                mock.patch.object(subject.subprocess, "run", side_effect=noisy_init), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            self.assertEqual(subject.main(), 0)
        self.assertTrue(json.loads(output.getvalue())["runtime_ready"])
        self.assertIn("progress noise", errors.getvalue())
        self.assertNotIn("progress noise", output.getvalue())

    def test_failed_init_does_not_report_runtime_ready(self):
        subject = load_module(self.source / BOOTSTRAP)
        output = io.StringIO()
        with mock.patch.object(sys, "argv", ["bootstrap", "--target", str(self.target)]), \
                mock.patch.object(subject.subprocess, "run", return_value=subprocess.CompletedProcess([], 7)), \
                contextlib.redirect_stdout(output), self.assertRaises(subject.BootstrapError):
            subject.main()
        self.assertEqual(output.getvalue(), "")
        state = json.loads((self.target / ".ai/L0#Execution/configs/zero-bootstrap-state.json").read_text())
        self.assertFalse(state["runtime_ready"])
        self.assertTrue(state["project_adaptation_pending"])

    def test_cloned_zero_can_bootstrap_itself_without_git(self):
        state = self.prepared(target=self.source)
        self.assertIsNotNone(state["backup"])
        self.assertTrue((self.source / CONFIG).is_symlink())
        self.assertTrue((self.source / ".ai/L1#Overview/zero-project-facts.md").is_file())
        self.assertFalse((self.source / ".git").exists())
        self.assertEqual(self.prepared(target=self.source)["changed_files"], 0)


if __name__ == "__main__":
    unittest.main()
