#!/usr/bin/env bash
set -euo pipefail

readonly REPO_URL='https://github.com/Daniel-Brai/feedbase.git'
readonly TARGET_DIR='/opt/feedbase'
readonly BRANCH='main'

function print_banner() {
  cat <<'BANNER'
 ______            _ _                    
|  ____|          | | |                   
| |__ ___  ___  __| | |__   __ _ ___  ___ 
|  __/ _ \/ _ \/ _` | '_ \ / _` / __|/ _ \
| | |  __/  __/ (_| | |_) | (_| \__ \  __/
|_|  \___|\___|\__,_|_.__/ \__,_|___/\___|
                                          
BANNER
}

function require_root() {
  if [[ "$EUID" -ne 0 ]]; then
    echo "This installer must be run as root."
    echo "Use sudo ./install.sh or run as root."
    exit 1
  fi
}

function check_dependencies() {
  if uname | grep -Eq 'MINGW|MSYS|CYGWIN|NT-|Windows'; then
    echo "Windows is not supported by this installer."
    exit 1
  fi

  if uname | grep -Eq '^Darwin'; then
    echo "macOS is not supported by this installer."
    exit 1
  fi

  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required but not installed. Please install Docker and try again."
    exit 1
  fi

  if ! docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
    echo "Docker Compose is required but not installed. Please install Docker Compose and try again."
    exit 1
  fi

  if ! command -v git >/dev/null 2>&1; then
    echo "Git is required but not installed. Please install Git and try again."
    exit 1
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
  fi
}

function validate_password() {
  local password="$1"

  if [[ ${#password} -lt 8 ]]; then
    return 1
  fi
  if ! [[ $password =~ [A-Z] ]]; then
    return 1
  fi
  if ! [[ $password =~ [a-z] ]]; then
    return 1
  fi
  if ! [[ $password =~ [0-9] ]]; then
    return 1
  fi
  if ! [[ $password =~ [^[:alnum:]] ]]; then
    return 1
  fi

  return 0
}

function read_password() {
  local password confirm

  while true; do
    read -rsp "Superuser password: " password
    echo
    read -rsp "Confirm password: " confirm
    echo

    if [[ "$password" != "$confirm" ]]; then
      echo "Passwords do not match. Please try again."
      continue
    fi

    if ! validate_password "$password"; then
      echo "Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character."
      continue
    fi

    echo "$password"
    return 0
  done
}

function prompt_default_env() {
  local answer
  while true; do
    read -rp "Use default .env from .env.template? (y/n): " answer
    case "$answer" in
      [Yy]*) return 0 ;; 
      [Nn]*) return 1 ;; 
      *) echo "Please answer y or n." ;; 
    esac
  done
}

function clone_or_update_repo() {
  if [[ -d "$TARGET_DIR/.git" ]]; then
    echo "Updating existing Feedbase checkout in $TARGET_DIR"
    git -C "$TARGET_DIR" fetch --all --prune
    git -C "$TARGET_DIR" checkout "$BRANCH"
    git -C "$TARGET_DIR" pull --ff-only origin "$BRANCH"
    return
  fi

  if [[ -e "$TARGET_DIR" ]] && [[ ! -z "$(ls -A "$TARGET_DIR")" ]]; then
    local answer
    while true; do
      read -rp "Target $TARGET_DIR exists and is not a git checkout. Remove it and clone fresh? (y/n): " answer
      case "$answer" in
        [Yy]*) rm -rf "$TARGET_DIR"; break ;; 
        [Nn]*) echo "Installation cancelled."; exit 1 ;; 
        *) echo "Please answer y or n." ;; 
      esac
    done
  fi

  echo "Cloning Feedbase from $REPO_URL into $TARGET_DIR"
  mkdir -p "$TARGET_DIR"
  git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TARGET_DIR"
}

function create_env_file() {
  local use_default="$1"
  local template_path="$TARGET_DIR/.env.template"
  local env_path="$TARGET_DIR/.env"

  if [[ ! -f "$template_path" ]]; then
    echo "Missing $template_path. Cannot create .env file."
    exit 1
  fi

  if [[ "$use_default" == true ]]; then
    cp "$template_path" "$env_path"
    return
  fi

  local superuser_name superuser_email superuser_password openapi_username openapi_password

  read -rp "Superuser name [Administrator]: " superuser_name
  superuser_name=${superuser_name:-Administrator}

  while true; do
    read -rp "Superuser email [admin@feedbase.app]: " superuser_email
    superuser_email=${superuser_email:-admin@feedbase.app}
    if [[ "$superuser_email" =~ ^[^@]+@[^@]+\.[^@]+$ ]]; then
      break
    fi
    echo "Please enter a valid email address."
  done

  superuser_password=$(read_password)

  read -rp "OpenAPI username [Administrator]: " openapi_username
  openapi_username=${openapi_username:-Administrator}

  read -rsp "OpenAPI password [AdminPassword@123]: " openapi_password
  echo
  openapi_password=${openapi_password:-Password@123}

  python3 <<PYTHON
from pathlib import Path
replacements = {
    'APP_SUPERUSER_NAME': "$superuser_name",
    'APP_SUPERUSER_EMAIL': "$superuser_email",
    'APP_SUPERUSER_PASSWORD': "$superuser_password",
    'OPENAPI_USERNAME': "$openapi_username",
    'OPENAPI_PASSWORD': "$openapi_password",
}
text = Path(r'''$template_path''').read_text()
lines = []
for raw in text.splitlines():
    if raw.strip().startswith('#') or '=' not in raw:
        lines.append(raw)
        continue
    key, rest = raw.split('=', 1)
    if key in replacements:
        lines.append(f"{key}={replacements[key]}")
    else:
        lines.append(raw)
Path(r'''$env_path''').write_text('\n'.join(lines) + '\n')
PYTHON
}

function install_service() {
  local service_file="$TARGET_DIR/infra/systemd/feedbase.service"

  if [[ ! -f "$service_file" ]]; then
    echo "Missing $service_file. Cannot install service."
    exit 1
  fi

  install -Dm644 "$service_file" /etc/systemd/system/feedbase.service
  systemctl daemon-reload
  systemctl enable --now feedbase.service
}

print_banner
require_root
check_dependencies
clone_or_update_repo

if [[ -f "$TARGET_DIR/.env" ]]; then
  read -rp "$TARGET_DIR/.env already exists. Overwrite it? (y/n): " overwrite
  case "$overwrite" in
    [Yy]*) true ;; 
    *) echo "Installation cancelled."; exit 0 ;; 
  esac
fi

if prompt_default_env; then
  create_env_file true
else
  create_env_file false
fi

install_service

echo "Feedbase installation complete. The service is enabled and started."
