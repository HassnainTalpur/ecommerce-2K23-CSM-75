from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.errors import ApiError
from app.models import SKU, User, Variant
from app.schemas import VariantCreate, VariantRead, VariantUpdate
from app.services import (
    commit_or_conflict,
    ensure_unique_variant,
    get_product,
    get_variant,
    normalize_variant_options,
)


router = APIRouter(prefix="/api/v1/admin", tags=["admin variants"])


@router.post("/products/{product_id}/variants", response_model=VariantRead, status_code=status.HTTP_201_CREATED)
def create_variant(
    product_id: int,
    payload: VariantCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    get_product(db, product_id)
    values, signature = normalize_variant_options(payload.option_values)
    ensure_unique_variant(db, product_id, signature)
    variant = Variant(product_id=product_id, option_values=values, option_signature=signature)
    db.add(variant)
    commit_or_conflict(db)
    db.refresh(variant)
    return variant


@router.get("/products/{product_id}/variants", response_model=list[VariantRead])
def list_variants(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    get_product(db, product_id)
    return list(db.scalars(select(Variant).where(Variant.product_id == product_id).order_by(Variant.id)))


@router.get("/variants/{variant_id}", response_model=VariantRead)
def read_variant(variant_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return get_variant(db, variant_id)


@router.patch("/variants/{variant_id}", response_model=VariantRead)
def update_variant(
    variant_id: int,
    payload: VariantUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    variant = get_variant(db, variant_id)
    values, signature = normalize_variant_options(payload.option_values)
    ensure_unique_variant(db, variant.product_id, signature, exclude_id=variant.id)
    variant.option_values = values
    variant.option_signature = signature
    commit_or_conflict(db)
    db.refresh(variant)
    return variant


@router.delete("/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(variant_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    variant = get_variant(db, variant_id)
    if db.scalar(select(SKU.id).where(SKU.variant_id == variant.id).limit(1)) is not None:
        raise ApiError(409, "variant_in_use", "A variant with a SKU cannot be deleted. Deactivate the SKU instead.")
    db.delete(variant)
    commit_or_conflict(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
