# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
omnia-auto — Shared Test Automation Utilities for Omnia

Plug-and-play library: all values come from the consumer via
``configure()`` — no module-specific defaults are baked in.

Usage::

    import omnia_auto

    omnia_auto.configure(
        module_root  = os.path.dirname(__file__),
        config_file  = "test_config.yml",
        default_timeout = 3600,
    )

    from omnia_auto import TestLogger, TestReport, get_testinfra_host
"""

__version__ = "0.1.0"

# --- Central config ---
from .vars.common_vars import (
    configure,
    get_setting,
    init_module_root,
    get_module_root,
)

# --- Formatting ---
from .functions.formatting_func import (
    Colors,
    Symbols,
    log,
    set_debug_mode,
    TestLogger,
    get_test_output,
)

# --- Host / Config ---
from .functions.host_func import (
    get_testinfra_host,
    load_test_config,
    load_test_credentials,
    run_on_host,
    is_local_execution,
    encrypt_test_credentials,
)

# --- Report ---
from .functions.report_func import (
    TestReport,
    get_current_report,
    set_current_report,
)

# --- Runner ---
from .functions.runner_func import run_playbook

# --- Sync ---
from .functions.sync_func import clone_repo, sync_files

__all__ = [
    "__version__",
    # Config
    "configure",
    "get_setting",
    "init_module_root",
    "get_module_root",
    # Formatting
    "Colors",
    "Symbols",
    "log",
    "set_debug_mode",
    "TestLogger",
    "get_test_output",
    # Host
    "get_testinfra_host",
    "load_test_config",
    "load_test_credentials",
    "run_on_host",
    "is_local_execution",
    "encrypt_test_credentials",
    # Report
    "TestReport",
    "get_current_report",
    "set_current_report",
    # Runner
    "run_playbook",
    # Sync
    "clone_repo",
    "sync_files",
]
