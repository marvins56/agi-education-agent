#!/usr/bin/env bash
# EduAGI Development Script — start, stop, logs for all services
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$PROJECT_DIR/.venv"
PID_DIR="$PROJECT_DIR/.pids"
LOG_DIR="$PROJECT_DIR/.logs"

mkdir -p "$PID_DIR" "$LOG_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[eduagi]${NC} $*"; }
warn() { echo -e "${YELLOW}[eduagi]${NC} $*"; }
err()  { echo -e "${RED}[eduagi]${NC} $*" >&2; }

# ---------- helpers ----------

is_running() {
    local pidfile="$PID_DIR/$1.pid"
    if [[ -f "$pidfile" ]]; then
        local pid
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
        rm -f "$pidfile"
    fi
    return 1
}

wait_for_port() {
    local port=$1 name=$2 tries=30
    while ! ss -tlnp 2>/dev/null | grep -q ":${port} " && (( tries-- > 0 )); do
        sleep 1
    done
    if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
        log "$name ready on port $port"
    else
        warn "$name may not be ready yet on port $port"
    fi
}

# ---------- start ----------

start_infra() {
    log "Starting infrastructure (Postgres, Redis, ChromaDB)..."
    docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d
    wait_for_port 5433 "PostgreSQL"
    wait_for_port 6380 "Redis"
    wait_for_port 8100 "ChromaDB"
}

start_backend() {
    if is_running backend; then
        warn "Backend already running (PID $(cat "$PID_DIR/backend.pid"))"
        return
    fi
    log "Starting backend (FastAPI on :8000)..."
    source "$VENV/bin/activate"
    cd "$PROJECT_DIR"
    nohup python -m uvicorn src.api.main:app \
        --host 0.0.0.0 --port 8000 --reload \
        > "$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$PID_DIR/backend.pid"
    wait_for_port 8000 "Backend"
}

start_frontend() {
    if is_running frontend; then
        warn "Frontend already running (PID $(cat "$PID_DIR/frontend.pid"))"
        return
    fi
    log "Starting frontend (Next.js on :3000)..."
    cd "$PROJECT_DIR/frontend"
    nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$PID_DIR/frontend.pid"
    wait_for_port 3000 "Frontend"
}

cmd_start() {
    local target="${1:-all}"
    case "$target" in
        infra)    start_infra ;;
        backend)  start_backend ;;
        frontend) start_frontend ;;
        all)
            start_infra
            start_backend
            start_frontend
            echo ""
            log "All services running:"
            echo -e "  ${CYAN}Backend${NC}   http://localhost:8000  (API docs: http://localhost:8000/docs)"
            echo -e "  ${CYAN}Frontend${NC}  http://localhost:3000"
            echo -e "  ${CYAN}Postgres${NC}  localhost:5433"
            echo -e "  ${CYAN}Redis${NC}     localhost:6380"
            echo -e "  ${CYAN}ChromaDB${NC}  localhost:8100"
            echo ""
            log "Logs:  $0 logs [backend|frontend|all]"
            log "Stop:  $0 stop"
            ;;
        *) err "Unknown target: $target (use: all, infra, backend, frontend)"; exit 1 ;;
    esac
}

# ---------- stop ----------

stop_service() {
    local name=$1
    if is_running "$name"; then
        local pid
        pid=$(cat "$PID_DIR/$name.pid")
        log "Stopping $name (PID $pid)..."
        kill "$pid" 2>/dev/null || true
        # Also kill child processes (e.g. uvicorn workers)
        pkill -P "$pid" 2>/dev/null || true
        rm -f "$PID_DIR/$name.pid"
    else
        warn "$name is not running"
    fi
}

cmd_stop() {
    local target="${1:-all}"
    case "$target" in
        infra)
            log "Stopping infrastructure..."
            docker compose -f "$PROJECT_DIR/docker-compose.yml" down
            ;;
        backend)  stop_service backend ;;
        frontend) stop_service frontend ;;
        all)
            stop_service frontend
            stop_service backend
            log "Stopping infrastructure..."
            docker compose -f "$PROJECT_DIR/docker-compose.yml" down
            log "All services stopped."
            ;;
        *) err "Unknown target: $target"; exit 1 ;;
    esac
}

# ---------- logs ----------

cmd_logs() {
    local target="${1:-all}"
    case "$target" in
        backend)
            if [[ -f "$LOG_DIR/backend.log" ]]; then
                tail -f "$LOG_DIR/backend.log"
            else
                err "No backend log found"
            fi
            ;;
        frontend)
            if [[ -f "$LOG_DIR/frontend.log" ]]; then
                tail -f "$LOG_DIR/frontend.log"
            else
                err "No frontend log found"
            fi
            ;;
        infra)
            docker compose -f "$PROJECT_DIR/docker-compose.yml" logs -f
            ;;
        all)
            log "Tailing all logs (Ctrl+C to stop)..."
            tail -f "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log" 2>/dev/null
            ;;
        *) err "Unknown target: $target"; exit 1 ;;
    esac
}

# ---------- status ----------

cmd_status() {
    echo -e "${CYAN}Service Status${NC}"
    echo "────────────────────────────────"

    # Backend
    if is_running backend; then
        echo -e "  Backend    ${GREEN}running${NC}  (PID $(cat "$PID_DIR/backend.pid")) :8000"
    else
        echo -e "  Backend    ${RED}stopped${NC}"
    fi

    # Frontend
    if is_running frontend; then
        echo -e "  Frontend   ${GREEN}running${NC}  (PID $(cat "$PID_DIR/frontend.pid")) :3000"
    else
        echo -e "  Frontend   ${RED}stopped${NC}"
    fi

    # Docker services
    for svc in eduagi-postgres eduagi-redis eduagi-chroma; do
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${svc}$"; then
            echo -e "  ${svc}  ${GREEN}running${NC}"
        else
            echo -e "  ${svc}  ${RED}stopped${NC}"
        fi
    done
}

# ---------- restart ----------

cmd_restart() {
    local target="${1:-all}"
    cmd_stop "$target"
    sleep 1
    cmd_start "$target"
}

# ---------- main ----------

usage() {
    echo "Usage: $0 <command> [target]"
    echo ""
    echo "Commands:"
    echo "  start   [all|infra|backend|frontend]   Start services (default: all)"
    echo "  stop    [all|infra|backend|frontend]   Stop services (default: all)"
    echo "  restart [all|infra|backend|frontend]   Restart services (default: all)"
    echo "  logs    [all|backend|frontend|infra]   Tail logs (default: all)"
    echo "  status                                 Show service status"
    echo ""
    echo "Examples:"
    echo "  $0 start           # Start everything"
    echo "  $0 logs backend    # Tail backend logs"
    echo "  $0 stop frontend   # Stop only the frontend"
    echo "  $0 restart backend # Restart the backend"
    echo "  $0 status          # Check what's running"
}

cmd="${1:-}"
shift || true

case "$cmd" in
    start)   cmd_start "$@" ;;
    stop)    cmd_stop "$@" ;;
    restart) cmd_restart "$@" ;;
    logs)    cmd_logs "$@" ;;
    status)  cmd_status ;;
    help|-h|--help) usage ;;
    "")      usage; exit 1 ;;
    *)       err "Unknown command: $cmd"; usage; exit 1 ;;
esac
