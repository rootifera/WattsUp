#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY="${WATTSUP_REPOSITORY:-https://github.com/rootifera/WattsUp.git}"
BRANCH="${WATTSUP_BRANCH:-main}"
INSTALL_DIR="${WATTSUP_DIR:-/opt/wattsup}"
ENV_FILE="${INSTALL_DIR}/.env"

log() {
  printf 'WattsUp: %s\n' "$*"
}

fail() {
  printf 'WattsUp: error: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

random_secret() {
  openssl rand -hex "$1"
}

ensure_setting() {
  local name="$1"
  local value="$2"
  if ! grep -qE "^${name}=" "${ENV_FILE}"; then
    printf '%s=%s\n' "${name}" "${value}" >> "${ENV_FILE}"
  fi
}

require_command git
require_command docker
require_command openssl
docker compose version >/dev/null 2>&1 ||
  fail "Docker Compose v2 is required (the 'docker compose' command)"

fresh_install=false
created_config=false
if [[ -d "${INSTALL_DIR}/.git" ]]; then
  log "existing installation found in ${INSTALL_DIR}"
  cd "${INSTALL_DIR}"
  if [[ -n "$(git status --porcelain)" ]]; then
    fail "the installation has local source changes; commit or remove them before updating"
  fi
  log "fetching ${BRANCH}"
  git fetch --prune origin "${BRANCH}"
  git checkout "${BRANCH}"
  git merge --ff-only "origin/${BRANCH}"
elif [[ -e "${INSTALL_DIR}" && -n "$(find "${INSTALL_DIR}" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  fail "${INSTALL_DIR} exists and is not an empty WattsUp checkout"
else
  fresh_install=true
  log "cloning WattsUp into ${INSTALL_DIR}"
  mkdir -p "$(dirname "${INSTALL_DIR}")"
  git clone --branch "${BRANCH}" --single-branch "${REPOSITORY}" "${INSTALL_DIR}"
  cd "${INSTALL_DIR}"
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  created_config=true
  log "creating private configuration"
  umask 077
  cat > "${ENV_FILE}" <<EOF
POLL_INTERVAL_SECONDS=30
WEB_PORT=8000
DATABASE_PASSWORD=$(random_secret 24)
JWT_SECRET=$(random_secret 32)
SETUP_TOKEN=$(random_secret 24)
EOF
else
  chmod 600 "${ENV_FILE}"
  ensure_setting "POLL_INTERVAL_SECONDS" "30"
  ensure_setting "WEB_PORT" "8000"
  ensure_setting "DATABASE_PASSWORD" "$(random_secret 24)"
  ensure_setting "JWT_SECRET" "$(random_secret 32)"
  ensure_setting "SETUP_TOKEN" "$(random_secret 24)"
fi

log "pulling service images"
docker compose pull postgres
log "building and starting WattsUp"
docker compose up -d --build --remove-orphans --wait

web_port="$(sed -n 's/^WEB_PORT=//p' "${ENV_FILE}" | tail -n 1)"
web_port="${web_port:-8000}"

log "deployment is healthy"
printf '\nOpen: http://localhost:%s\n' "${web_port}"
if [[ "${fresh_install}" == true || "${created_config}" == true ]]; then
  setup_token="$(sed -n 's/^SETUP_TOKEN=//p' "${ENV_FILE}" | tail -n 1)"
  printf 'Setup token: %s\n' "${setup_token}"
  printf 'The token is also stored in %s.\n' "${ENV_FILE}"
else
  printf 'Configuration and Docker volumes were preserved.\n'
fi
