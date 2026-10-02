from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import Category, User
from app.schemas import CategoryCreate, CategoryRead, CategoryTree, CategoryUpdate
from app.services import (
    commit_or_conflict,
    ensure_unique_slug,
    get_category,
    validate_category_parent,
)


router = APIRouter(prefix="/api/v1/admin/categories", tags=["admin categories"])


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    ensure_unique_slug(db, Category, payload.slug)
    validate_category_parent(db, None, payload.parent_id)
    category = Category(**payload.model_dump())
    db.add(category)
    commit_or_conflict(db)
    db.refresh(category)
    return category


@router.get("", response_model=list[CategoryTree])
def list_categories(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    categories = list(db.scalars(select(Category).order_by(Category.name)))
    nodes = {
        category.id: CategoryTree.model_validate(category).model_copy(update={"children": []})
        for category in categories
    }
    roots: list[CategoryTree] = []
    for category in categories:
        node = nodes[category.id]
        if category.parent_id is None:
            roots.append(node)
        else:
            nodes[category.parent_id].children.append(node)
    return roots


@router.get("/{category_id}", response_model=CategoryRead)
def read_category(category_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return get_category(db, category_id)


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    category = get_category(db, category_id)
    changes = payload.model_dump(exclude_unset=True)
    if "slug" in changes:
        ensure_unique_slug(db, Category, changes["slug"], exclude_id=category.id)
    if "parent_id" in changes:
        validate_category_parent(db, category.id, changes["parent_id"])

    for field, value in changes.items():
        setattr(category, field, value)
    commit_or_conflict(db)
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    category = get_category(db, category_id)
    category.active = False
    commit_or_conflict(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
