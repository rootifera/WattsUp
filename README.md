# WattsUp

WattsUp is a modern, self-hosted management interface for
[Network UPS Tools (NUT)](https://networkupstools.org/). It provides live UPS monitoring,
historical collection, dynamically discovered UPS controls, and guarded shutdown automation for
remote Linux devices.

WattsUp connects directly to `upsd` over TCP. It does not access USB devices, require privileged
containers, or invoke `upsc`/`upscmd` subprocesses.

## Features

- Responsive dark dashboard with five-second live updates
- Automatic discovery and selection of multiple UPS units on one NUT server
- Human-readable NUT status messages and dynamic state headlines
- Battery, runtime, load, voltage, device, firmware, and driver information
- Automatic hiding of optional metrics not supported by a UPS
- SQLite historical readings collected every 30 seconds
- Dynamically discovered instant commands with descriptions
- Grouped battery, beeper, panel, driver, and power controls
- Typed confirmation for dangerous UPS commands
- Single-administrator JWT authentication
- Persistent remote-device shutdown rules
- Ed25519 SSH key generation and host-key approval
- Per-device SSH readiness tests
- Global automation disable switch and dry-run mode
- Safe condition simulation without executing SSH commands
- Automatic remote Linux shutdown with restricted passwordless sudo

## Requirements

- A running NUT server reachable over TCP, normally on port `3493`
- Docker with Docker Compose
- For UPS command execution, a NUT account authorized to run instant commands
- For remote shutdown, Linux devices with an SSH server

The NUT server must listen on an address reachable from the WattsUp container. A listener bound
only to `127.0.0.1` cannot be reached from Docker.

## Run with Docker

Copy the example configuration:

```shell
cp .env.example .env
```

Edit `.env`:

```env
NUT_HOST=192.168.1.5
NUT_PORT=3493
UPS_NAME=ups
NUT_USERNAME=
NUT_PASSWORD=
NUT_TIMEOUT_SECONDS=5
POLL_INTERVAL_SECONDS=30

ADMIN_USERNAME=admin
ADMIN_PASSWORD=replace-with-a-long-random-password
JWT_SECRET=replace-with-at-least-32-random-characters

DATABASE_URL=sqlite+aiosqlite:////data/wattsup.db
SSH_KEY_PATH=/data/ssh/id_ed25519
```

Use unique production values for `ADMIN_PASSWORD` and `JWT_SECRET`. Keep `.env` private.
`UPS_NAME` is the default and migration fallback; WattsUp discovers every UPS exposed by the
configured NUT server and lets the administrator switch between them in the Web UI.

Build and start WattsUp:

```shell
docker compose up -d --build
```

Open <http://localhost:8000>. API documentation is available at
<http://localhost:8000/api/docs>.

The container runs as an unprivileged user with Linux capabilities removed. SQLite data and the
generated SSH keypair are stored in the `wattsup-data` Docker volume.

## Authentication

Sign in with `ADMIN_USERNAME` and `ADMIN_PASSWORD`. Successful login issues a bearer token with a
12-hour lifetime by default.

All API endpoints except the following require authentication:

- `GET /api/health`
- `POST /api/auth/login`
- `GET /adduser.sh`

`/adduser.sh` is intentionally public so a new remote device can install WattsUp's public key. It
does not expose the private key, administrator password, JWT secret, or NUT credentials.

## Dashboard

The dashboard refreshes every five seconds and presents live data in one consolidated power panel.
When NUT exposes multiple UPS units, the selector in the header switches the entire interface to
the chosen UPS without changing the page layout. The selection is remembered in the browser.
NUT status codes are translated into readable states such as:

- Online
- Online · Charging
- Online · Battery full
- On battery
- Low battery
- Replace battery
- Discharging
- Overloaded
- Power restored

The headline changes with the current state. After an on-battery incident, WattsUp shows a
temporary power-restored message for five minutes.

Optional values such as output voltage or frequency remain visible during discovery and are hidden
after ten consecutive successful polls return no value. They reappear automatically if the UPS
begins reporting them.

The UPS details section exposes all variables returned by NUT using human-readable labels. Hover
over a label to see its original NUT variable name.

## UPS controls

WattsUp discovers supported instant commands directly from NUT instead of assuming a particular
UPS model. Commands are grouped into:

- Battery tests
- Beeper controls
- Panel tests
- Driver actions
- Dangerous power actions

Routine commands require confirmation. Dangerous commands require the exact command name to be
typed before execution. Obsolete beeper aliases are hidden when current alternatives are available.

UPS commands require valid `NUT_USERNAME` and `NUT_PASSWORD` credentials with suitable permissions
on the NUT server.

## Shutdown automation

Shutdown Automation manages independent rules for remote Linux devices. Each device can configure:

- The UPS whose state controls the rule
- Friendly name
- Hostname or IP address
- SSH port and username
- Enabled/disabled state
- Passwordless sudo use
- Required mains state: online, on battery, or any
- Required battery state: charging, discharging, full, or any
- Battery percentage threshold
- An approved SSH host-key fingerprint

A device is evaluated only against its assigned UPS. A rule matches when all selected conditions
are true. The recommended default is:

```text
On battery AND Discharging AND Battery <= configured percentage
```

### Safety model

New installations default to:

```text
Automation enabled: false
Dry-run mode: true
```

Additional protections:

- Devices are disabled unless explicitly enabled.
- SSH host keys require approval in the Web UI.
- A changed host key blocks command execution.
- Readiness tests verify SSH and required passwordless sudo permissions.
- The simulator evaluates conditions without running SSH.
- A matching device triggers only once during a continuous incident.
- A device becomes eligible again only after its rule stops matching.
- Global automation can be disabled immediately.

When a real shutdown is permitted, WattsUp tries these Linux commands in order:

```text
sudo -n /usr/bin/systemctl poweroff
sudo -n /usr/sbin/shutdown -h now
sudo -n /usr/sbin/poweroff
```

It stops after a command is accepted or the SSH connection closes.

### Set up a remote device

Expand **Remote device setup** in the Shutdown Automation tab. It provides WattsUp's public key,
a complete setup script, and a command based on the URL used to access WattsUp:

```shell
curl -fsSL https://wattsup.example.com/adduser.sh | sudo bash
```

The script:

- Creates a dedicated `wattsup` Linux user if needed
- Installs the generated Ed25519 public key
- Applies correct SSH directory and file permissions
- Installs a narrowly scoped rule in `/etc/sudoers.d/wattsup`
- Validates the sudoers rule before installation
- Is safe to run repeatedly

After running it:

1. Add the device in WattsUp with username `wattsup`.
2. Inspect and approve its SSH host-key fingerprint.
3. Run **Test readiness**.
4. Enable the device rule when its conditions are correct.
5. Use simulation and dry-run mode before enabling real automation.

## Reverse proxy

WattsUp works behind a reverse proxy such as BunkerWeb, Caddy, Traefik, or NGINX. Proxy the domain
root to port `8000` without changing request paths. The following paths must all reach WattsUp:

```text
/
/api/*
/assets/*
/adduser.sh
```

The setup command uses the browser's current origin. Opening WattsUp through
`https://wattsup.example.com` therefore generates:

```shell
curl -fsSL https://wattsup.example.com/adduser.sh | sudo bash
```

If the reverse proxy adds another authentication layer, exempt `/adduser.sh` or the remote device
will download an authentication page instead of the shell script. TLS is strongly recommended.

When BunkerWeb and WattsUp are containers on a shared Docker network, use the WattsUp service name
as the upstream:

```text
REVERSE_PROXY_URL=/
REVERSE_PROXY_HOST=http://wattsup:8000
```

Do not use `localhost:8000` as the upstream from another container.

## API

Core endpoints:

```text
GET    /api/health
POST   /api/auth/login
GET    /api/ups
GET    /api/status
GET    /api/history
GET    /api/variables
GET    /api/commands
POST   /api/command/{name}
```

Shutdown automation endpoints:

```text
GET    /api/shutdown/public-key
GET    /api/shutdown/settings
PUT    /api/shutdown/settings
GET    /api/shutdown/devices
POST   /api/shutdown/devices
PUT    /api/shutdown/devices/{id}
DELETE /api/shutdown/devices/{id}
GET    /api/shutdown/devices/{id}/host-key
POST   /api/shutdown/devices/{id}/trust-host-key
POST   /api/shutdown/devices/{id}/test
POST   /api/shutdown/simulate
GET    /adduser.sh
```

Interactive OpenAPI documentation is served at `/api/docs`.

## Local development

Create `.env` at the repository root, then install the backend:

```shell
python3.13 -m venv .venv
. .venv/bin/activate
pip install -e "backend[dev]"
uvicorn wattsup.main:app --reload
```

In a second terminal:

```shell
cd frontend
npm install
npm run dev
```

Vite serves the UI at <http://localhost:5173> and proxies `/api` requests to port `8000`.

For local development, set writable paths in `.env`:

```env
DATABASE_URL=sqlite+aiosqlite:///./data/wattsup.db
SSH_KEY_PATH=./data/ssh/id_ed25519
```

## Quality checks

Backend:

```shell
.venv/bin/ruff check backend
.venv/bin/black --check backend
.venv/bin/mypy backend/src
.venv/bin/pytest backend
```

Frontend:

```shell
cd frontend
npm run lint
npm run format
npm run build
npm audit
```

## License

WattsUp is licensed under the GNU General Public License v2. See [LICENSE](LICENSE).
