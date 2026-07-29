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
Testinfra host, configuration, and credential utilities.

Every function accepts its required paths as parameters.
When a parameter is not passed, the value is looked up from
``get_setting()`` — which itself only returns what the consumer
configured via ``configure()``.

Handles:
- Config YAML loading
- Credentials loading + Ansible Vault encryption
- Testinfra host connection (local or remote SSH)
- Local vs remote execution detection
"""

import os
import subprocess
import tempfile
from typing import Dict, Any, Optional, Tuple

import yaml
import testinfra

from ..vars.common_vars import get_module_root, get_setting


# =============================================================================
# CONFIG LOADING
# =============================================================================

def _resolve_config_path(config_path: Optional[str] = None) -> str:
    """Resolve the config file path.

    Args:
        config_path: Explicit path.  When ``None``, built from
                     ``module_root`` + ``config_file`` setting.

    Raises:
        RuntimeError: If neither param nor setting is available.
    """
    if config_path:
        return config_path
    config_file = get_setting("config_file")
    if not config_file:
        raise RuntimeError(
            "config_file not configured. "
            "Pass config_path= or call configure(config_file=...)."
        )
    return os.path.join(get_module_root(), config_file)


def _resolve_credentials_paths(
    creds_path: Optional[str] = None,
    key_path: Optional[str] = None,
) -> Tuple[str, str]:
    """Resolve credentials file and key file paths.

    Args:
        creds_path: Explicit credentials file path.
        key_path: Explicit vault key file path.

    Raises:
        RuntimeError: If neither param nor setting is available.
    """
    root = get_module_root()
    if not creds_path:
        creds_file = get_setting("credentials_file")
        if not creds_file:
            raise RuntimeError(
                "credentials_file not configured. "
                "Pass creds_path= or call configure(credentials_file=...)."
            )
        creds_path = os.path.join(root, creds_file)
    if not key_path:
        key_file = get_setting("credentials_key")
        if not key_file:
            raise RuntimeError(
                "credentials_key not configured. "
                "Pass key_path= or call configure(credentials_key=...)."
            )
        key_path = os.path.join(root, key_file)
    return creds_path, key_path


def load_test_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load test configuration from a YAML file.

    Args:
        config_path: Explicit file path.  When ``None``, resolved
                     from ``configure(config_file=...)``.

    Returns:
        Dict containing the configuration, or empty dict if not found.
    """
    path = _resolve_config_path(config_path)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


# =============================================================================
# VAULT ENCRYPTION
# =============================================================================

def _is_vault_encrypted(file_path: str) -> bool:
    """Check if file is ansible-vault encrypted."""
    if not os.path.exists(file_path):
        return False
    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()
    return first_line.startswith("$ANSIBLE_VAULT")


def _create_vault_key(key_path: str) -> None:
    """Create a new vault key file with random 32-char password."""
    import secrets
    key = secrets.token_urlsafe(32)[:32]
    with open(key_path, "w", encoding="utf-8") as f:
        f.write(key)
    os.chmod(key_path, 0o600)


def _decrypt_vault_file(config_path: str, key_path: str) -> Dict:
    """Decrypt ansible-vault encrypted file and return as dict."""
    try:
        result = subprocess.run(
            [
                "ansible-vault", "view", config_path,
                "--vault-password-file", key_path,
            ],
            capture_output=True, text=True, timeout=30, check=True,
        )
        return yaml.safe_load(result.stdout) or {}
    except subprocess.CalledProcessError as exc:
        raise ValueError(
            f"Failed to decrypt {config_path}: {exc.stderr}"
        ) from exc
    except FileNotFoundError:
        raise ValueError(
            "ansible-vault not found. Install ansible."
        ) from None


def _encrypt_vault_file(config_path: str, key_path: str) -> bool:
    """Encrypt file with ansible-vault."""
    try:
        subprocess.run(
            [
                "ansible-vault", "encrypt", config_path,
                "--vault-password-file", key_path,
            ],
            capture_output=True, text=True, timeout=30, check=True,
        )
        return True
    except subprocess.CalledProcessError as exc:
        raise ValueError(
            f"Failed to encrypt {config_path}: {exc.stderr}"
        ) from exc
    except FileNotFoundError:
        raise ValueError(
            "ansible-vault not found. Install ansible."
        ) from None


