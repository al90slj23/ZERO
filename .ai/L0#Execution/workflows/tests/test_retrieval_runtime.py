#!/usr/bin/env python3
"""Offline runtime regression checks; run with Python 3 on macOS or Linux.

The adapter runs against temporary projects with fake Node/npm/QMD/CodeGraph.
No installed retrieval CLI, network access, model download, or real index is used.
"""

import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest


EXECUTION = Path(__file__).resolve().parents[2]
ADAPTER = Path(".ai/L0#Execution/workflows/local/retrieval-indexes.sh")
GENERATED = Path(".ai/L5#Knowledge/.generated")
EMBED_MODEL = (
    "hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"
)

FAKE_NODE = r'''#!/usr/bin/env python3
import json, os, sys
major = int(os.environ.get('FIXTURE_NODE_MAJOR', '22'))
if sys.argv[1] == '-p':
    print(json.dumps([str(major) + '.0.0', 'fixture-abi', sys.platform, 'fixture-arch']))
elif sys.argv[1] == '-e':
    if major < 22:
        print('Retrieval requires Node.js >= 22.', file=sys.stderr)
        sys.exit(1)
else:
    raise SystemExit('Unexpected real Node invocation in offline test')
'''

FAKE_NPM = r'''#!/usr/bin/env python3
import json, os, pathlib, sys, time
args = sys.argv[1:]
project = pathlib.Path.cwd()
target = pathlib.Path(args[args.index('--prefix') + 1])
runtime = project / '.ai/L5#Knowledge/.generated'
assert target == runtime / 'tools'
assert pathlib.Path(args[args.index('--cache') + 1]) == runtime / 'cache/npm'
assert pathlib.Path(os.environ['npm_config_devdir']) == runtime / 'cache/node-gyp'
assert pathlib.Path(os.environ['TMPDIR']) == runtime / 'tmp'
assert 'ci' in args and '--no-audit' in args and '--no-fund' in args
with (project / '.ai/events.jsonl').open('a') as log:
    log.write(json.dumps({'cli': 'npm', 'args': ['ci']}) + '\n')
time.sleep(float(os.environ.get('FIXTURE_INSTALL_DELAY', '0')))
if os.environ.get('FIXTURE_FAIL_NPM'):
    sys.exit(37)
manifest = json.loads((target / 'package.json').read_text())
modules = target / 'node_modules'
bins = modules / '.bin'
bins.mkdir(parents=True, exist_ok=True)
for name, version in manifest['dependencies'].items():
    package = modules / name
    package.mkdir(parents=True, exist_ok=True)
    (package / 'package.json').write_text(json.dumps({'version': version}))
for name in ('qmd', 'codegraph'):
    cli = bins / name
    cli.write_text((pathlib.Path(__file__).parent / 'fixture-cli').read_text())
    cli.chmod(0o755)
print('Installation diagnostics must stay off MCP stdout')
'''

