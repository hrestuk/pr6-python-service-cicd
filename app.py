import os

from flask import Flask, jsonify

def create_app():
    version = os.getenv("APP_VERSION", "0.1.0").strip()

    if not version:
        raise ValueError("APP_VERSION must not be empty")

    health_setting = os.getenv(
        "SIMULATE_HEALTH_FAILURE", "false"
    ).strip().lower()

    if health_setting not in {"true", "false"}:
        raise ValueError(
            "SIMULATE_HEALTH_FAILURE must be true or false"
        )

    simulate_health_failure = health_setting == "true"

    app = Flask(__name__)

    @app.get("/health")
    def health():
        if simulate_health_failure:
            return jsonify(status="unhealthy"), 503

        return jsonify(status="ok"), 200

    @app.get("/version")
    def version_info():
        return jsonify(version=version), 200

    return app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
    )