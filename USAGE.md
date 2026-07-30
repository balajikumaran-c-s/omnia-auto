# omnia-auto — Usage Guide

Complete function reference for the `omnia-auto` package.
Every function is documented with **inputs**, **outputs**, **errors**, and **examples**.

> **Design principle:** Zero hardcoded values.
> The consumer module passes all paths, variable names, and settings.
> If a required value is missing, the function raises an error — never falls back silently.

---

## Table of Contents

| Section | Source File | Functions |
|---------|-----------|-----------|
| [Configuration](#1-configuration) | `vars/common_vars.py` | `configure`, `get_setting`, `init_module_root`, `get_module_root` |
| [Formatting & Logging](#2-formatting--logging) | `functions/formatting_func.py` | `Colors`, `Symbols`, `TestLogger`, `log`, `set_debug_mode`, `get_test_output`, `add_session_result`, `print_summary_table` |
| [Host & Config](#3-host--config) | `functions/host_func.py` | `load_test_config`, `load_test_credentials`, `encrypt_test_credentials`, `get_testinfra_host`, `is_local_execution`, `run_on_host`, `connection_params`, `read_remote_env`, `ensure_remote_dir`, `resolve_domain_input_path` |
| [Sync](#4-sync) | `functions/sync_func.py` | `clone_repo`, `sync_files` |
| [Runner](#5-runner) | `functions/runner_func.py` | `run_playbook` |
| [Report](#6-report) | `functions/report_func.py` | `TestReport`, `get_current_report`, `set_current_report` |

---

## 1. Configuration

**Source:** `vars/common_vars.py`

### `configure(**kwargs)`

Initialize the package. Call **once** at the top of your `conftest.py`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `module_root` | `str` | **Yes** | Absolute path to the consumer's test directory |
| `config_file` | `str` | **Yes** | Config YAML filename (relative to `module_root`) |
| `credentials_file` | `str` | No | Credentials YAML filename |
| `credentials_key` | `str` | No | Vault key filename |
| `env_file` | `str` | No | Path to env file on target (default `/etc/omnia/omnia.env`) |
| `ssh_opts` | `str` | No | SSH options string |
| `default_verbosity` | `int` | No | Ansible verbosity 0-4 |
| `default_timeout` | `int` | No | Playbook timeout in seconds |
| `line_width` | `int` | No | Terminal output line width |
| `runner_logger_name` | `str` | No | Logger name for `run_playbook` |

Any extra key-value pairs are stored and retrievable with `get_setting()`.

```python
import os, omnia_auto

omnia_auto.configure(
    module_root=os.path.dirname(__file__),
    config_file="test_config.yml",
    credentials_file="test_creds.yml",
    credentials_key=".test_creds.key",
    env_file="/etc/omnia/omnia.env",
    default_timeout=3600,
)
```

### `get_setting(key, default=None) -> Any`

Retrieve a previously configured value.

```python
timeout = omnia_auto.get_setting("default_timeout")   # 3600
custom  = omnia_auto.get_setting("my_key", "fallback")
```

### `init_module_root(path)` / `get_module_root() -> str`

Set or get the module root directory.

```python
omnia_auto.init_module_root("/root/my-module/test")
root = omnia_auto.get_module_root()  # "/root/my-module/test"
```

---

## 2. Formatting & Logging

**Source:** `functions/formatting_func.py`

### `Colors`

ANSI color constants. Auto-disabled when output is piped (override with `FORCE_COLOR=1`).

```python
from omnia_auto import Colors
print(f"{Colors.BRIGHT_GREEN}PASS{Colors.RESET}")
```

| Attribute | Description |
|-----------|-------------|
| `RESET` | Reset all formatting |
| `BOLD`, `DIM` | Weight modifiers |
| `RED`, `GREEN`, `YELLOW`, `BLUE`, `CYAN`, `GRAY` | Standard colors |
| `BRIGHT_RED`, `BRIGHT_GREEN`, `BRIGHT_YELLOW`, `BRIGHT_BLUE`, `BRIGHT_CYAN` | Bright variants |

### `Symbols`

Unicode status indicators.

```python
from omnia_auto import Symbols
print(f"{Symbols.CHECK} Passed")   # ✔ Passed
print(f"{Symbols.CROSS} Failed")   # ✘ Failed
print(f"{Symbols.ARROW} Step")     # → Step
print(f"{Symbols.SKIP} Skipped")   # ↷ Skipped
```

| Attribute | Character | Use |
|-----------|-----------|-----|
| `CHECK` | ✔ | Passed |
| `CROSS` | ✘ | Failed |
| `ARROW` | → | Step / transition |
| `SKIP` | ↷ | Skipped |
| `TRIANGLE` | ▶ | Header |
| `PIPE` | │ | Detail indent |

### `log(message, level="INFO")`

Timestamped log line.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | `str` | **Yes** | Message text |
| `level` | `str` | No | `INFO`, `DEBUG`, `WARN`, `ERROR`, `OK` |

```python
from omnia_auto import log

log("Starting sync", "INFO")    # [14:30:00] [INFO] Starting sync
log("Debug detail", "DEBUG")    # Only printed when debug mode is on
log("Problem found", "WARN")
log("Fatal error", "ERROR")
log("All checks passed", "OK")
```

### `set_debug_mode(enabled: bool)`

Enable or disable `DEBUG` level output globally.

```python
from omnia_auto import set_debug_mode
set_debug_mode(True)   # DEBUG messages now visible
```

### `TestLogger(test_name, tc_id="")`

Structured test output logger. Captures output for reports.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `test_name` | `str` | **Yes** | Display name for the test |
| `tc_id` | `str` | No | Test case ID (e.g. `TC_IT_001`) |

| Method | Description |
|--------|-------------|
| `check(message)` | Log a check being performed (yellow arrow) |
| `info(message)` | Log informational message (blue arrow) |
| `passed(message, details=None)` | Log pass with optional multi-line details |
| `failed(message, details=None)` | Log failure with optional details |
| `skipped(message, details=None)` | Log skip with optional reason |
| `get_output() -> str` | Get all captured output as a single string |

```python
from omnia_auto import TestLogger

tl = TestLogger("Verify containers running", "TC_PR_001")
tl.check("Checking minio container...")
tl.passed("minio-server is running", "Status: Up 2 hours")
tl.failed("registry not found", "Expected: registry\nActual: not running")
output = tl.get_output()
```

### `get_test_output(test_name=None) -> str`

Get captured output from the last `TestLogger` instance.

### `add_session_result(test_name, status, duration, tc_id="")`

Accumulate a test result for the end-of-session summary table.
Call from your `pytest_runtest_makereport` hook.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `test_name` | `str` | **Yes** | Test function name |
| `status` | `str` | **Yes** | `PASSED`, `FAILED`, or `SKIPPED` |
| `duration` | `float` | **Yes** | Duration in seconds |
| `tc_id` | `str` | No | Test case ID |

```python
from omnia_auto import add_session_result

# In pytest_runtest_makereport hook:
add_session_result(
    test_name="test_container_running",
    status="PASSED",
    duration=1.23,
    tc_id="TC_PR_001",
)
```

### `print_summary_table()`

Print a formatted summary of all results accumulated via `add_session_result`.
Call from your `pytest_sessionfinish` hook. Prints nothing if no results were recorded.

Respects environment variables:
- `OMNIA_RESULTS_FILE` — export results to JSON for aggregation
- `OMNIA_SUPPRESS_SUMMARY` — skip printing (shell wrapper prints combined)

```python
from omnia_auto import print_summary_table

# In pytest_sessionfinish hook:
print_summary_table()
```

**Output example:**

```
=====================================================================================
  TEST EXECUTION SUMMARY
=====================================================================================
  TC ID        Test Name                                Status     Duration
  ------------ ---------------------------------------- ---------- --------
  TC_BD_002    test_s3_images_x86_64                    PASSED        1.58s
  TC_BD_003    test_s3_images_aarch64                   SKIPPED       0.85s
  TC_BD_004    test_registry_images_x86_64              PASSED        1.46s
  ------------ ---------------------------------------- ---------- --------
  3 passed, 0 failed, 0 skipped / 3 total (3.89s)
=====================================================================================
```

---

## 3. Host & Config

**Source:** `functions/host_func.py`

### `load_test_config() -> dict`

Load the consumer's YAML config file.

| Input | From `configure(config_file=...)` |
|-------|-----------------------------------|
| **Returns** | `dict` — parsed YAML contents |
| **Raises** | `RuntimeError` if config_file not configured |

```python
from omnia_auto import load_test_config

config = load_test_config()
ip      = config["oim_server_ip"]    # "10.0.0.1"
dataset = config["dataset"]          # "data_set_01"
```

### `load_test_credentials() -> dict`

Load credentials with automatic Ansible Vault handling.

| Scenario | Behaviour |
|----------|-----------|
| Plain YAML file exists | Reads it, generates vault key, encrypts it, returns dict |
| Encrypted file + key exists | Decrypts and returns dict |
| Encrypted file + key missing | Raises `ValueError` |
| File not found | Returns `{}` |

```python
from omnia_auto import load_test_credentials

creds = load_test_credentials()
password = creds.get("oim_password")
```

### `encrypt_test_credentials() -> bool`

Explicitly encrypt the credentials file. Returns `True` on success.

### `get_testinfra_host() -> Host`

Get a testinfra `Host` object for the target server.

| Config Value | Connection |
|-------------|------------|
| `oim_server_ip` empty or local | `testinfra.get_host("local://")` |
| `oim_server_ip` set to remote IP | SSH via ansible inventory |

```python
from omnia_auto import get_testinfra_host

host = get_testinfra_host()
result = host.run("hostname")
print(result.stdout)  # "image-builder"
```

### `is_local_execution() -> bool`

Returns `True` when `oim_server_ip` is empty or matches a local interface IP.

### `run_on_host(host, cmd) -> result`

Run a shell command on the target.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `host` | `Host` | **Yes** | Testinfra host object |
| `cmd` | `str` | **Yes** | Shell command string |

| Returns | `result` object with `.stdout`, `.stderr`, `.rc` |
|---------|--------------------------------------------------|

```python
from omnia_auto import get_testinfra_host, run_on_host

host = get_testinfra_host()
result = run_on_host(host, "podman ps --format '{{.Names}}'")
print(result.stdout)
```

### `connection_params() -> dict`

Build a connection dict from the consumer's config and credentials.
Ready to unpack into `sync_files()` or `clone_repo()`.

| Returns | Dict with keys |
|---------|---------------|
| `mode` | `"local"` or `"ssh"` |
| `ip` | Target IP or `None` |
| `user` | SSH username |
| `password` | SSH password or `None` |
| `ssh_opts` | SSH options string |

| Raises | `ValueError` if `oim_server_ip` or `oim_ssh_user` missing for remote mode |
|--------|----------------------------------------------------------------------------|

```python
from omnia_auto import connection_params, sync_files

conn = connection_params()
# conn = {"mode": "ssh", "ip": "10.0.0.1", "user": "root", ...}

result = sync_files(
    mode=conn["mode"],
    src="/local/path",
    dest="/remote/path",
    ip=conn["ip"],
    user=conn["user"],
    password=conn["password"],
    ssh_opts=conn["ssh_opts"],
)
```

### `read_remote_env(host, var_name, env_file=None) -> str`

Read an environment variable from the target host.

Sources the env file on the target before reading, so variables set by
setup scripts are available even in non-login SSH shells.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `host` | `Host` | **Yes** | Testinfra host object |
| `var_name` | `str` | **Yes** | Variable name to read (e.g. `"OMNIA_DATA_PATH"`) |
| `env_file` | `str` | No | Path to env file on target. Defaults to `configure(env_file=...)` or `/etc/omnia/omnia.env` |

| Returns | `str` — the variable value, stripped |
|---------|--------------------------------------|
| **Raises** | `ValueError` if the variable is **not set or empty** on the target |

**No fallback values.** If the variable is missing, the function raises — never returns a silent default.

```python
from omnia_auto import get_testinfra_host, read_remote_env

host = get_testinfra_host()

# Read OMNIA_DATA_PATH — raises ValueError if not set
data_path = read_remote_env(host, "OMNIA_DATA_PATH")
# data_path = "/opt/omnia"

# Read from a custom env file
value = read_remote_env(host, "MY_VAR", env_file="/etc/myapp/env")
```

### `ensure_remote_dir(host, path) -> None`

Create a directory on the target if it does not exist (`mkdir -p`).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `host` | `Host` | **Yes** | Testinfra host object |
| `path` | `str` | **Yes** | Absolute path to create |

| Returns | `None` |
|---------|--------|
| **Raises** | `ValueError` if `path` is empty |
| **Raises** | `RuntimeError` if `mkdir -p` fails |

```python
from omnia_auto import get_testinfra_host, ensure_remote_dir

host = get_testinfra_host()
ensure_remote_dir(host, "/opt/omnia/image_build_manager/input/project_default")
```

### `resolve_domain_input_path(host, domain, data_path_var, project_var) -> str`

Build the remote input directory for a domain by reading env vars from the target.

Assembles: `<data_path>/<domain>/input/<project>/`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `host` | `Host` | **Yes** | Testinfra host object |
| `domain` | `str` | **Yes** | Domain name (e.g. `"image_build_manager"`) — consumer defines this in its own vars |
| `data_path_var` | `str` | **Yes** | Env var name for the data path (e.g. `"OMNIA_DATA_PATH"`) — consumer passes this |
| `project_var` | `str` | **Yes** | Env var name for the project (e.g. `"OMNIA_PROJECT_NAME"`) — consumer passes this |

| Returns | `str` — absolute path on the target |
|---------|--------------------------------------|
| **Raises** | `ValueError` if `domain` is empty or either env var is not set on target |

**No hardcoded paths.** The consumer passes the env var **names** and the function reads their values from the target.

```python
from omnia_auto import get_testinfra_host, resolve_domain_input_path

host = get_testinfra_host()

# Consumer defines these in its own vars/common_vars.py:
# DOMAIN_NAME = "image_build_manager"
# ENV_OMNIA_DATA_PATH = "OMNIA_DATA_PATH"
# ENV_OMNIA_PROJECT_NAME = "OMNIA_PROJECT_NAME"

path = resolve_domain_input_path(
    host,
    domain="image_build_manager",
    data_path_var="OMNIA_DATA_PATH",
    project_var="OMNIA_PROJECT_NAME",
)
# path = "/opt/omnia/image_build_manager/input/project_default"
```

---

## 4. Sync

**Source:** `functions/sync_func.py`

Both functions are **fully parameter-driven**. The consumer passes everything.
The package reads nothing from config files for sync operations.

### `clone_repo(mode, url, dest, ...) -> dict`

Clone or pull a git repository.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mode` | `str` | **Yes** | `"local"` or `"ssh"` |
| `url` | `str` | **Yes** | Git clone URL |
| `dest` | `str` | **Yes** | Destination path |
| `ip` | `str` | No* | Target IP (*required for SSH mode) |
| `user` | `str` | No | SSH user (default `"root"`) |
| `password` | `str` | No | SSH password (uses `sshpass` if set) |
| `ssh_opts` | `str` | No | SSH options string |
| `force` | `bool` | No | Remove existing and re-clone (default `False`) |
| `timeout` | `int` | No | Subprocess timeout in seconds (default `300`) |

| Returns | `dict` with keys: `success` (bool), `details` (str), `error` (str) |
|---------|---------------------------------------------------------------------|

```python
from omnia_auto import clone_repo

result = clone_repo(
    mode="ssh",
    url="https://github.com/dell/omnia.git",
    dest="/root/omnia",
    ip="10.0.0.1",
    user="root",
)
assert result["success"], result["error"]
```

### `sync_files(mode, src, dest, ...) -> dict`

Sync files or directories. Uses `rsync` for directories, `cp`/`scp` for single files.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mode` | `str` | **Yes** | `"local"` or `"ssh"` |
| `src` | `str` | **Yes** | Source path (local filesystem) |
| `dest` | `str` | **Yes** | Destination path |
| `ip` | `str` | No* | Target IP (*required for SSH mode) |
| `user` | `str` | No | SSH user (default `"root"`) |
| `password` | `str` | No | SSH password |
| `ssh_opts` | `str` | No | SSH options string |
| `timeout` | `int` | No | Subprocess timeout in seconds (default `120`) |
| `mkdir` | `bool` | No | Create dest directory before sync (default `True`) |

| Returns | `dict` with keys: `success` (bool), `details` (str), `error` (str) |
|---------|---------------------------------------------------------------------|

```python
from omnia_auto import sync_files

result = sync_files(
    mode="ssh",
    src="/root/datasets/input",
    dest="/opt/omnia/image_build_manager/input/project_default",
    ip="10.0.0.1",
    user="root",
)
assert result["success"], result["error"]
```

---

## 5. Runner

**Source:** `functions/runner_func.py`

### `run_playbook(playbook, tag, ...) -> dict`

Run `ansible-playbook` with live output streaming.
Wraps the command in SSH for remote targets automatically.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `playbook` | `str` | **Yes** | Playbook filename — consumer must pass this from its own vars |
| `tag` | `str` or `list` | No | Ansible tag(s): `"prepare"` or `["prepare", "build"]` |
| `extra_vars` | `dict` | No | Extra `-e key=value` pairs |
| `verbosity` | `int` | No | Ansible `-v` level 0-4 |
| `timeout` | `int` | No | Max seconds to wait |
| `limit` | `str` | No | Ansible `--limit` pattern |
| `playbook_workdir` | `str` | **Yes** | Subdir under `clone_path` — consumer must pass this from its own vars |

| Returns | `dict` with keys |
|---------|------------------|
| `success` | `bool` — `True` if exit code 0 |
| `rc` | `int` — exit code |
| `output` | `str` — full stdout |
| `duration` | `float` — seconds |
| `error` | `str` — error message if failed |
| `playbook` | `str` — playbook filename used |

**Important:** `playbook` and `playbook_workdir` are **required** — no fallback values.
The consumer defines them in its own `vars/common_vars.py` and wraps `run_playbook`
so test files stay clean:

```python
# Consumer's vars/common_vars.py
PLAYBOOK_ENTRY_POINT = "image_build_manager.yml"
PLAYBOOK_WORKDIR = "src/image_build_manager/playbooks"

# Consumer's functions/__init__.py
from omnia_auto import run_playbook as _run_playbook
from ..vars.common_vars import PLAYBOOK_ENTRY_POINT, PLAYBOOK_WORKDIR

def run_playbook(tag=None, **kwargs):
    """Wrapper that injects module-specific playbook and workdir."""
    return _run_playbook(
        playbook=kwargs.pop("playbook", PLAYBOOK_ENTRY_POINT),
        playbook_workdir=kwargs.pop("playbook_workdir", PLAYBOOK_WORKDIR),
        tag=tag,
        **kwargs,
    )
```

Test files then call it simply:

```python
# Consumer's test file
from library.functions import run_playbook

result = run_playbook(tag="prepare", timeout=1800)
assert result["success"], result["error"]
```

---

## 6. Report

**Source:** `functions/report_func.py`

### `TestReport(module_name, report_path, report_name, server_ip, ...)`

Test report generator. Produces JSON and HTML reports organized by server.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `module_name` | `str` | **Yes** | Scenario/module name (e.g. `"validate"`) |
| `report_path` | `str` | **Yes** | Absolute directory where JSON/HTML are saved |
| `report_name` | `str` | **Yes** | Base filename without extension |
| `server_ip` | `str` | **Yes** | Target server IP address |
| `report_id` | `str` | No | Report run ID (default: auto-generated timestamp) |

| Method | Description |
|--------|-------------|
| `add_result(result_dict)` | Add a test result (dict with `test_name`, `status`, `duration`, `details`, `error`) |
| `save()` | Write JSON + HTML report files |
| `results` | List of accumulated result dicts |

```python
from omnia_auto import TestReport, set_current_report, get_current_report

# Create and set as active report
report = TestReport(
    module_name="validate",
    report_path="/opt/omnia/reports",
    report_name="image_test_report",
    server_ip="10.0.0.1",
    report_id="20260730120000",
)
set_current_report(report)

# Save at session end
report.save()
# Creates: /opt/omnia/reports/image_test_report.json
# Creates: /opt/omnia/reports/image_test_report.html

# Retrieve active report
current = get_current_report()
```

---

## Full Consumer Example

A complete `conftest.py` showing how a consumer module uses `omnia-auto`:

```python
import sys, os, pytest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
if _TEST_DIR not in sys.path:
    sys.path.insert(0, _TEST_DIR)

# 1. Configure the package
import omnia_auto
omnia_auto.configure(
    module_root=_TEST_DIR,
    config_file="test_config.yml",
    credentials_file="test_creds.yml",
    credentials_key=".test_creds.key",
    env_file="/etc/omnia/omnia.env",
)

# 2. Import what you need
from omnia_auto import (
    get_testinfra_host, load_test_config,
    encrypt_test_credentials, connection_params,
    read_remote_env, ensure_remote_dir,
    resolve_domain_input_path, sync_files,
    TestReport, set_current_report, get_current_report,
    add_session_result, print_summary_table, log,
)

# 3. Consumer defines domain constants in its own vars
from library.vars.common_vars import (
    DOMAIN_NAME,              # "image_build_manager"
    ENV_OMNIA_DATA_PATH,      # "OMNIA_DATA_PATH"
    ENV_OMNIA_PROJECT_NAME,   # "OMNIA_PROJECT_NAME"
)


def pytest_sessionstart(session):
    encrypt_test_credentials()
    config = load_test_config()
    host = get_testinfra_host()
    conn = connection_params()

    # Sync input files to env-var-based path on target
    remote_input = resolve_domain_input_path(
        host, DOMAIN_NAME, ENV_OMNIA_DATA_PATH, ENV_OMNIA_PROJECT_NAME,
    )
    ensure_remote_dir(host, remote_input)
    local_input = os.path.join(
        _TEST_DIR, "datasets", config["dataset"], "input",
    )
    result = sync_files(
        mode=conn["mode"], src=local_input, dest=remote_input,
        ip=conn["ip"], user=conn["user"],
        password=conn["password"], ssh_opts=conn["ssh_opts"],
    )
    assert result["success"], result["error"]

    # Init report
    report = TestReport(
        module_name="my_module",
        report_path=config.get("report_path", "/opt/omnia/reports"),
        report_name=config.get("report_name", "test_report"),
        server_ip=config.get("oim_server_ip", "localhost"),
    )
    set_current_report(report)


def pytest_sessionfinish(session, exitstatus):
    report = get_current_report()
    if report and report.results:
        report.save()
    print_summary_table()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    result = outcome.get_result()
    if result.when == "call":
        status = "PASSED" if result.passed else (
            "SKIPPED" if result.skipped else "FAILED"
        )
        add_session_result(
            test_name=item.name,
            status=status,
            duration=getattr(result, "duration", 0),
        )


@pytest.fixture(scope="session")
def host():
    return get_testinfra_host()
```

---

## Error Handling Summary

| Function | Error Type | When |
|----------|-----------|------|
| `read_remote_env` | `ValueError` | Env var not set on target |
| `ensure_remote_dir` | `ValueError` | Empty path passed |
| `ensure_remote_dir` | `RuntimeError` | `mkdir -p` fails |
| `resolve_domain_input_path` | `ValueError` | Empty domain or env var not set |
| `connection_params` | `ValueError` | Missing `oim_server_ip` or `oim_ssh_user` for remote mode |
| `run_playbook` | Returns `{"success": False}` | Missing `playbook` or `playbook_workdir` arg |
| `clone_repo` / `sync_files` | Returns `{"success": False}` | Invalid mode, missing params, subprocess failure |
| `load_test_credentials` | `ValueError` | Encrypted file but key missing |
