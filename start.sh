#!/bin/bash
set -e

# Single-port production mode: backend serves the built React SPA on PORT.
PORT="${PORT:-49393}"
BACKEND_PORT="$PORT"
FRONTEND_PORT="$PORT"

# Start MongoDB if not already running
if ! docker ps | grep -q eudi-mongo; then
  echo "Starting MongoDB..."
  docker run -d --name eudi-mongo -p 27017:27017 mongo:latest >/dev/null 2>&1 || true
  sleep 3
else
  echo "MongoDB already running"
fi

# Generate a persistent MASTER_KEY for AES-256-GCM key wrapping (32 bytes → base64)
# If one already exists in .env, reuse it; otherwise generate a new one.
if [ -f backend/.env ] && grep -q "^MASTER_KEY=" backend/.env 2>/dev/null; then
  MASTER_KEY=$(grep "^MASTER_KEY=" backend/.env | cut -d= -f2- | tr -d '\r\n')
else
  MASTER_KEY=$(python3 -c "import base64,os; print(base64.b64encode(os.urandom(32)).decode())")
fi

# Write backend .env with the chosen port and MASTER_KEY
cat > backend/.env <<EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=eudi_nexus
ISSUER_URL=http://localhost:$BACKEND_PORT
MASTER_KEY=$MASTER_KEY
EOF

# Start backend
echo "Starting backend on port $BACKEND_PORT..."
cd backend
source venv/bin/activate
ISSUER_URL=http://localhost:$BACKEND_PORT MASTER_KEY=$MASTER_KEY python -m uvicorn server:app --host 0.0.0.0 --port $BACKEND_PORT --reload --log-level info &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "Waiting for backend..."
for i in $(seq 1 30); do
  if curl -sf -o /dev/null -w "%{http_code}" "http://localhost:$BACKEND_PORT/api/health" 2>/dev/null | grep -q "200"; then
    echo "Backend is ready (port $BACKEND_PORT)"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "ERROR: Backend failed to start after 30s"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
  fi
  sleep 1
done

# Build frontend (production) so the backend can serve it on the same origin
echo "Building frontend (production)..."
cd frontend
yarn build
cd ..

# Frontend is served by the backend from frontend/build/ (see server.py SPA mount).
# No separate dev server is started.
FRONTEND_PID=$BACKEND_PID

echo ""
echo "=========================================="
echo "Services started:"
echo "  Backend:  http://localhost:$BACKEND_PORT"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "  API:      http://localhost:$BACKEND_PORT/api"
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT TERM
wait
