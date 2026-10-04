#!/usr/bin/env bash
set -e

echo "🚀 Starting TravelMate environment with real-time decryption..."

# 1. Start Docker Compose using real-time dotenvx
echo "🔓 Decrypting environment variables in memory..."
echo "🐳 Starting Docker containers (API, Web, Admin, Redis)..."
if command -v dotenvx >/dev/null 2>&1; then
    dotenvx run -f .env -- docker compose -f docker-compose.dev.yml up -d
else
    echo "⚠️  'dotenvx' CLI not found. Please install it."
    exit 1
fi

echo "⏳ Waiting 5 seconds for Vite servers to initialize..."
sleep 5

# 2. Open User Interfaces in the default browser
echo "🌐 Opening User Interfaces..."
if command -v xdg-open >/dev/null; then
    xdg-open "http://localhost:5173" >/dev/null 2>&1 &
    xdg-open "http://localhost:4173" >/dev/null 2>&1 &
    xdg-open "http://localhost:8000/docs" >/dev/null 2>&1 &
elif command -v open >/dev/null; then
    open "http://localhost:5173"
    open "http://localhost:4173"
    open "http://localhost:8000/docs"
else
    echo "Could not detect automatic browser opener."
fi

echo ""
echo "✅ TravelMate is running successfully!"
echo "---------------------------------------------------"
echo "👉 Web App (User):    http://localhost:5173"
echo "👉 Admin Dashboard:   http://localhost:4173"
echo "👉 API Swagger Docs:  http://localhost:8000/docs"
echo "---------------------------------------------------"
echo "Stop the servers anytime by running: docker compose -f docker-compose.dev.yml down"
echo "View live logs by running:           docker compose -f docker-compose.dev.yml logs -f"
