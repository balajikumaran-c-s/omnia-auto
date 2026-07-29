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
omnia-auto — Central Configuration

All defaults live here.  Consumer modules override them via
``configure()`` — no values are hard-wired to any specific module.

Usage (from the consumer's conftest.py)::

    import omnia_auto
    omnia_auto.configure(
        module_root  = os.path.dirname(__file__),   # test/ dir
        config_file  = "test_config.yml",
        credentials_file = "test_creds.yml",
        credentials_key  = ".test_creds.key",
        default_timeout  = 3600,                    # override 7200
    )
"""

import os

# =============================================================================
# MUTABLE DEFAULTS — consumer overrides via configure()
# =============================================================================

_defaults = {
    # --- Module root (set via init_module_root / configure) ---
    "module_root": None,

    # --- Config file names (consumer MUST set these) ---
    "config_file": "test_config.yml",
    "credentials_file": "test_creds.yml",
    "credentials_key": ".test_creds.key",

    # --- SSH options (string form — rsync, scp) ---
    "ssh_opts": (
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/dev/null "
        "-o LogLevel=ERROR"
    ),

    # --- SSH options (list form — subprocess calls) ---
    "ssh_options_list": [
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=10",
    ],

    # --- Runner defaults ---
    "default_verbosity": 1,
    "default_timeout": 7200,   # 2 hours — consumer can lower this
    "line_width": 160,
    "runner_logger_name": "playbook_runner",
}


# =============================================================================
# PUBLIC API
# =============================================================================

def configure(**kwargs) -> None:
    """Override package defaults from the consumer module.

    Any key in ``_defaults`` can be overridden.  Unknown keys are
    stored as well so modules can stash their own settings.

    Example::

        omnia_auto.configure(
            module_root="/root/image-build-manager/test",
            config_file="test_config.yml",
            default_timeout=1800,
        )
    """
    for key, value in kwargs.items():
        if key == "module_root" and value:
            _defaults[key] = os.path.abspath(value)
        else:
            _defaults[key] = value


def get_setting(key, default=None):
    """Get a configured setting value.

    Returns the stored value if not None, otherwise *default*.
    """
    val = _defaults.get(key)
    return val if val is not None else default


def init_module_root(path: str) -> None:
    """Convenience wrapper — sets ``module_root`` in the config."""
    _defaults["module_root"] = os.path.abspath(path)


def get_module_root() -> str:
    """Get the module root directory.

    Resolution order:
      1. Value set via ``init_module_root()`` / ``configure()``
      2. ``OMNIA_TEST_ROOT`` environment variable
      3. Current working directory (last-resort fallback)
    """
    root = _defaults.get("module_root")
    if root:
        return root
    env = os.environ.get("OMNIA_TEST_ROOT")
    if env:
        _defaults["module_root"] = os.path.abspath(env)
        return _defaults["module_root"]
    return os.getcwd()
