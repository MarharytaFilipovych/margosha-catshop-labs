import os
import requests

BASE = os.environ.get("QA_BASE_URL", "http://localhost:8080")
PARTNER = os.environ.get("QA_PROFILE", "") == "partner"


def test_ready_reports_postgres():
    body = requests.get(f"{BASE}/ready", timeout=5).json()
    assert body["ready"] is True
    assert body["store"] == "postgres"


def test_visits_are_stored_in_postgres():
    result = requests.get(f"{BASE}/visits", timeout=5)
    assert result.status_code == 200
    assert result.json()["store"] == "postgres"


def test_price_body_has_sku_and_currency_or_error():
    result = requests.get(f"{BASE}/price/MK-II", timeout=10)
    body = result.json()
    assert body["sku"] == "MK-II"
    if PARTNER:
        assert result.status_code == 200
        assert body["currency"] == "UAH"
    else:
        assert result.status_code == 502
        assert body["error"]


def test_post_to_health__endpoint_is_not_allowed():
    assert requests.post(f"{BASE}/health", timeout=5).status_code == 405
