# omnia-auto

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)

Plug-and-play test automation utilities for [Dell Omnia](https://github.com/dell/omnia) modules.

Provides reusable functions for formatting, host connectivity, playbook execution, file synchronisation, and test reporting — with **zero hardcoded values**. Every setting is driven by the consumer module via `configure()`.

## Features

- **Formatting** — ANSI colors, Unicode symbols, structured `TestLogger`
- **Host / Config** — YAML config loading, Ansible Vault credential encryption, testinfra host connection
- **Runner** — `run_playbook()` with live output streaming, timeout, SSH wrapping
- **Sync** — `clone_repo()` and `sync_files()` for local or SSH file transfer
- **Report** — `TestReport` for JSON and HTML test result generation

## Installation

### From wheel (recommended for internal use)

```bash
# Build the wheel
cd omnia-auto
python -m build --wheel

# Install
pip install dist/omnia_auto-0.1.0-py3-none-any.whl
```

### From source (editable / development)

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
import os
import omnia_auto

# 1. Configure — consumer passes ALL settings
omnia_auto.configure(
    module_root=os.path.dirname(__file__),
    config_file="test_config.yml",
    credentials_file="test_creds.yml",
    credentials_key=".test_creds.key",
    default_timeout=3600,
)

# 2. Use
from omnia_auto import TestLogger, load_test_config, run_playbook

log = TestLogger("Verify module deployment", "TC_001")
log.check("Loading configuration...")
config = load_test_config()
log.passed(f"Config loaded for {config.get('project_name')}")

# 3. Run a playbook
result = run_playbook(tag="prepare", timeout=1800)
assert result["success"], result["error"]
```

See **[USAGE.md](USAGE.md)** for the complete function reference.

## Contributing

1. **Fork** the repository
2. **Create a branch** — `git checkout -b feature/my-change`
3. **Make changes** and test
4. **Build** — `python -m build --wheel`
5. **Commit** — `git commit -s -m "feat: description"` (use `--signoff`)
6. **Push** — `git push origin feature/my-change`
7. **Open a Pull Request**

### Building a new wheel

```bash
# Clean previous builds
rm -rf dist/ build/ src/*.egg-info

# Build
python -m build --wheel

# The wheel is in dist/
ls dist/
# omnia_auto-0.1.0-py3-none-any.whl
```

### Installing in a consumer module

```bash
# Install from local wheel
pip install dist/omnia_auto-0.1.0-py3-none-any.whl

# Or force-reinstall after rebuild
pip install --force-reinstall dist/omnia_auto-0.1.0-py3-none-any.whl
```

## Project Structure

```
omnia-auto/
├── pyproject.toml                  # Package metadata and dependencies
├── README.md                       # This file
├── USAGE.md                        # Function reference and examples
├── LICENSE                         # Apache 2.0
└── src/omnia_auto/
    ├── __init__.py                 # Public API exports
    ├── functions/
    │   ├── formatting_func.py      # Colors, Symbols, TestLogger, log()
    │   ├── host_func.py            # Config/credentials loading, testinfra host
    │   ├── report_func.py          # TestReport (JSON + HTML)
    │   ├── runner_func.py          # run_playbook() with live streaming
    │   └── sync_func.py            # clone_repo(), sync_files()
    ├── vars/
    │   └── common_vars.py          # configure(), get_setting()
    └── messages/
        └── runner_msgs.py          # Log and assertion message templates
```

## License

Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
