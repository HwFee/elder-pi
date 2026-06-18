#!/usr/bin/env bash
set -euo pipefail
cd signaling-server
SECRET_KEY=test-secret python -m pytest tests/ -v
