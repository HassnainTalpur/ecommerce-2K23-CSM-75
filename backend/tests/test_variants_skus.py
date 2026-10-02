from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import SKU
from tests.helpers import create_category, create_product


def setup_product(client, headers, *, category_slug="emergency-lighting", product_slug="emergency-lantern"):
    category = create_category(client, headers, slug=category_slug)
    return create_product(client, headers, category["id"], slug=product_slug)


def test_variant_combination_must_be_unique(client, admin_headers):
    product = setup_product(client, admin_headers)
    payload = {"option_values": {"color": "Black", "power": "Rechargeable"}}

    first = client.post(f"/api/v1/admin/products/{product['id']}/variants", headers=admin_headers, json=payload)
    assert first.status_code == 201

    duplicate = client.post(f"/api/v1/admin/products/{product['id']}/variants", headers=admin_headers, json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "duplicate_variant"


def test_sku_code_and_stock_rules(client, admin_headers):
    product = setup_product(client, admin_headers)
    variant = client.post(
        f"/api/v1/admin/products/{product['id']}/variants",
        headers=admin_headers,
        json={"option_values": {"color": "Black", "power": "Rechargeable"}},
    ).json()

    created = client.post(
        f"/api/v1/admin/products/{product['id']}/skus",
        headers=admin_headers,
        json={"code": "RS-LAN-BLK-R", "variant_id": variant["id"], "price": "54.50", "stock_quantity": 4},
    )
    assert created.status_code == 201

    duplicate_code = client.post(
        f"/api/v1/admin/products/{product['id']}/skus",
        headers=admin_headers,
        json={"code": "RS-LAN-BLK-R", "price": "55.00", "stock_quantity": 1},
    )
    assert duplicate_code.status_code == 409
    assert duplicate_code.json()["error"]["code"] == "duplicate_sku"

    negative = client.patch(
        f"/api/v1/admin/skus/{created.json()['id']}",
        headers=admin_headers,
        json={"stock_quantity": -1},
    )
    assert negative.status_code == 422


def test_variant_must_belong_to_same_product_as_sku(client, admin_headers):
    first = setup_product(client, admin_headers, category_slug="lighting-one", product_slug="lantern-one")
    second_category = create_category(client, admin_headers, name="Second Lighting", slug="lighting-two")
    second = create_product(client, admin_headers, second_category["id"], name="Lantern Two", slug="lantern-two")

    variant = client.post(
        f"/api/v1/admin/products/{first['id']}/variants",
        headers=admin_headers,
        json={"option_values": {"color": "Black"}},
    ).json()

    response = client.post(
        f"/api/v1/admin/products/{second['id']}/skus",
        headers=admin_headers,
        json={"code": "RS-BAD-001", "variant_id": variant["id"], "price": "10.00", "stock_quantity": 1},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "variant_product_mismatch"


def test_database_rejects_negative_stock_even_if_api_is_bypassed(client, admin_headers):
    product = setup_product(client, admin_headers)

    with SessionLocal() as db:
        db.add(SKU(product_id=product["id"], code="RS-NEG-001", price=Decimal("10.00"), stock_quantity=-5, active=True))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
