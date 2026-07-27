# WattsUp

WattsUp is a modern, self-hosted management interface for
[Network UPS Tools](https://networkupstools.org/). It connects to `upsd` over TCP; it does not
access USB devices or invoke NUT command-line tools.

## Run with Docker

Copy the example environment and set your NUT server:

```shell
cp .env.example .env
docker compose up --build
```

Open <http://localhost:8000>. API documentation is available at
<http://localhost:8000/api/docs>.

Sign in with the administrator credentials configured by `ADMIN_USERNAME` and
`ADMIN_PASSWORD`. Keep `.env` private and set a unique `JWT_SECRET`.

## Local development

Backend:

```shell
python3.13 -m venv .venv
. .venv/bin/activate
pip install -e "backend[dev]"
uvicorn wattsup.main:app --reload
```

Frontend (in a second terminal):

```shell
cd frontend
npm install
npm run dev
```

Vite serves the UI at <http://localhost:5173> and proxies API requests to port 8000.

## Current API

- `GET /api/health`
- `GET /api/status`
- `GET /api/history?hours=24`
- `GET /api/variables`
- `GET /api/commands`
- `POST /api/command/{name}` with `{"confirmed": true}` for dangerous commands

All endpoints except `/api/health` and `/api/auth/login` require a bearer token.
