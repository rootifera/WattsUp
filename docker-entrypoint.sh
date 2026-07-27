#!/bin/sh
set -eu

exec uvicorn wattsup.main:app --host 0.0.0.0 --port 8000

