from tests.helpers import create_category, create_product


def test_product_create_and_duplicate_slug_rejection(client, admin_headers):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    assert product["status"] == "draft"

    duplicate = client.post(
        "/api/v1/admin/products",
        headers=admin_headers,
        json={
            "category_id": category["id"],
            "name": "Another Lantern",
            "slug": "emergency-lantern",
            "description": "Different product, duplicate slug.",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "duplicate_slug"


def test_product_required_field_validation(client, admin_headers):
    category = create_category(client, admin_headers)
    response = client.post(
        "/api/v1/admin/products",
        headers=admin_headers,
        json={"category_id": category["id"], "slug": "missing-name"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_published_product_requires_active_sku(client, admin_headers):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])

    blocked = client.patch(
        f"/api/v1/admin/products/{product['id']}",
        headers=admin_headers,
        json={"status": "published"},
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "no_sellable_sku"

    sku = client.post(
        f"/api/v1/admin/products/{product['id']}/skus",
        headers=admin_headers,
        json={"code": "RS-LAN-001", "price": "49.90", "stock_quantity": 0, "active": True},
    )
    assert sku.status_code == 201

    published = client.patch(
        f"/api/v1/admin/products/{product['id']}",
        headers=admin_headers,
        json={"status": "published"},
    )
    assert published.status_code == 200
    assert published.json()["status"] == "published"


def test_product_cannot_be_assigned_to_inactive_category(client, admin_headers):
    category = create_category(client, admin_headers)
    client.delete(f"/api/v1/admin/categories/{category['id']}", headers=admin_headers)

    response = client.post(
        "/api/v1/admin/products",
        headers=admin_headers,
        json={
            "category_id": category["id"],
            "name": "Emergency Lantern",
            "slug": "emergency-lantern",
            "description": "Portable light.",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "inactive_category"


def test_last_active_sku_cannot_be_deactivated_from_published_product(client, admin_headers):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    sku = client.post(
        f"/api/v1/admin/products/{product['id']}/skus",
        headers=admin_headers,
        json={"code": "RS-PUB-001", "price": "22.00", "stock_quantity": 3, "active": True},
    ).json()
    published = client.patch(
        f"/api/v1/admin/products/{product['id']}",
        headers=admin_headers,
        json={"status": "published"},
    )
    assert published.status_code == 200

    blocked = client.delete(f"/api/v1/admin/skus/{sku['id']}", headers=admin_headers)
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "last_sellable_sku"
