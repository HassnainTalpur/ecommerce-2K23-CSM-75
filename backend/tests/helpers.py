def create_category(client, headers, *, name="Emergency Lighting", slug="emergency-lighting", parent_id=None):
    response = client.post(
        "/api/v1/admin/categories",
        headers=headers,
        json={"name": name, "slug": slug, "parent_id": parent_id, "active": True},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_product(client, headers, category_id, *, name="Emergency Lantern", slug="emergency-lantern"):
    response = client.post(
        "/api/v1/admin/products",
        headers=headers,
        json={
            "category_id": category_id,
            "name": name,
            "slug": slug,
            "description": "Portable light for emergency use.",
            "status": "draft",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
