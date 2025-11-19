#!/bin/sh
set -e

# If secrets are injected as env vars, write them to the files the app expects.
# If the files already exist in the image (because you committed them), we keep them
# unless the corresponding env var is set (env var overrides image contents).

APP_DIR=/app
CRED_FILE="$APP_DIR/credentials.json"
TOKEN_FILE="$APP_DIR/token.json"

if [ -n "$CLIENT_SECRETS" ]; then
  echo "[entrypoint] CLIENT_SECRETS env var present (length: $(printf '%s' "$CLIENT_SECRETS" | wc -c) bytes)"
  echo "[entrypoint] Writing CLIENT_SECRETS to $CRED_FILE"
  # write safely
  printf '%s' "$CLIENT_SECRETS" > "$CRED_FILE"
  chmod 600 "$CRED_FILE" || true
  echo "[entrypoint] Wrote $CRED_FILE (size: $(stat -c%s "$CRED_FILE" 2>/dev/null || echo 'unknown') bytes)"
else
  if [ -f "$CRED_FILE" ]; then
    echo "Using credentials.json present in image"
  else
    echo "Warning: no credentials.json provided (neither env var nor file)"
  fi
fi

if [ -n "$TOKEN_JSON" ]; then
  echo "[entrypoint] TOKEN_JSON env var present (length: $(printf '%s' "$TOKEN_JSON" | wc -c) bytes)"
  echo "[entrypoint] Writing TOKEN_JSON to $TOKEN_FILE"
  printf '%s' "$TOKEN_JSON" > "$TOKEN_FILE"
  chmod 600 "$TOKEN_FILE" || true
  echo "[entrypoint] Wrote $TOKEN_FILE (size: $(stat -c%s "$TOKEN_FILE" 2>/dev/null || echo 'unknown') bytes)"
else
  if [ -f "$TOKEN_FILE" ]; then
    echo "Using token.json present in image"
  else
    echo "Warning: no token.json provided (neither env var nor file)"
  fi
fi

# Debug: show working directory contents so Cloud Run logs include file listing
echo "[entrypoint] Current working directory: $(pwd)"
echo "[entrypoint] Files in /app:" 
ls -la /app || true
echo "[entrypoint] /app file sizes:" 
for f in "$CRED_FILE" "$TOKEN_FILE"; do
  if [ -f "$f" ]; then
    printf "%s: %s bytes\n" "$f" "$(stat -c%s "$f" 2>/dev/null || echo 'unknown')"
  else
    printf "%s: not present\n" "$f"
  fi
done

# Small guard: fail early with clear message if neither secret exists
if [ ! -f "$CRED_FILE" ] && [ -z "$CLIENT_SECRETS" ]; then
  echo "[entrypoint] WARNING: credentials.json is not present and CLIENT_SECRETS env var is empty"
fi

# End debug
# Start the application (gunicorn)
exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 600 main:app
