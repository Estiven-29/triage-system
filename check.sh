#!/usr/bin/env bash
# Verificacion local: corre los mismos chequeos que .github/workflows/ci.yml
# (lint + tests del backend, tests + build del frontend) sin depender de
# GitHub Actions. Ejecutalo antes de cada commit o PR:
#
#   ./check.sh             # backend + frontend
#   ./check.sh backend     # solo backend
#   ./check.sh frontend    # solo frontend
#
# Para probar tambien contra PostgreSQL (como el job backend-postgres),
# exporta TEST_DATABASE_URL apuntando a una BD DESECHABLE: el script borra
# todas sus tablas. Nunca uses la BD de docker compose ni una con datos.
#   docker run --rm -d --name triage-pg-test -p 55432:5432 \
#     -e POSTGRES_PASSWORD=test -e POSTGRES_DB=triage_test postgres:16-alpine
#   TEST_DATABASE_URL=postgresql://postgres:test@localhost:55432/triage_test ./check.sh backend
#   docker stop triage-pg-test
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-all}"

step() { printf '\n\033[1;34m==> %s\033[0m\n' "$1"; }

check_backend() {
  cd "$ROOT/backend"
  step "Backend: lint (ruff)"
  ruff check .
  if [ -n "${TEST_DATABASE_URL:-}" ]; then
    # Ida y vuelta de migraciones; termina en "base" para que los tests de
    # API de abajo arranquen sobre una BD vacia.
    step "Backend: migraciones ida y vuelta en la BD de TEST_DATABASE_URL"
    DATABASE_URL="$TEST_DATABASE_URL" python -m alembic upgrade head
    DATABASE_URL="$TEST_DATABASE_URL" python -m alembic downgrade base
    DATABASE_URL="$TEST_DATABASE_URL" python -m alembic upgrade head
    DATABASE_URL="$TEST_DATABASE_URL" python -m alembic check
    DATABASE_URL="$TEST_DATABASE_URL" python -m alembic downgrade base
  fi
  # Sin TEST_DATABASE_URL los tests usan SQLite; con ella, tests/test_api.py
  # corre contra esa BD.
  step "Backend: tests (pytest)"
  python -m pytest -q
}

check_frontend() {
  cd "$ROOT/frontend"
  if [ ! -d node_modules ]; then
    step "Frontend: instalando dependencias (npm ci)"
    npm ci
  fi
  step "Frontend: tests (Jest)"
  CI=true npx craco test --watchAll=false
  step "Frontend: build de produccion"
  CI=true npm run build
}

case "$TARGET" in
  backend) check_backend ;;
  frontend) check_frontend ;;
  all) check_backend; check_frontend ;;
  *) echo "Uso: $0 [backend|frontend|all]" >&2; exit 2 ;;
esac

printf '\n\033[1;32m✓ Todos los chequeos pasaron\033[0m\n'
