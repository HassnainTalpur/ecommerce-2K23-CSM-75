from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.errors import ApiError
from app.models import SKU, User
from app.schemas import SKUCreate, SKURead, SKUUpdate
from app.services import (
    commit_or_conflict,
    ensure_sku_can_be_deactivated,
    ensure_unique_sku_code,
    get_product,
    get_sku,
    get_variant,
)


router = APIRouter(prefix="/api/v1/admin", tags=["admin skus"])


@router.post("/products/{product_id}/skus", response_model=SKURead, status_code=status.HTTP_201_CREATED)
def create_sku(
    product_id: int,
    payload: SKUCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    get_product(db, product_id)
    ensure_unique_sku_code(db, payload.code)

    if payload.variant_id is not None:
        variant = get_variant(db, payload.variant_id)
        if variant.product_id != product_id:
            raise ApiError(422, "variant_product_mismatch", "The selected variant belongs to a different product.")
        existing = db.scalar(select(SKU).where(SKU.variant_id == variant.id))
        if existing is not None:
            raise ApiError(409, "variant_has_sku", "This variant already has a SKU.")

    sku = SKU(product_id=product_id, **payload.model_dump())
    db.add(sku)
    commit_or_conflict(db)
    db.refresh(sku)
    return sku


@router.get("/products/{product_id}/skus", response_model=list[SKURead])
def list_skus(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    get_product(db, product_id)
    return list(db.scalars(select(SKU).where(SKU.product_id == product_id).order_by(SKU.id)))


@router.get("/skus/{sku_id}", response_model=SKURead)
def read_sku(sku_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return get_sku(db, sku_id)


@router.patch("/skus/{sku_id}", response_model=SKURead)
def update_sku(
    sku_id: int,
    payload: SKUUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    sku = get_sku(db, sku_id)
    changes = payload.model_dump(exclude_unset=True)
    if "code" in changes:
        ensure_unique_sku_code(db, changes["code"], exclude_id=sku.id)
    if changes.get("active") is False:
        ensure_sku_can_be_deactivated(db, sku)
    for field, value in changes.items():
        setattr(sku, field, value)
    commit_or_conflict(db)
    db.refresh(sku)
    return sku


@router.delete("/skus/{sku_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_sku(sku_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    sku = get_sku(db, sku_id)
    ensure_sku_can_be_deactivated(db, sku)
    sku.active = False
    commit_or_conflict(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
