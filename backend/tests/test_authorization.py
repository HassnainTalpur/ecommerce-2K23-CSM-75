def test_admin_route_rejects_unauthenticated_request(client):
    response = client.post(
        "/api/v1/admin/categories",
        json={"name": "First Aid", "slug": "first-aid", "active": True},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"


def test_admin_route_rejects_non_admin(client, normal_headers):
    response = client.post(
        "/api/v1/admin/categories",
        headers=normal_headers,
        json={"name": "First Aid", "slug": "first-aid", "active": True},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "admin_required"
