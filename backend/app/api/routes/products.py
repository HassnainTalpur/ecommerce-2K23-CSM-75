from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.errors import ApiError
from app.models import Product, ProductStatus, User
from app.schemas import ProductCreate, ProductRead, ProductUpdate
from app.services import (
    commit_or_conflict,
    ensure_category_assignable,
    ensure_publishable,
    ensure_unique_slug,
    get_product,
)


router = APIRouter(prefix="/api/v1/admin/products", tags=["admin products"])


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    ensure_unique_slug(db, Product, payload.slug)
    ensure_category_assignable(db, payload.category_id)
    if payload.status == ProductStatus.PUBLISHED:
        raise ApiError(409, "no_sellable_sku", "Create the product as a draft, add an active SKU, then publish it.")

    product = Product(**payload.model_dump(mode="json"))
    db.add(product)
    commit_or_conflict(db)
    db.refresh(product)
    return product


@router.get("", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return list(db.scalars(select(Product).order_by(Product.id)))


@router.get("/{product_id}", response_model=ProductRead)
def read_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return get_product(db, product_id)


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    product = get_product(db, product_id)
    changes = payload.model_dump(exclude_unset=True, mode="json")

    if "slug" in changes:
        ensure_unique_slug(db, Product, changes["slug"], exclude_id=product.id)
    if "category_id" in changes:
        ensure_category_assignable(db, changes["category_id"])
    if changes.get("status") == ProductStatus.PUBLISHED.value:
        ensure_publishable(db, product)

    for field, value in changes.items():
        setattr(product, field, value)
    commit_or_conflict(db)
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    product = get_product(db, product_id)
    product.status = ProductStatus.INACTIVE.value
    commit_or_conflict(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
