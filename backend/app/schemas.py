from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import ProductStatus


Slug = Annotated[str, Field(min_length=1, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
Money = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    slug: Slug
    parent_id: int | None = None
    active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    slug: Slug | None = None
    parent_id: int | None = None
    active: bool | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int | None
    name: str
    description: str
    slug: str
    active: bool
    created_at: datetime
    updated_at: datetime


class CategoryTree(CategoryRead):
    children: list["CategoryTree"] = Field(default_factory=list)


Primitive = str | int | float | bool
SpecificationValue = Primitive | list[Primitive]


def _validate_specifications(value: dict[str, SpecificationValue]) -> dict[str, SpecificationValue]:
    if len(value) > 30:
        raise ValueError("a product may have at most 30 specification fields")
    for key, item in value.items():
        if not key.strip() or len(key) > 60:
            raise ValueError("specification keys must be 1 to 60 characters")
        if isinstance(item, list) and len(item) > 20:
            raise ValueError("a specification list may contain at most 20 values")
    return value


class ProductCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=150)
    slug: Slug
    description: str = Field(default="", max_length=5000)
    status: ProductStatus = ProductStatus.DRAFT
    specifications: dict[str, SpecificationValue] = Field(default_factory=dict)

    @field_validator("specifications")
    @classmethod
    def validate_specifications(cls, value):
        return _validate_specifications(value)


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=150)
    slug: Slug | None = None
    description: str | None = Field(default=None, max_length=5000)
    status: ProductStatus | None = None
    specifications: dict[str, SpecificationValue] | None = None

    @field_validator("specifications")
    @classmethod
    def validate_specifications(cls, value):
        if value is None:
            return value
        return _validate_specifications(value)


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    slug: str
    description: str
    status: str
    specifications: dict
    created_at: datetime
    updated_at: datetime


class VariantCreate(BaseModel):
    option_values: dict[str, str] = Field(min_length=1, max_length=12)

    @field_validator("option_values")
    @classmethod
    def clean_options(cls, value: dict[str, str]):
        cleaned: dict[str, str] = {}
        for key, option in value.items():
            k = key.strip().lower()
            v = option.strip()
            if not k or not v:
                raise ValueError("variant option names and values cannot be blank")
            if len(k) > 50 or len(v) > 80:
                raise ValueError("variant option names or values are too long")
            cleaned[k] = v
        if len(cleaned) != len(value):
            raise ValueError("variant option names must be unique")
        return cleaned


class VariantUpdate(VariantCreate):
    pass


class VariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    option_values: dict
    created_at: datetime
    updated_at: datetime


class SKUCreate(BaseModel):
    code: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    variant_id: int | None = None
    price: Money
    stock_quantity: int = Field(ge=0)
    active: bool = True


class SKUUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    price: Money | None = None
    stock_quantity: int | None = Field(default=None, ge=0)
    active: bool | None = None


class SKURead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    variant_id: int | None
    code: str
    price: Decimal
    stock_quantity: int
    active: bool
    created_at: datetime
    updated_at: datetime
