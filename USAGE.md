# omnia-auto — Usage Guide

Complete function reference and examples for the `omnia-auto` package.

---

## Table of Contents

- [Configuration](#configuration)
- [Formatting](#formatting)
- [Host & Config](#host--config)
- [Sync (Clone & File Transfer)](#sync-clone--file-transfer)
- [Runner (Playbook Execution)](#runner-playbook-execution)
- [Report](#report)
- [Defaults & Overrides](#defaults--overrides)

---

## Configuration

All settings are passed by the consumer module. No values are hardcoded.

### `configure(**kwargs)`

Set or override package defaults. Call this **once** early in your `conftest.py`.

```python
import os
import omnia_auto

omnia_auto.configure(
    module_root=os.path.dirname(__file__),
    config_file="test_config.yml",
    credentials_file="test_creds.yml",
    credentials_key=".test_creds.key",
    default_timeout=3600,
    default_verbosity=2,
    ssh_opts="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null",
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `module_root` | `str` | `None` | Absolute path to the consumer's `test/` directory |
| `config_file` | `str` | `"test_config.yml"` | Config file name (relative to `module_root`) |
| `credentials_file` | `str` | `"test_creds.yml"` | Credentials file name |
| `credentials_key` | `str` | `".test_creds.key"` | Vault key file name |
| `ssh_opts` | `str` | `"-o StrictHostKeyChecking=no ..."` | SSH options string |
| `ssh_options_list` | `list` | `["-o", "StrictHostKeyChecking=no", ...]` | SSH options as list |
| `default_verbosity` | `int` | `1` | Ansible verbosity level (0–4) |
| `default_timeout` | `int` | `7200` | Playbook timeout in seconds |
| `line_width` | `int` | `160` | Terminal output line width |
| `runner_logger_name` | `str` | `"playbook_runner"` | Logger name for run_playbook |

Any key can be passed — unknown keys are stored and retrievable via `get_setting()`.

### `get_setting(key, default=None)`

Retrieve a configured value.

```python
timeout = omnia_auto.get_setting("default_timeout")       # 3600
custom  = omnia_auto.get_setting("my_custom_key", "fallback")
```

### `init_module_root(path)` / `get_module_root()`

Convenience functions for the `module_root` setting.

```python
omnia_auto.init_module_root("/root/my-module/test")
root = omnia_auto.get_module_root()  # "/root/my-module/test"
```

Fallback order: `configure()` value → `OMNIA_TEST_ROOT` env var → `os.getcwd()`.

---

## Formatting

### `Colors`

ANSI color codes. Automatically disabled when output is piped (override with `FORCE_COLOR=1`).

```python
from omnia_auto import Colors

print(f"{Colors.GREEN}PASS{Colors.RESET}")
print(f"{Colors.BRIGHT_RED}FAIL{Colors.RESET}")
```

Available: `RESET`, `BOLD`, `DIM`, `RED`, `GREEN`, `YELLOW`, `BLUE`, `CYAN`, `GRAY`, `BRIGHT_RED`, `BRIGHT_GREEN`, `BRIGHT_YELLOW`, `BRIGHT_BLUE`, `BRIGHT_CYAN`.

### `Symbols`

Unicode status indicators.

```python
from omnia_auto import Symbols

print(f"{Symbols.CHECK} Passed")   # ✔ Passed
print(f"{Symbols.CROSS} Failed")   # ✘ Failed
print(f"{Symbols.ARROW} Step")     # → Step
print(f"{Symbols.SKIP} Skipped")   # ↷ Skipped
```

### `TestLogger(test_name, tc_id="")`

Structured test output logger for pytest.

```python
from omnia_auto import TestLogger

log = TestLogger("Verify containers", "TC_001")
log.check("Checking container status...")
log.info("Found 3 containers")
log.passed("All containers running", "minio: up\nregistry: up\ns3: up")
log.skipped("aarch64 not applicable")
log.failed("Container missing", "Expected: minio\nGot: not found")

output = log.get_output()  # Captured output as string
```

### `log(message, level="INFO")`

Simple timestamped logging.

```python
from omnia_auto import log

log("Starting test", "INFO")    # [14:30:00] [INFO] Starting test
log("Debug info", "DEBUG")      # Only printed when debug mode is on
log("Warning", "WARN")
log("Error occurred", "ERROR")
log("Success", "OK")
```

### `set_debug_mode(enabled)`

Enable/disable DEBUG level output.

```python
from omnia_auto import set_debug_mode
set_debug_mode(True)   # DEBUG messages now print
```

---

## Host & Config

### `load_test_config() -> dict`

Load the YAML config file (name from `configure(config_file=...)`).

```python
from omnia_auto import load_test_config

config = load_test_config()
ip = config["oim_server_ip"]
dataset = config["dataset"]
```

### `load_test_credentials() -> dict`

Load credentials with automatic Ansible Vault encryption.

- **Plain file** → reads it, creates a vault key, encrypts it, returns dict
- **Encrypted file + key exists** → decrypts and returns dict
- **Encrypted file + key missing** → raises `ValueError`
- **File not found** → returns empty dict

```python
from omnia_auto import load_test_credentials

creds = load_test_credentials()
password = creds.get("oim_password", "")
```

### `encrypt_test_credentials() -> bool`

Explicitly encrypt the credentials file. Returns `True` on success.

### `get_testinfra_host()`

Get a testinfra `Host` object connected to the target server.

- **Local IP / empty** → `testinfra.get_host("local://")`
- **Remote IP** → SSH connection via ansible inventory

```python
from omnia_auto import get_testinfra_host

host = get_testinfra_host()
result = host.run("hostname")
print(result.stdout)
```

### `is_local_execution() -> bool`

Returns `True` when `oim_server_ip` is empty or matches a local IP.

### `run_on_host(host, cmd) -> result`

Run a command on the target host.

```python
from omnia_auto import get_testinfra_host, run_on_host

host = get_testinfra_host()
result = run_on_host(host, "podman ps --format '{{.Names}}'")
print(result.stdout)
```

---

## Sync (Clone & File Transfer)

Both functions are **fully parameter-driven**. The consumer passes everything — `mode`, `ip`, `user`, `password`, `ssh_opts`. The package reads nothing from config files.

### `clone_repo(mode, url, dest, *, ip, user, password, ssh_opts, force, timeout) -> dict`

Clone or pull a git repository.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `str` | *required* | `"local"` or `"ssh"` |
| `url` | `str` | *required* | Git clone URL |
| `dest` | `str` | *required* | Destination path |
| `ip` | `str` | `None` | Target IP (required for SSH) |
| `user` | `str` | `"root"` | SSH user |
| `password` | `str` | `None` | SSH password (uses `sshpass` when set) |
| `ssh_opts` | `str` | `"-o StrictHostKeyChecking=no ..."` | SSH options |
| `force` | `bool` | `False` | Remove existing repo and re-clone |
| `timeout` | `int` | `300` | Subprocess timeout in seconds |

**Returns:** `{"success": bool, "details": str, "error": str}`

```python
from omnia_auto import clone_repo

# Local clone
result = clone_repo(
    mode="local",
    url="https://github.com/dell/omnia.git",
    dest="/root/omnia",
)

# SSH clone
result = clone_repo(
    mode="ssh",
    url="https://github.com/dell/omnia.git",
    dest="/root/omnia",
    ip="10.0.0.1",
    user="root",
    password="my_password",
)
assert result["success"], result["error"]
```

### `sync_files(mode, src, dest, *, ip, user, password, ssh_opts, timeout, mkdir) -> dict`

Sync files or directories. Automatically uses `rsync` for directories and `cp`/`scp` for single files.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `str` | *required* | `"local"` or `"ssh"` |
| `src` | `str` | *required* | Source path (local filesystem) |
| `dest` | `str` | *required* | Destination path |
| `ip` | `str` | `None` | Target IP (required for SSH) |
| `user` | `str` | `"root"` | SSH user |
| `password` | `str` | `None` | SSH password |
| `ssh_opts` | `str` | `"-o StrictHostKeyChecking=no ..."` | SSH options |
| `timeout` | `int` | `120` | Subprocess timeout in seconds |
| `mkdir` | `bool` | `True` | Create destination directory before sync |

**Returns:** `{"success": bool, "details": str, "error": str}`

```python
from omnia_auto import sync_files

# Sync a directory locally
result = sync_files(
    mode="local",
    src="/root/datasets/input",
    dest="/opt/omnia/input/project_default",
)

# Sync a file over SSH
result = sync_files(
    mode="ssh",
    src="/root/datasets/config.yml",
    dest="/root/omnia/config.yml",
    ip="10.0.0.1",
    user="root",
    password="my_password",
)
assert result["success"], result["error"]
```

---

## Runner (Playbook Execution)

### `run_playbook(playbook, tag, extra_vars, verbosity, timeout, limit, playbook_workdir) -> dict`

Run an `ansible-playbook` with live output streaming. Automatically wraps in SSH for remote targets.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `playbook` | `str` | from config `playbook_entry_point` or `"site.yml"` | Playbook filename |
| `tag` | `str` | `None` | Ansible tag (`prepare`, `build`, etc.) |
| `extra_vars` | `dict` | `None` | Extra `--extra-vars` key=value pairs |
| `verbosity` | `int` | from `configure(default_verbosity=...)` | Ansible `-v` level (0–4) |
| `timeout` | `int` | from `configure(default_timeout=...)` | Max wait in seconds |
| `limit` | `str` | `None` | Ansible `--limit` pattern |
| `playbook_workdir` | `str` | from config `playbook_workdir` or `"src"` | Subdir under clone_path |

**Returns:** `{"success": bool, "rc": int, "output": str, "duration": float, "error": str, "playbook": str}`

```python
from omnia_auto import run_playbook

result = run_playbook(tag="prepare", timeout=1800, verbosity=2)
assert result["success"], result["error"]
print(f"Completed in {result['duration']:.1f}s")
```

---

## Report

### `TestReport(report_path, report_name, report_id, server, module_name)`

Manage JSON and HTML test reports.

```python
from omnia_auto import TestReport

report = TestReport(
    report_path="/opt/omnia/reports",
    report_name="test_report",
    report_id="20260101120000",
    server="10.0.0.1",
    module_name="my_module",
)

report.add_result(
    test_name="test_container",
    tc_id="TC_001",
    status="passed",
    duration=1.5,
)

report.save()
```

### `get_current_report()` / `set_current_report(report)`

Global report accessor for pytest hooks.

---

## Defaults & Overrides

Every default in `omnia-auto` can be overridden by the consumer:

```python
import omnia_auto

# Override defaults
omnia_auto.configure(
    default_timeout=1800,        # 30 min instead of 2 hours
    default_verbosity=3,         # More ansible output
    line_width=200,              # Wider terminal output
    ssh_opts="-o StrictHostKeyChecking=no",  # Custom SSH options
)

# Check current value
print(omnia_auto.get_setting("default_timeout"))  # 1800

# Override again at any time
omnia_auto.configure(default_timeout=900)
```

### Error Handling

All sync and clone functions return a `dict` with `success`, `details`, and `error` keys:

```python
result = clone_repo(mode="ssh", url="...", dest="...", ip="10.0.0.1")
if not result["success"]:
    print(f"Error: {result['error']}")
```

Errors handled: invalid mode, missing required params, source not found, subprocess timeout, OS errors, SSH failures.
