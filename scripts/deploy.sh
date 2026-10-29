
#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/home/pr6user/pr6-deploy"
NEW_TAG="${1:?Pass the new image tag}"
SIMULATE="${2:-false}"

if [[ ! "$NEW_TAG" =~ ^[a-f0-9]{40}$ ]]; then
    echo "Invalid commit SHA: $NEW_TAG" >&2
    exit 2
fi

if [[ "$SIMULATE" != "true" && "$SIMULATE" != "false" ]]; then
    echo "SIMULATE must be true or false" >&2
    exit 2
fi

cd "$APP_DIR"

if ! docker info >/dev/null 2>&1; then
    echo "Docker is not accessible to the deployment user." >&2
    exit 1
fi

docker load -i "$APP_DIR/pr6-image.tar"

if ! docker image inspect "pr6-python-service:$NEW_TAG" >/dev/null 2>&1; then
    echo "Image for commit $NEW_TAG was not found." >&2
    exit 1
fi

PREVIOUS_TAG=""

if [[ -f .env ]]; then
    cp .env .env.previous
    PREVIOUS_TAG="$(sed -n 's/^IMAGE_TAG=//p' .env.previous | head -n 1)"
fi

cat > .env <<EOF
IMAGE_TAG=$NEW_TAG
APP_VERSION=$NEW_TAG
SIMULATE_HEALTH_FAILURE=$SIMULATE
EOF

dc() {
    docker compose --env-file "$APP_DIR/.env" \
        -f "$APP_DIR/compose.deploy.yaml" "$@"
}

wait_for_health() {
    for attempt in $(seq 1 15); do
        if curl --fail --silent --max-time 3 \
            http://127.0.0.1:5000/health >/dev/null; then
            return 0
        fi
        sleep 2
    done
    return 1
}

rollback() {
    if [[ -z "$PREVIOUS_TAG" ]]; then
        echo "Rollback unavailable: no previous deployment exists." >&2
        return 1
    fi

    if ! docker image inspect \
        "pr6-python-service:$PREVIOUS_TAG" >/dev/null 2>&1; then
        echo "Previous image is missing: $PREVIOUS_TAG" >&2
        return 1
    fi

    echo "Restoring previous image: $PREVIOUS_TAG"

    cp .env.previous .env

    if ! dc up -d --no-build --force-recreate; then
        echo "Failed to start the previous version." >&2
        return 1
    fi

    if wait_for_health; then
        printf '%s\n' "$PREVIOUS_TAG" > .current_tag
        echo "Rollback succeeded: $PREVIOUS_TAG"
        return 0
    fi

    echo "Rollback completed, but health check still fails." >&2
    dc logs --no-color || true
    return 1
}

if ! dc up -d --no-build --force-recreate; then
    echo "Deployment command failed." >&2
    dc logs --no-color || true
    if ! rollback; then
        echo "Automatic rollback failed." >&2
    fi
    exit 1
fi

if wait_for_health; then
    printf '%s\n' "$NEW_TAG" > .current_tag
    rm -f "$APP_DIR/pr6-image.tar"
    echo "Deployment succeeded: $NEW_TAG"
    exit 0
fi

echo "Health check failed. Collecting logs and rolling back." >&2
dc logs --no-color || true

if ! rollback; then
    echo "Automatic rollback failed." >&2
fi

exit 1
