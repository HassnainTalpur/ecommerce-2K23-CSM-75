from tests.helpers import create_category


def test_category_create_list_update_and_deactivate(client, admin_headers):
    root = create_category(client, admin_headers, name="Emergency Supplies", slug="emergency-supplies")
    child = create_category(
        client,
        admin_headers,
        name="First Aid Supplies",
        slug="first-aid-supplies",
        parent_id=root["id"],
    )

    listed = client.get("/api/v1/admin/categories", headers=admin_headers)
    assert listed.status_code == 200
    tree = listed.json()
    assert len(tree) == 1
    assert tree[0]["slug"] == "emergency-supplies"
    assert [child["slug"] for child in tree[0]["children"]] == ["first-aid-supplies"]

    renamed = client.patch(
        f"/api/v1/admin/categories/{child['id']}",
        headers=admin_headers,
        json={"name": "Household First Aid"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Household First Aid"

    deleted = client.delete(f"/api/v1/admin/categories/{child['id']}", headers=admin_headers)
    assert deleted.status_code == 204
    read_back = client.get(f"/api/v1/admin/categories/{child['id']}", headers=admin_headers)
    assert read_back.json()["active"] is False


def test_duplicate_category_slug_is_rejected(client, admin_headers):
    create_category(client, admin_headers, name="Emergency Supplies", slug="emergency-supplies")
    response = client.post(
        "/api/v1/admin/categories",
        headers=admin_headers,
        json={"name": "Duplicate", "slug": "emergency-supplies", "active": True},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_slug"


def test_category_cycle_is_rejected(client, admin_headers):
    root = create_category(client, admin_headers, name="Emergency Supplies", slug="emergency-supplies")
    child = create_category(client, admin_headers, name="Lighting", slug="lighting", parent_id=root["id"])
    grandchild = create_category(client, admin_headers, name="Lanterns", slug="lanterns", parent_id=child["id"])

    response = client.patch(
        f"/api/v1/admin/categories/{root['id']}",
        headers=admin_headers,
        json={"parent_id": grandchild["id"]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "category_cycle"


def test_deactivating_parent_keeps_child_record(client, admin_headers):
    root = create_category(client, admin_headers, name="Emergency Supplies", slug="emergency-supplies")
    child = create_category(client, admin_headers, name="Lighting", slug="lighting", parent_id=root["id"])

    response = client.delete(f"/api/v1/admin/categories/{root['id']}", headers=admin_headers)
    assert response.status_code == 204

    child_after = client.get(f"/api/v1/admin/categories/{child['id']}", headers=admin_headers)
    assert child_after.status_code == 200
    assert child_after.json()["parent_id"] == root["id"]
    assert child_after.json()["active"] is True