FAKE_CLI = r'''#!/usr/bin/env python3
import fcntl, json, os, pathlib, sys, time
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
project = pathlib.Path.cwd()
def record(arguments):
    with (project / '.ai/events.jsonl').open('a') as log:
        log.write(json.dumps({'cli': name, 'args': arguments}) + '\n')
if name == 'qmd':
    assert args[:2] == ['--index', 'zero'] or args[:3] == ['mcp', '--index', 'zero']
    args = [arg for arg in args if arg not in ('--index', 'zero')]
command = args[0]
# Mutating calls must be serialized, even across simultaneous init processes.
guard = None
if command in ('update', 'pull', 'embed', 'init', 'sync'):
    guard = (project / ('.ai/fixture-' + name + '.lock')).open('a')
    fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
record(args)
if name == 'qmd':
    config = json.loads((pathlib.Path(os.environ['QMD_CONFIG_DIR']) / 'zero.yml').read_text())
    assert config['models']['embed'] == os.environ['QMD_EMBED_MODEL']
    assert config['models']['rerank'] == os.environ['QMD_RERANK_MODEL']
    assert config['models']['generate'] == os.environ['QMD_GENERATE_MODEL']
    assert 'Qwen3-Embedding' in config['models']['embed']
    assert set(config['models']) == {'embed', 'generate', 'rerank'}
    assert config['collections']['zero-ai']['path'] == str(project / '.ai')
    assert config['collections']['zero-ai']['ignore'] == ['L0#Execution/backups/**', '**/.generated/**']
    cache = pathlib.Path(os.environ['XDG_CACHE_HOME']) / 'qmd'
    if command == 'update':
        cache.mkdir(parents=True, exist_ok=True)
        (cache / 'zero.sqlite').write_text('fixture text index')
    elif command == 'pull':
        if os.environ.get('FIXTURE_FAIL_PULL'):
            sys.exit(41)
        models = cache / 'models'
        models.mkdir(parents=True, exist_ok=True)
        for role, uri in config['models'].items():
            owner, repository, filename = uri[3:].split('/')
            (models / ('hf_' + owner + '_' + filename)).write_text('GGUF fixture ' + role)
            # Remote metadata is deliberately unrelated to the raw-file digest.
            (models / (filename + '.etag')).write_text('fixture Xet object identifier')
    elif command == 'embed':
        gate = os.environ.get('FIXTURE_EMBED_GATE')
        deadline = time.monotonic() + 15
        while gate and pathlib.Path(gate).exists():
            if time.monotonic() > deadline:
                raise SystemExit('Test failed to release the background embedding gate')
            time.sleep(0.02)
        if os.environ.get('FIXTURE_FAIL_EMBED'):
            sys.exit(43)
        record(['embed-finished'])
    if command == 'mcp':
        print(json.dumps({'jsonrpc': '2.0', 'fixture': 'qmd'}))
    else:
        print('QMD maintenance diagnostics: ' + command)
else:
    assert os.environ['CODEGRAPH_TELEMETRY'] == '0'
    assert 'CODEGRAPH_NO_DAEMON' not in os.environ
    if command == 'init':
        store = project / os.environ['CODEGRAPH_DIR']
        store.mkdir(parents=True, exist_ok=True)
        (store / 'codegraph.db').write_text('fixture code graph')
    if command == 'serve':
        print(json.dumps({'jsonrpc': '2.0', 'fixture': 'codegraph'}))
    else:
        print('CodeGraph maintenance diagnostics: ' + command)
'''


class RetrievalRuntimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="zero-retrieval-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.bin = self.root / "fixture-bin"
        self.bin.mkdir()
        (self.bin / "python3").symlink_to(sys.executable)
        for name, source in (
            ("node", FAKE_NODE), ("npm", FAKE_NPM), ("fixture-cli", FAKE_CLI)
        ):
            executable = self.bin / name
            executable.write_text(source)
            executable.chmod(0o755)
        # Detect accidental fallback to a globally installed retrieval CLI.
        for name in ("qmd", "codegraph"):
            executable = self.bin / name
            executable.write_text("#!/bin/sh\nexit 91\n")
            executable.chmod(0o755)
        self.project = self.make_project("project with spaces 项目")

    def make_project(self, name):
        project = self.root / name
        for folder in ("L1#Overview", "L3#Standards", "L5#Knowledge"):
            (project / ".ai" / folder).mkdir(parents=True, exist_ok=True)
        execution = project / ".ai/L0#Execution"
        shutil.copytree(EXECUTION / "workflows/local", execution / "workflows/local")
        shutil.copytree(
            EXECUTION / "configs/retrieval-toolchain", execution / "configs/retrieval-toolchain"
        )
        (project / ".ai/events.jsonl").write_text("")
        (project / ".ai/L3#Standards/source.md").write_text("# Source knowledge\n")
        return project

    def run_adapter(self, action, *, project=None, timeout=20, **overrides):
        env = dict(os.environ, PATH=str(self.bin) + os.pathsep + "/usr/bin:/bin")
        env.update(overrides)
        return subprocess.run(
            ["/bin/bash", str(ADAPTER), action], cwd=project or self.project,
            env=env, capture_output=True, text=True, timeout=timeout,
        )

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def events(self, project=None):
        lines = ((project or self.project) / ".ai/events.jsonl").read_text().splitlines()
        return [json.loads(line) for line in lines]

    def count(self, cli, command, project=None):
        return sum(
            item["cli"] == cli and item["args"][0] == command
            for item in self.events(project)
        )

    def wait_until(self, predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while not predicate():
            self.assertLess(time.monotonic(), deadline, "Background fixture did not finish")
            time.sleep(0.02)

    def test_cold_init_installs_pins_prefetches_models_and_keeps_state_inside_ai(self):
        self.assert_success(self.run_adapter("init"))
        generated = self.project / GENERATED
        self.assertEqual(len(list((generated / "cache/qmd/models").glob("*.gguf"))), 3)
        manifest = json.loads((generated / "qmd/models-manifest.json").read_text())
        self.assertEqual(len(manifest["models"]), 3)
        self.assertEqual(self.count("npm", "ci"), 1)
        self.assertEqual(self.count("qmd", "pull"), 1)
        self.assertEqual(self.count("qmd", "embed"), 1)
        self.assertEqual(self.count("codegraph", "init"), 1)
        self.assertEqual(self.count("codegraph", "sync"), 1)
        self.assertEqual(set(p.name for p in self.project.iterdir()), {".ai", ".codegraph"})
        self.assertEqual((self.project / ".codegraph").resolve(), generated / "codegraph")
        self.assertEqual(
            (self.project / ".ai/L3#Standards/source.md").read_text(), "# Source knowledge\n"
        )

    def test_setup_is_idempotent_and_refresh_does_not_prefetch_models(self):
        for action in ("setup", "setup", "init", "refresh"):
            self.assert_success(self.run_adapter(action))
        self.assertEqual(self.count("npm", "ci"), 1)
        self.assertEqual(self.count("qmd", "pull"), 1)

    def test_repeated_init_verifies_own_model_hashes_and_skips_network_pull(self):
        self.assert_success(self.run_adapter("init"))
        # A remote HEAD/pull failure cannot delete previously verified models.
        result = self.run_adapter("init", FIXTURE_FAIL_PULL="1")
        self.assert_success(result)
        self.assertIn("verified by SHA256", result.stderr)
        self.assertEqual(self.count("qmd", "pull"), 1)

    def test_changed_model_cache_requires_pull_and_rewrites_own_manifest(self):
        self.assert_success(self.run_adapter("init"))
        models = self.project / GENERATED / "cache/qmd/models"
        model = next(models.glob("*.gguf"))
        original = model.read_bytes()
        # Preserve the valid header and length: only a full digest detects this.
        model.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
        self.assert_success(self.run_adapter("init"))
        self.assertEqual(self.count("qmd", "pull"), 2)
        self.assertEqual(model.read_bytes(), original)
        self.assert_success(self.run_adapter("init", FIXTURE_FAIL_PULL="1"))
        self.assertEqual(self.count("qmd", "pull"), 2)

    def test_existing_models_without_success_manifest_still_require_official_pull(self):
        self.assert_success(self.run_adapter("init"))
        (self.project / GENERATED / "qmd/models-manifest.json").unlink()
        self.assert_success(self.run_adapter("init"))
        self.assertEqual(self.count("qmd", "pull"), 2)

    def test_existing_collection_without_exclusions_is_updated_without_forced_embed(self):
        self.assert_success(self.run_adapter("refresh"))
        config = self.project / GENERATED / "qmd/config/zero.yml"
        previous = json.loads(config.read_text())
        previous["collections"]["zero-ai"].pop("ignore")
        config.write_text(json.dumps(previous))
        self.assert_success(self.run_adapter("refresh"))
        current = json.loads(config.read_text())["collections"]["zero-ai"]
        self.assertEqual(current["ignore"], ["L0#Execution/backups/**", "**/.generated/**"])
        self.assertNotIn("L0#Execution/evidence/**", current["ignore"])
        embeds = [event["args"] for event in self.events() if event["cli"] == "qmd" and event["args"][0] == "embed"]
        self.assertTrue(all("-f" not in args for args in embeds))

    def test_existing_model_config_drift_is_repaired_without_forcing_same_model_vectors(self):
        self.assert_success(self.run_adapter("refresh"))
        config = self.project / GENERATED / "qmd/config/zero.yml"
        previous = json.loads(config.read_text())
        previous["models"]["generate"] = "hf:fixture/old-generator/old.gguf"
        config.write_text(json.dumps(previous))
        self.assert_success(self.run_adapter("refresh"))
        current = json.loads(config.read_text())
        self.assertNotEqual(current["models"]["generate"], previous["models"]["generate"])
        embeds = [event["args"] for event in self.events() if event["cli"] == "qmd" and event["args"][0] == "embed"]
        self.assertTrue(all("-f" not in args for args in embeds))

    def test_old_yaml_policy_is_normalized_without_forcing_verified_model_vectors(self):
        self.assert_success(self.run_adapter("refresh"))
        config = self.project / GENERATED / "qmd/config/zero.yml"
        config.write_text("models:\n  embed: " + EMBED_MODEL + "\ncollections: {}\n")
        self.assert_success(self.run_adapter("refresh"))
        self.assertEqual(json.loads(config.read_text())["models"]["embed"], EMBED_MODEL)
        embeds = [event["args"] for event in self.events() if event["cli"] == "qmd" and event["args"][0] == "embed"]
        self.assertTrue(all("-f" not in args for args in embeds))

    def test_simultaneous_initializations_install_once_and_serialize_writers(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            jobs = [pool.submit(self.run_adapter, "init", FIXTURE_INSTALL_DELAY="0.15") for _ in range(3)]
            for job in jobs:
                self.assert_success(job.result())
        self.assertEqual(self.count("npm", "ci"), 1)

    def test_failed_install_keeps_no_success_marker_and_recovers(self):
        self.assertNotEqual(self.run_adapter("setup", FIXTURE_FAIL_NPM="1").returncode, 0)
        self.assertFalse((self.project / GENERATED / "tools/install-fingerprint").exists())
        self.assert_success(self.run_adapter("setup"))
        self.assertEqual(self.count("npm", "ci"), 2)

    def test_model_download_failure_is_visible_and_skips_embedding(self):
        self.assertNotEqual(self.run_adapter("init", FIXTURE_FAIL_PULL="1").returncode, 0)
        self.assertEqual(self.count("qmd", "embed"), 0)
        self.assert_success(self.run_adapter("init"))
        self.assertEqual(self.count("npm", "ci"), 1)

    def test_embedding_failure_is_visible_and_refresh_recovers(self):
        self.assertNotEqual(self.run_adapter("init", FIXTURE_FAIL_EMBED="1").returncode, 0)
        self.assert_success(self.run_adapter("refresh"))
        self.assertEqual(self.count("npm", "ci"), 1)

    def test_cold_mcp_bootstrap_keeps_stdout_clean_and_skips_full_model_pull(self):
        gate = self.project / ".ai/embedding-gate"
        gate.touch()
        try:
            result = self.run_adapter("qmd-mcp", timeout=5, FIXTURE_EMBED_GATE=str(gate))
            self.assert_success(result)
            self.assertEqual(json.loads(result.stdout), {"jsonrpc": "2.0", "fixture": "qmd"})
            self.wait_until(lambda: self.count("qmd", "embed") == 1)
            self.assertEqual(self.count("qmd", "embed-finished"), 0)
            self.assertEqual(self.count("qmd", "pull"), 0)
        finally:
            gate.unlink(missing_ok=True)
            self.wait_until(lambda: self.count("qmd", "embed-finished") == 1)
        result = self.run_adapter("codegraph-mcp")
        self.assert_success(result)
        self.assertEqual(json.loads(result.stdout), {"jsonrpc": "2.0", "fixture": "codegraph"})

    def test_legacy_embedding_model_is_migrated_with_one_forced_rebuild(self):
        self.assert_success(self.run_adapter("setup"))
        generated = self.project / GENERATED
        config = generated / "qmd/config"
        config.mkdir(parents=True)
        database = generated / "cache/qmd/zero.sqlite"
        database.parent.mkdir(parents=True, exist_ok=True)
        database.write_text("legacy vectors")
        (config / "zero.yml").write_text("models:\n  embed: previous-model\n")
        (config / "source-root").write_text(str(self.project) + "\n")
        for _ in range(2):
            self.assert_success(self.run_adapter("refresh"))
        embeds = [event["args"] for event in self.events() if event["cli"] == "qmd" and event["args"][0] == "embed"]
        self.assertIn("-f", embeds[0])
        self.assertNotIn("-f", embeds[1])
        self.assertFalse((config / "reembed-required").exists())
        self.assertEqual(json.loads((config / "zero.yml").read_text())["models"]["embed"], EMBED_MODEL)

    def test_status_is_read_only_before_setup(self):
        self.assert_success(self.run_adapter("status"))
        self.assertEqual(self.events(), [])
        self.assertFalse((self.project / GENERATED).exists())

    def test_missing_lockfile_fails_before_install(self):
        (self.project / ".ai/L0#Execution/configs/retrieval-toolchain/package-lock.json").unlink()
        result = self.run_adapter("init")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lockfile", result.stderr)
        self.assertEqual(self.events(), [])

    def test_unsupported_node_fails_before_install(self):
        result = self.run_adapter("setup", FIXTURE_NODE_MAJOR="20")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Node.js >= 22", result.stderr)
        self.assertEqual(self.events(), [])

    def assert_refuses_external_alias(self, relative, action, *, directory):
        outside = self.root / "outside-state"
        outside.mkdir()
        sentinel = outside / "sentinel"
        sentinel.write_text("Keep external state unchanged\n")
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(outside if directory else sentinel, target_is_directory=directory)
        result = self.run_adapter(action)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("preflight refused", result.stderr)
        self.assertEqual(self.events(), [])
        self.assertEqual(list(outside.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_text(), "Keep external state unchanged\n")

    def test_setup_refuses_external_tools_directory_before_npm(self):
        self.assert_refuses_external_alias(GENERATED / "tools", "setup", directory=True)

    def test_mcp_refuses_external_model_cache_before_bootstrap(self):
        self.assert_refuses_external_alias(GENERATED / "cache", "qmd-mcp", directory=True)

    def test_refresh_refuses_external_lock_file_before_opening_it(self):
        self.assert_refuses_external_alias(GENERATED / "qmd/refresh.lock", "refresh", directory=False)

    def test_refresh_refuses_external_database_file(self):
        self.assert_refuses_external_alias(GENERATED / "cache/qmd/zero.sqlite", "refresh", directory=False)

    def test_init_refuses_external_database_in_legacy_codegraph_directory(self):
        self.assert_refuses_external_alias(Path(".codegraph/codegraph.db"), "init", directory=False)

    def test_real_npm_executable_links_and_owned_root_alias_remain_supported(self):
        self.assert_success(self.run_adapter("setup"))
        modules = self.project / GENERATED / "tools/node_modules"
        for name, package in (("qmd", "@tobilu/qmd"), ("codegraph", "@colbymchenry/codegraph")):
            executable = modules / ".bin" / name
            destination = modules / package / "fixture-cli"
            executable.rename(destination)
            executable.symlink_to(Path("..") / package / "fixture-cli")
        self.assert_success(self.run_adapter("init"))
        self.assert_success(self.run_adapter("refresh"))
        self.assertEqual(self.count("npm", "ci"), 1)
        self.assertEqual(os.readlink(self.project / ".codegraph"), ".ai/L5#Knowledge/.generated/codegraph")

    def socket_project(self):
        # macOS sockaddr_un paths are short; default temporary roots can exceed it.
        temporary = tempfile.TemporaryDirectory(prefix="zr-", dir="/tmp")
        self.addCleanup(temporary.cleanup)
        return self.make_project(str(Path(temporary.name).resolve() / "p"))

    def bind_fixture_socket(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(connection.close)
        connection.bind(str(path))
        return connection

    def test_owned_codegraph_daemon_socket_survives_refresh_and_mcp_startup(self):
        project = self.socket_project()
        self.assert_success(self.run_adapter("refresh", project=project))
        path = project / GENERATED / "codegraph/daemon.sock"
        connection = self.bind_fixture_socket(path)
        inode = path.lstat().st_ino
        self.assert_success(self.run_adapter("refresh", project=project))
        result = self.run_adapter("codegraph-mcp", project=project)
        self.assert_success(result)
        self.assertEqual(json.loads(result.stdout), {"jsonrpc": "2.0", "fixture": "codegraph"})
        self.assertEqual(path.lstat().st_ino, inode)
        self.assertEqual(connection.getsockname(), str(path))

    def test_socket_outside_exact_codegraph_daemon_path_is_rejected(self):
        project = self.socket_project()
        path = project / GENERATED / "qmd/unexpected.sock"
        connection = self.bind_fixture_socket(path)
        inode = path.lstat().st_ino
        result = self.run_adapter("refresh", project=project)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("preflight refused", result.stderr)
        self.assertEqual(self.events(project), [])
        self.assertEqual(path.lstat().st_ino, inode)
        self.assertEqual(connection.getsockname(), str(path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
