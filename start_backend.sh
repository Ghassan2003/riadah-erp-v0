#!/bin/bash
# RIADAH ERP - Start Script (Local Development)
cd "$(dirname "$0")/backend"
export DJANGO_SECRET_KEY=riadah-erp-local-dev-secret-key-2024
export DEBUG=True
export SECURE_SSL_REDIRECT=False
export SECURE_HSTS_SECONDS=0
/home/z/my-project/.venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload
