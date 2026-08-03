"""
Tests for restocking API endpoints.
"""
import re
from datetime import datetime

import pytest


class TestRestockingRecommendationsEndpoint:
    """Test suite for restocking recommendation endpoint."""

    def test_zero_budget_returns_no_items(self, client):
        """Test that a zero budget yields no recommended items."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["remaining_budget"] == 0

    def test_recommendations_sorted_by_urgency(self, client):
        """Test that recommendations are ordered by trend (increasing > stable > decreasing),
        then by descending demand gap within the same trend."""
        response = client.get("/api/restocking/recommendations?budget=1000000")
        assert response.status_code == 200

        data = response.json()
        skus = [item["item_sku"] for item in data["items"]]
        assert skus == [
            "WDG-001", "FLT-405", "GSK-203",
            "BRG-102", "PSU-501", "SNR-420", "VLV-506", "CTL-330"
        ]

    def test_partial_fill_when_budget_insufficient_for_full_item(self, client):
        """Test that the last affordable item is partially filled and the walk stops there."""
        response = client.get("/api/restocking/recommendations?budget=7000")
        assert response.status_code == 200

        data = response.json()
        items = data["items"]
        assert len(items) == 2

        assert items[0]["item_sku"] == "WDG-001"
        assert items[0]["is_partial"] is False
        assert items[0]["quantity"] == items[0]["recommended_qty"] == 150

        assert items[1]["item_sku"] == "FLT-405"
        assert items[1]["is_partial"] is True
        assert items[1]["quantity"] == 40
        assert items[1]["quantity"] < items[1]["recommended_qty"]

        assert data["total_cost"] == 7000.0
        assert data["remaining_budget"] == 0.0

    def test_large_budget_fully_covers_all_gaps(self, client):
        """Test that a budget at or above max_useful_budget fully satisfies every item's gap."""
        probe = client.get("/api/restocking/recommendations?budget=0").json()
        max_useful_budget = probe["max_useful_budget"]

        response = client.get(f"/api/restocking/recommendations?budget={max_useful_budget}")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 8
        for item in data["items"]:
            assert item["is_partial"] is False
            assert item["quantity"] == item["recommended_qty"]
        assert data["remaining_budget"] >= 0

    def test_zero_gap_items_excluded(self, client):
        """Test that items with no demand gap (forecasted <= current) never appear."""
        response = client.get("/api/restocking/recommendations?budget=1000000")
        assert response.status_code == 200

        skus = [item["item_sku"] for item in response.json()["items"]]
        assert "MTR-304" not in skus

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget is rejected."""
        response = client.get("/api/restocking/recommendations?budget=-1")
        assert response.status_code == 400


class TestRestockingOrdersEndpoint:
    """Test suite for restocking order submission and retrieval."""

    def test_submit_order_creates_entry_visible_in_get(self, client):
        """Test that a submitted order appears in the submitted orders list."""
        response = client.post("/api/restocking/orders", json={
            "budget": 1000,
            "items": [{"item_sku": "SNR-420", "quantity": 5}]
        })
        assert response.status_code == 201
        order = response.json()

        list_response = client.get("/api/restocking/orders")
        assert list_response.status_code == 200
        order_ids = [o["id"] for o in list_response.json()]
        assert order["id"] in order_ids

    def test_lead_time_is_max_across_items(self, client):
        """Test that an order's lead time is the max lead_time_days across its items."""
        response = client.post("/api/restocking/orders", json={
            "budget": 5000,
            "items": [
                {"item_sku": "FLT-405", "quantity": 10},  # lead_time_days = 3
                {"item_sku": "MTR-304", "quantity": 2}    # lead_time_days = 21
            ]
        })
        assert response.status_code == 201
        order = response.json()
        assert order["lead_time_days"] == 21

    def test_expected_delivery_date_math(self, client):
        """Test that expected_delivery = order_date + lead_time_days."""
        response = client.post("/api/restocking/orders", json={
            "budget": 100,
            "items": [{"item_sku": "GSK-203", "quantity": 3}]  # lead_time_days = 5
        })
        assert response.status_code == 201
        order = response.json()

        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert (expected_delivery - order_date).days == order["lead_time_days"] == 5

    def test_unknown_sku_rejected(self, client):
        """Test that submitting an unknown SKU is rejected."""
        response = client.post("/api/restocking/orders", json={
            "budget": 100,
            "items": [{"item_sku": "NOT-A-REAL-SKU", "quantity": 1}]
        })
        assert response.status_code == 404

    def test_non_positive_quantity_rejected(self, client):
        """Test that a non-positive quantity is rejected."""
        response = client.post("/api/restocking/orders", json={
            "budget": 100,
            "items": [{"item_sku": "PSU-501", "quantity": 0}]
        })
        assert response.status_code == 400

    def test_empty_items_rejected(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restocking/orders", json={
            "budget": 100,
            "items": []
        })
        assert response.status_code == 400

    def test_order_number_format(self, client):
        """Test that the generated order_number matches the RST-YYYY-#### format."""
        response = client.post("/api/restocking/orders", json={
            "budget": 100,
            "items": [{"item_sku": "CTL-330", "quantity": 1}]
        })
        assert response.status_code == 201
        order = response.json()
        assert re.match(r"^RST-\d{4}-\d{4}$", order["order_number"])

    def test_order_total_cost_matches_line_costs(self, client):
        """Test that total_cost equals the sum of each item's line_cost."""
        response = client.post("/api/restocking/orders", json={
            "budget": 1000,
            "items": [
                {"item_sku": "VLV-506", "quantity": 4},
                {"item_sku": "BRG-102", "quantity": 6}
            ]
        })
        assert response.status_code == 201
        order = response.json()
        calculated_total = sum(item["line_cost"] for item in order["items"])
        assert abs(order["total_cost"] - calculated_total) < 0.01
