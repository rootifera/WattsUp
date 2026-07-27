import asyncio
import os
from pathlib import Path

import asyncssh


class SshService:
    def __init__(self, key_path: Path) -> None:
        self.key_path = key_path

    def ensure_key(self) -> None:
        if self.key_path.exists():
            return
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        key = asyncssh.generate_private_key("ssh-ed25519")
        self.key_path.write_bytes(key.export_private_key())
        os.chmod(self.key_path, 0o600)
        self.key_path.with_suffix(".pub").write_bytes(key.export_public_key())

    def public_key(self) -> str:
        self.ensure_key()
        return self.key_path.with_suffix(".pub").read_text().strip()

    def setup_script(self) -> str:
        public_key = self.public_key()
        sudoers_rule = (
            "wattsup ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff, "
            "/usr/sbin/shutdown, /usr/sbin/poweroff"
        )
        return f"""#!/usr/bin/env bash
set -euo pipefail

if [[ "${{EUID}}" -ne 0 ]]; then
  echo "Run as root: curl -fsSL <wattsup-url>/adduser.sh | sudo bash" >&2
  exit 1
fi

WATTSUP_USER="wattsup"
PUBLIC_KEY='{public_key}'
AUTHORIZED_KEYS="/home/${{WATTSUP_USER}}/.ssh/authorized_keys"

if ! id "${{WATTSUP_USER}}" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "${{WATTSUP_USER}}"
fi

install -d -m 700 -o "${{WATTSUP_USER}}" -g "${{WATTSUP_USER}}" "/home/${{WATTSUP_USER}}/.ssh"
touch "${{AUTHORIZED_KEYS}}"
if ! grep -qxF "${{PUBLIC_KEY}}" "${{AUTHORIZED_KEYS}}"; then
  printf '%s\\n' "${{PUBLIC_KEY}}" >> "${{AUTHORIZED_KEYS}}"
fi
chown "${{WATTSUP_USER}}:${{WATTSUP_USER}}" "${{AUTHORIZED_KEYS}}"
chmod 600 "${{AUTHORIZED_KEYS}}"

TEMP_SUDOERS="$(mktemp)"
trap 'rm -f "${{TEMP_SUDOERS}}"' EXIT
printf '%s\\n' '{sudoers_rule}' > "${{TEMP_SUDOERS}}"
chmod 440 "${{TEMP_SUDOERS}}"
visudo -cf "${{TEMP_SUDOERS}}"
install -m 440 "${{TEMP_SUDOERS}}" /etc/sudoers.d/wattsup

echo "WattsUp SSH access configured successfully."
"""

    async def inspect_host_key(self, host: str, port: int) -> tuple[str, str, str]:
        key = await asyncio.wait_for(asyncssh.get_server_host_key(host, port), timeout=10)
        if key is None:
            raise ConnectionError("SSH server did not present a host key")
        return (
            key.get_algorithm(),
            key.get_fingerprint("sha256"),
            key.export_public_key().decode().strip(),
        )

    async def run(
        self,
        *,
        host: str,
        port: int,
        username: str,
        trusted_host_key: str,
        command: str,
        timeout_seconds: int = 15,
    ) -> tuple[int, str]:
        self.ensure_key()
        async with asyncssh.connect(
            host,
            port=port,
            username=username,
            client_keys=[str(self.key_path)],
            known_hosts=None,
            connect_timeout=timeout_seconds,
        ) as connection:
            server_key = connection.get_server_host_key()
            if server_key is None:
                raise ConnectionError("SSH server did not present a host key")
            actual = server_key.export_public_key().decode().strip()
            if actual != trusted_host_key.strip():
                raise ValueError("SSH host key changed; approve the new key before connecting")
            result = await asyncio.wait_for(
                connection.run(command, check=False), timeout=timeout_seconds
            )
            raw_output = result.stdout or result.stderr or ""
            output = (
                raw_output.decode(errors="replace") if isinstance(raw_output, bytes) else raw_output
            ).strip()
            return result.exit_status if result.exit_status is not None else 255, output
