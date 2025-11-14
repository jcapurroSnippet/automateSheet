#!/bin/sh
set -e

# If secrets are injected as env vars, write them to the files the app expects.
# If the files already exist in the image (because you committed them), we keep them
# unless the corresponding env var is set (env var overrides image contents).

APP_DIR=/app
CRED_FILE="$APP_DIR/credentials.json"
TOKEN_FILE="$APP_DIR/token.json"

if [ -n "$CLIENT_SECRETS" ]; then
  echo "Writing CLIENT_SECRETS to $CRED_FILE"
  printf '%s' "$CLIENT_SECRETS" > "$CRED_FILE"
  chmod 600 "$CRED_FILE" || true
else
  if [ -f "$CRED_FILE" ]; then
    echo "Using credentials.json present in image"
  else
    echo "Warning: no credentials.json provided (neither env var nor file)"
  fi
fi

if [ -n "$TOKEN_JSON" ]; then
  echo "Writing TOKEN_JSON to $TOKEN_FILE"
  printf '%s' "$TOKEN_JSON" > "$TOKEN_FILE"
  chmod 600 "$TOKEN_FILE" || true
else
  if [ -f "$TOKEN_FILE" ]; then
    echo "Using token.json present in image"
  else
    echo "Warning: no token.json provided (neither env var nor file)"
  fi
fi

# Start the application (gunicorn)
exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 120 main:app
