"""
Tests for the restocking recommendation and restocking order endpoints.
"""
from datetime import date, timedelta

import pytest

from mock_data import restocking_orders


@pytest.fixture(autouse=True)
def clean_restocking_orders():
    """Restocking orders live in a module-level list; isolate each test."""
    restocking_orders.clear()
    yield
    restocking_orders.clear()


class TestRestockRecommendations:
    """Tests for GET /api/restocking/recommendations"""

    def test_zero_budget_recommends_nothing(self, client):
        data = client.get("/api/restocking/recommendations?budget=0").json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["remaining_budget"] == 0

    def test_negative_budget_returns_400(self, client):
        assert client.get("/api/restocking/recommendations?budget=-1").status_code == 400

    def test_never_exceeds_budget(self, client):
        for budget in (500, 5000, 20000, 100000):
            data = client.get(f"/api/restocking/recommendations?budget={budget}").json()
            assert data["total_cost"] <= budget
            assert data["remaining_budget"] == pytest.approx(budget - data["total_cost"], abs=0.01)

    def test_ranked_by_shortfall_and_quantity_capped(self, client):
        data = client.get("/api/restocking/recommendations?budget=100000").json()
        assert len(data["items"]) > 1
        shortfalls = [i["shortfall"] for i in data["items"]]
        assert shortfalls == sorted(shortfalls, reverse=True)
        for item in data["items"]:
            assert 0 < item["quantity"] <= item["shortfall"]
            assert item["line_total"] == pytest.approx(item["quantity"] * item["unit_cost"], abs=0.01)

    def test_large_budget_covers_every_shortfall(self, client):
        data = client.get("/api/restocking/recommendations?budget=100000").json()
        assert all(i["quantity"] == i["shortfall"] for i in data["items"])

    def test_small_budget_buys_partial_quantity(self, client):
        data = client.get("/api/restocking/recommendations?budget=1000").json()
        assert data["items"]
        assert any(i["quantity"] < i["shortfall"] for i in data["items"])

    def test_items_without_shortfall_are_excluded(self, client):
        skus = {i["sku"] for i in client.get("/api/restocking/recommendations?budget=100000").json()["items"]}
        # PSU-501 and MTR-304 have more stock than forecasted demand
        assert "PSU-501" not in skus
        assert "MTR-304" not in skus


class TestRestockOrders:
    """Tests for POST/GET /api/restocking-orders"""

    def _order(self, client, sku="WDG-001", quantity=10, budget=10000):
        return client.post("/api/restocking-orders", json={
            "budget": budget,
            "items": [{"sku": sku, "quantity": quantity}],
        })

    def test_create_order(self, client):
        response = self._order(client)
        assert response.status_code == 201
        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert order["total_value"] == pytest.approx(10 * 42.50)

    def test_lead_time_is_slowest_line(self, client):
        response = client.post("/api/restocking-orders", json={
            "budget": 100000,
            "items": [
                {"sku": "SNR-420", "quantity": 5},   # Sensors: 10 days
                {"sku": "WDG-001", "quantity": 5},   # Actuators: 14 days
            ],
        })
        order = response.json()
        assert order["lead_time_days"] == 14
        expected = date.today() + timedelta(days=14)
        assert order["expected_delivery"] == expected.isoformat()

    def test_prices_come_from_inventory_not_client(self, client):
        response = client.post("/api/restocking-orders", json={
            "budget": 10000,
            "items": [{"sku": "WDG-001", "quantity": 1, "unit_cost": 0.01}],
        })
        assert response.json()["items"][0]["unit_cost"] == 42.50

    def test_duplicate_skus_are_merged(self, client):
        response = client.post("/api/restocking-orders", json={
            "budget": 10000,
            "items": [{"sku": "WDG-001", "quantity": 3}, {"sku": "WDG-001", "quantity": 2}],
        })
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["quantity"] == 5

    def test_over_budget_rejected(self, client):
        assert self._order(client, quantity=1000, budget=100).status_code == 400

    def test_unknown_sku_rejected(self, client):
        assert self._order(client, sku="NOPE-000").status_code == 400

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_non_positive_quantity_rejected(self, client, quantity):
        assert self._order(client, quantity=quantity).status_code == 422

    def test_empty_items_rejected(self, client):
        assert client.post("/api/restocking-orders", json={"budget": 100, "items": []}).status_code == 422

    def test_list_orders_newest_first(self, client):
        self._order(client)
        self._order(client, sku="SNR-420")
        orders = client.get("/api/restocking-orders").json()
        assert [o["order_number"][-4:] for o in orders] == ["0002", "0001"]
