import importlib

import pytest

import app

COUNTER_FILE = "COUNTER_FILE"
DB_URL = "DATABASE_URL"
PARTNER_URL = "PARTNER_URL"
PARTNER_TIMEOUT = "PARTNER_TIMEOUT"

HEALTH_PATH = "/health"
READY_PATH = "/ready"
VISITS_PATH = "/visits"
PRICE_PATH = "/price/{sku}"

VISITS = "visits"
VISITS_FILE = "visits.txt"
STORE = "store"
READY = "ready"

UNREACHABLE = "127.0.0.1:9"


def load_app():
    importlib.reload(app)
    app.app.config.update(TESTING=True)
    return app


@pytest.fixture
def make_client(tmp_path, monkeypatch):
    monkeypatch.setenv(COUNTER_FILE, str(tmp_path / VISITS_FILE))
    monkeypatch.delenv(DB_URL, raising=False)
    return lambda: load_app().app.test_client()


@pytest.fixture
def client(make_client):
    return make_client()


def test_health_returns_ok(client):
    result = client.get(HEALTH_PATH)
    assert result.status_code == 200
    assert result.data.decode().strip() == "ok"


def test_ready_returns_the_file_store_name_when_db_env_is_not_set(client):
    result = client.get(READY_PATH).get_json()
    assert result[READY] is True
    assert result[STORE].startswith("file:")


def test_ready_reports_not_ready_when_store_is_broken(make_client, monkeypatch, tmp_path):
    broken = tmp_path / "broken.txt"
    broken.write_text("a file, not a directory")
    monkeypatch.setenv(COUNTER_FILE, str(broken / VISITS_FILE))

    result = make_client().get(READY_PATH)
    assert result.status_code == 503
    assert result.get_json()[READY] is False


def test_visits_counts_invocations(client):
    first_time = client.get(VISITS_PATH).get_json()
    second_time = client.get(VISITS_PATH).get_json()
    assert second_time[VISITS] == first_time[VISITS] + 1
    assert second_time == {VISITS: 2, STORE: "file"}


def test_visits_returns_1_on_the_first_invocation(client, tmp_path):
    result = client.get(VISITS_PATH)
    assert result.status_code == 200
    assert result.get_json() == {VISITS: 1, STORE: "file"}
    assert (tmp_path / VISITS_FILE).read_text() == "1"


def test_database_url_switches_to_postgres_and_a_dead_db_answers_503(make_client, monkeypatch, tmp_path):
    monkeypatch.setenv(DB_URL, f"postgresql://cat:cat@{UNREACHABLE}/catshop")
    test_client = make_client()

    visits = test_client.get(VISITS_PATH)
    assert visits.status_code == 503
    assert visits.get_json()[STORE] == "postgres"

    ready = test_client.get(READY_PATH)
    assert ready.status_code == 503
    assert ready.get_json()[READY] is False

    assert not (tmp_path / VISITS_FILE).exists()


def test_price_fails_when_partner_cannot_be_reached(make_client, monkeypatch):
    monkeypatch.setenv(PARTNER_URL, f"http://{UNREACHABLE}")
    monkeypatch.setenv(PARTNER_TIMEOUT, "0.25")

    result = make_client().get(PRICE_PATH.format(sku="MK-II"))
    body = result.get_json()
    assert result.status_code == 502
    assert body["error"] in ("ConnectionError", "ConnectTimeout")
    assert body["sku"] == "MK-II"
    assert UNREACHABLE in body["source"]


class FakePartnerResponse:
    sku = "PRETTY_SKU"
    price = "666"
    currency = "NO_CURRENCY"

    def raise_for_status(self):
        pass

    def json(self):
        return {"sku": self.sku, "price": self.price, "currency": self.currency}


def test_price_returns_the_partner_price_when_the_partner_answers(make_client, monkeypatch):
    partner_url = "http://partner_in_test"
    monkeypatch.setenv(PARTNER_URL, partner_url)
    expected_source = f"{partner_url}/v1/catalog/{FakePartnerResponse.sku}"
    expected_timeout = 2.0

    app_module = load_app()

    requested_urls = []
    requested_timeouts = []

    def fake_get(url, timeout):
        requested_urls.append(url)
        requested_timeouts.append(timeout)
        return FakePartnerResponse()

    monkeypatch.setattr(app_module.requests, "get", fake_get)

    result = app_module.app.test_client().get(PRICE_PATH.format(sku=FakePartnerResponse.sku))
    assert result.status_code == 200

    assert result.get_json() == {
        "sku": FakePartnerResponse.sku,
        "price": FakePartnerResponse.price,
        "currency": FakePartnerResponse.currency,
        "source": expected_source
    }
    assert requested_urls == [expected_source]
    assert requested_timeouts == [expected_timeout]
