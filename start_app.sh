#!/bin/bash
source ./.venv/bin/activate
exec gunicorn --workers 3 --bind 127.0.0.1:8000 --worker-class eventlet -m 007 wsgi:app
