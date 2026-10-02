import json

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import Category, Product, ProductStatus, SKU, Variant


def commit_or_conflict(db: Session, *, code: str = "constraint_violation", message: str = "The change violates a database constraint."):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(409, code, message) from exc


def ensure_unique_slug(db: Session, model, slug: str, *, exclude_id: int | None = None):
    query = select(model).where(model.slug == slug)
    if exclude_id is not None:
        query = query.where(model.id != exclude_id)
    if db.scalar(query) is not None:
        raise ApiError(409, "duplicate_slug", f"The slug '{slug}' is already in use.")


def ensure_unique_sku_code(db: Session, code: str, *, exclude_id: int | None = None):
    query = select(SKU).where(SKU.code == code)
    if exclude_id is not None:
        query = query.where(SKU.id != exclude_id)
    if db.scalar(query) is not None:
        raise ApiError(409, "duplicate_sku", f"The SKU code '{code}' is already in use.")


def get_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise ApiError(404, "category_not_found", "Category not found.")
    return category


def validate_category_parent(db: Session, category_id: int | None, parent_id: int | None):
    if parent_id is None:
        return
    if category_id is not None and parent_id == category_id:
        raise ApiError(422, "category_cycle", "A category cannot be its own parent.")

    parent = get_category(db, parent_id)
    seen: set[int] = set()
    current = parent
    while current is not None:
        if current.id in seen:
            raise ApiError(422, "category_cycle", "The existing category tree contains a cycle.")
        seen.add(current.id)
        if category_id is not None and current.id == category_id:
            raise ApiError(422, "category_cycle", "The selected parent would create a category cycle.")
        current = current.parent


def get_product(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise ApiError(404, "product_not_found", "Product not found.")
    return product


def ensure_category_assignable(db: Session, category_id: int) -> Category:
    category = get_category(db, category_id)
    if not category.active:
        raise ApiError(422, "inactive_category", "Products cannot be assigned to an inactive category.")
    return category


def ensure_publishable(db: Session, product: Product):
    active_sku = db.scalar(select(SKU).where(SKU.product_id == product.id, SKU.active.is_(True)).limit(1))
    if active_sku is None:
        raise ApiError(409, "no_sellable_sku", "A product needs at least one active SKU before it can be published.")



def ensure_sku_can_be_deactivated(db: Session, sku: SKU):
    product = get_product(db, sku.product_id)
    if product.status != ProductStatus.PUBLISHED.value or not sku.active:
        return
    another_active = db.scalar(
        select(SKU.id).where(SKU.product_id == product.id, SKU.active.is_(True), SKU.id != sku.id).limit(1)
    )
    if another_active is None:
        raise ApiError(409, "last_sellable_sku", "A published product must keep at least one active SKU.")


def normalize_variant_options(options: dict[str, str]) -> tuple[dict[str, str], str]:
    normalized = {key.strip().lower(): value.strip() for key, value in options.items()}
    signature = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return normalized, signature


def ensure_unique_variant(db: Session, product_id: int, signature: str, *, exclude_id: int | None = None):
    query = select(Variant).where(Variant.product_id == product_id, Variant.option_signature == signature)
    if exclude_id is not None:
        query = query.where(Variant.id != exclude_id)
    if db.scalar(query) is not None:
        raise ApiError(409, "duplicate_variant", "That variant combination already exists for this product.")


def get_variant(db: Session, variant_id: int) -> Variant:
    variant = db.get(Variant, variant_id)
    if variant is None:
        raise ApiError(404, "variant_not_found", "Variant not found.")
    return variant


def get_sku(db: Session, sku_id: int) -> SKU:
    sku = db.get(SKU, sku_id)
    if sku is None:
        raise ApiError(404, "sku_not_found", "SKU not found.")
    return sku
