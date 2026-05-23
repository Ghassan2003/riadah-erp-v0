#!/bin/bash
# RIADAH ERP - Start Frontend (Local Development)
cd "$(dirname "$0")/frontend"
npx vite --host 0.0.0.0 --port 5173
