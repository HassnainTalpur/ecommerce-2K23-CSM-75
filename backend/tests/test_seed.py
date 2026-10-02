from sqlalchemy import select

from app.database import SessionLocal
from app.models import Category, Product, SKU, Variant
from app.scripts.seed_catalog import seed_catalog
from app.services import normalize_variant_options


def test_seed_is_repeatable_and_keeps_unavailable_combination_absent():
    seed_catalog()
    seed_catalog()

    with SessionLocal() as db:
        assert len(list(db.scalars(select(Category)))) == 4
        assert len(list(db.scalars(select(Product)))) == 3
        assert len(list(db.scalars(select(SKU)))) == 5
        assert len(list(db.scalars(select(Variant)))) == 3

        lantern = db.scalar(select(Product).where(Product.slug == "rechargeable-emergency-lantern"))
        _, unavailable_signature = normalize_variant_options({"color": "Red", "power": "Solar"})
        missing = db.scalar(
            select(Variant).where(
                Variant.product_id == lantern.id,
                Variant.option_signature == unavailable_signature,
            )
        )
        assert missing is None
