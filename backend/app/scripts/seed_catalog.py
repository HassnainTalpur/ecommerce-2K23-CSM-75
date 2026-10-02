from decimal import Decimal

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Category, Product, SKU, Variant
from app.services import normalize_variant_options


CATEGORY_DATA = [
    ("Emergency Supplies", "emergency-supplies", None),
    ("First Aid Supplies", "first-aid-supplies", "emergency-supplies"),
    ("Emergency Lighting", "emergency-lighting", "emergency-supplies"),
    ("Water Storage & Filtration", "water-storage-filtration", "emergency-supplies"),
]


def get_or_create_category(db, name: str, slug: str, parent: Category | None) -> Category:
    category = db.scalar(select(Category).where(Category.slug == slug))
    if category is None:
        category = Category(name=name, slug=slug, parent=parent, active=True)
        db.add(category)
        db.flush()
    return category


def get_or_create_product(db, *, category: Category, name: str, slug: str, description: str) -> Product:
    product = db.scalar(select(Product).where(Product.slug == slug))
    if product is None:
        product = Product(
            category_id=category.id,
            name=name,
            slug=slug,
            description=description,
            status="draft",
            specifications={},
        )
        db.add(product)
        db.flush()
    return product


def get_or_create_variant(db, product: Product, options: dict[str, str]) -> Variant:
    values, signature = normalize_variant_options(options)
    variant = db.scalar(
        select(Variant).where(Variant.product_id == product.id, Variant.option_signature == signature)
    )
    if variant is None:
        variant = Variant(product_id=product.id, option_values=values, option_signature=signature)
        db.add(variant)
        db.flush()
    return variant


def get_or_create_sku(
    db,
    *,
    product: Product,
    code: str,
    price: Decimal,
    stock: int,
    variant: Variant | None = None,
):
    sku = db.scalar(select(SKU).where(SKU.code == code))
    if sku is None:
        sku = SKU(
            product_id=product.id,
            variant_id=variant.id if variant else None,
            code=code,
            price=price,
            stock_quantity=stock,
            active=True,
        )
        db.add(sku)
        db.flush()
    return sku


def seed_catalog():
    with SessionLocal() as db:
        categories: dict[str, Category] = {}
        for name, slug, parent_slug in CATEGORY_DATA:
            parent = categories.get(parent_slug) if parent_slug else None
            categories[slug] = get_or_create_category(db, name, slug, parent)

        first_aid = get_or_create_product(
            db,
            category=categories["first-aid-supplies"],
            name="Home First Aid Kit",
            slug="home-first-aid-kit",
            description="Compact household kit for common minor injuries and basic emergency preparation.",
        )
        get_or_create_sku(db, product=first_aid, code="RS-FAK-001", price=Decimal("39.90"), stock=25)

        lantern = get_or_create_product(
            db,
            category=categories["emergency-lighting"],
            name="Rechargeable Emergency Lantern",
            slug="rechargeable-emergency-lantern",
            description="Portable emergency lantern available in selected colour and power-source combinations.",
        )
        black_rechargeable = get_or_create_variant(db, lantern, {"color": "Black", "power": "Rechargeable"})
        red_rechargeable = get_or_create_variant(db, lantern, {"color": "Red", "power": "Rechargeable"})
        black_solar = get_or_create_variant(db, lantern, {"color": "Black", "power": "Solar"})
        get_or_create_sku(
            db, product=lantern, variant=black_rechargeable, code="RS-LAN-BLK-R", price=Decimal("54.50"), stock=18
        )
        get_or_create_sku(
            db, product=lantern, variant=red_rechargeable, code="RS-LAN-RED-R", price=Decimal("54.50"), stock=7
        )
        get_or_create_sku(
            db, product=lantern, variant=black_solar, code="RS-LAN-BLK-S", price=Decimal("61.00"), stock=0
        )
        # Red + Solar is intentionally not inserted. A missing combination stays missing instead of
        # being represented by a made-up zero-stock SKU.

        water_filter = get_or_create_product(
            db,
            category=categories["water-storage-filtration"],
            name="Emergency Water Filter Bottle",
            slug="emergency-water-filter-bottle",
            description="Reusable bottle intended for emergency water filtration and preparedness kits.",
        )
        get_or_create_sku(db, product=water_filter, code="RS-WFB-001", price=Decimal("28.75"), stock=14)

        db.commit()

    print("Catalog seed complete: 4 categories, 3 products, 3 lantern variants, 5 SKUs.")
    print("Intentionally unavailable combination: Rechargeable Emergency Lantern / Red / Solar.")


if __name__ == "__main__":
    seed_catalog()
