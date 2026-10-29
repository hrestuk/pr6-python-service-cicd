import pytest

from app import create_app

@pytest.fixture
def client(monkeypatch):
    """Створює тестовий клієнт Flask із коректними налаштуваннями."""
    monkeypatch.setenv("APP_VERSION", "0.1.0")
    monkeypatch.setenv("SIMULATE_HEALTH_FAILURE", "false")

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client

def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

# def test_version_returns_default_value(client):
#     response = client.get("/version")
#
#     assert response.status_code == 200
#     assert response.get_json() == {"version": "0.1.0"}
def test_version_returns_default_value(client):
    response = client.get("/version")

    assert response.status_code == 200
    assert response.get_json() == {"version": "9.9.9"}

@pytest.mark.parametrize(
    "version",
    ["0.1.0", "1.0.0", "test-build"],
)
def test_version_reads_environment(monkeypatch, version):
    monkeypatch.setenv("APP_VERSION", version)
    monkeypatch.setenv("SIMULATE_HEALTH_FAILURE", "false")

    app = create_app()
    response = app.test_client().get("/version")

    assert response.status_code == 200
    assert response.get_json() == {"version": version}

def test_health_can_return_unhealthy(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "0.1.0")
    monkeypatch.setenv("SIMULATE_HEALTH_FAILURE", "true")

    app = create_app()
    response = app.test_client().get("/health")

    assert response.status_code == 503
    assert response.get_json() == {"status": "unhealthy"}

def test_empty_version_is_rejected(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "")
    monkeypatch.setenv("SIMULATE_HEALTH_FAILURE", "false")

    with pytest.raises(ValueError, match="APP_VERSION"):
        create_app()

def test_invalid_health_setting_is_rejected(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "0.1.0")
    monkeypatch.setenv("SIMULATE_HEALTH_FAILURE", "sometimes")

    with pytest.raises(ValueError, match="SIMULATE_HEALTH_FAILURE"):
        create_app()