def load_test_credentials(
    creds_path: Optional[str] = None,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Load test credentials with automatic vault encryption.

    Args:
        creds_path: Explicit credentials file path.
        key_path: Explicit vault key file path.

    Behavior:
    - Encrypted + key exists: decrypt and return
    - Encrypted + key missing: raise error
    - Plain: read, create key, encrypt, return
    - Not found: return empty dict
    """
    creds_path, key_path = _resolve_credentials_paths(creds_path, key_path)

    if not os.path.exists(creds_path):
        return {}

    if _is_vault_encrypted(creds_path):
        if os.path.exists(key_path):
            return _decrypt_vault_file(creds_path, key_path)
        raise ValueError(
            f"Credentials encrypted but key not found: {key_path}"
        )

    with open(creds_path, "r", encoding="utf-8") as f:
        creds = yaml.safe_load(f) or {}

    if not os.path.exists(key_path):
        _create_vault_key(key_path)

    _encrypt_vault_file(creds_path, key_path)
    return creds


def encrypt_test_credentials(
    creds_path: Optional[str] = None,
    key_path: Optional[str] = None,
) -> bool:
    """Encrypt credentials file if not already encrypted.

    Args:
        creds_path: Explicit credentials file path.
        key_path: Explicit vault key file path.
    """
    creds_path, key_path = _resolve_credentials_paths(creds_path, key_path)

    if not os.path.exists(creds_path):
        return False
    if _is_vault_encrypted(creds_path):
        return True
    if not os.path.exists(key_path):
        _create_vault_key(key_path)

    _encrypt_vault_file(creds_path, key_path)
    return True


# =============================================================================
# LOCAL / REMOTE DETECTION
# =============================================================================

def _is_local_ip(ip: str) -> bool:
    """Check if IP belongs to this machine."""
    if ip in ("localhost", "127.0.0.1", ""):
        return True
    try:
        result = subprocess.run(
            ["hostname", "-I"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        return ip in result.stdout.strip().split()
    except (OSError, subprocess.SubprocessError):
        return False


def is_local_execution() -> bool:
    """Determine if tests run locally on the target host.

    Returns True when:
    - oim_server_ip is empty/not set
    - oim_server_ip matches a local IP address
    """
    config = load_test_config()
    oim_ip = config.get("oim_server_ip", "")
    if not oim_ip:
        return True
    return _is_local_ip(str(oim_ip).strip())


# =============================================================================
# TESTINFRA HOST CONNECTION
# =============================================================================

def get_testinfra_host():
    """Get testinfra host connected to the target server.

    When oim_server_ip is empty or local, runs in local mode.
    When oim_server_ip is remote, connects via SSH.

    Returns:
        testinfra Host object.
    """
    config = load_test_config()
    credentials = load_test_credentials()
    oim_ip = str(config.get("oim_server_ip", "")).strip()

    # Local execution
    if not oim_ip or _is_local_ip(oim_ip):
        return testinfra.get_host("local://")

    # Remote — SSH
    ssh_user = config["oim_ssh_user"]
    ssh_port = config.get("oim_ssh_port", 22)
    ssh_password = credentials.get("oim_password", "")

    inventory_dir = os.path.join(
        tempfile.gettempdir(), "omnia_auto_testinfra"
    )
    os.makedirs(inventory_dir, exist_ok=True)
    inventory_path = os.path.join(inventory_dir, "inventory.ini")

    ssh_args = get_setting(
        "ssh_opts",
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/dev/null "
        "-o LogLevel=ERROR",
    )

    with open(inventory_path, "w", encoding="utf-8") as f:
        f.write("[all]\n")
        f.write(
            f"target ansible_host={oim_ip} "
            f"ansible_user={ssh_user} "
            f"ansible_port={ssh_port} "
            f"ansible_ssh_pass={ssh_password} "
            f"ansible_connection=ssh "
            f"ansible_ssh_common_args='{ssh_args}'\n"
        )

    return testinfra.get_host(
        "ansible://target", ansible_inventory=inventory_path
    )


def run_on_host(host, cmd: str):
    """Run command on the target host (OIM server).

    Args:
        host: Testinfra host object
        cmd: Command to execute

    Returns:
        Result with stdout, stderr, rc attributes.
    """
    return host.run(cmd)


