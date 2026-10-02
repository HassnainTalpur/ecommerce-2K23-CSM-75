"""catalog foundation

Revision ID: 20261002_0001
Revises:
Create Date: 2026-10-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20261002_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("parent_id IS NULL OR parent_id <> id", name="ck_categories_not_own_parent"),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], ondelete="RESTRICT", onupdate="CASCADE"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"])

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("specifications", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('draft', 'published', 'inactive')", name="ck_products_status"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="RESTRICT", onupdate="CASCADE"),
        sa.UniqueConstraint("slug", name="uq_products_slug"),
    )
    op.create_index("ix_products_slug", "products", ["slug"])

    op.create_table(
        "variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("option_values", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("option_signature", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT", onupdate="CASCADE"),
        sa.UniqueConstraint("product_id", "option_signature", name="uq_variants_product_signature"),
        sa.UniqueConstraint("id", "product_id", name="uq_variants_id_product"),
    )
    op.create_index("ix_variants_product_id", "variants", ["product_id"])

    op.create_table(
        "skus",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("price >= 0", name="ck_skus_price_nonnegative"),
        sa.CheckConstraint("stock_quantity >= 0", name="ck_skus_stock_nonnegative"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT", onupdate="CASCADE"),
        sa.ForeignKeyConstraint(
            ["variant_id", "product_id"],
            ["variants.id", "variants.product_id"],
            name="fk_skus_variant_same_product",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.UniqueConstraint("code", name="uq_skus_code"),
        sa.UniqueConstraint("variant_id", name="uq_skus_variant_id"),
    )
    op.create_index("ix_skus_code", "skus", ["code"])
    op.create_index("ix_skus_product_id", "skus", ["product_id"])

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("variant_id", sa.Integer(), nullable=True),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False, server_default="gallery"),
        sa.Column("alt_text", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.CheckConstraint(
            "(product_id IS NOT NULL AND variant_id IS NULL) OR (product_id IS NULL AND variant_id IS NOT NULL)",
            name="ck_assets_one_owner",
        ),
        sa.CheckConstraint("sort_order >= 0", name="ck_assets_sort_order_nonnegative"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT", onupdate="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["variants.id"], ondelete="RESTRICT", onupdate="CASCADE"),
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION readysafe_prevent_category_cycle()
        RETURNS trigger AS $$
        DECLARE
            cycle_found boolean;
        BEGIN
            IF NEW.parent_id IS NULL THEN
                RETURN NEW;
            END IF;
            IF NEW.id IS NOT NULL AND NEW.parent_id = NEW.id THEN
                RAISE EXCEPTION 'category cannot be its own parent';
            END IF;

            WITH RECURSIVE ancestors AS (
                SELECT id, parent_id FROM categories WHERE id = NEW.parent_id
                UNION ALL
                SELECT c.id, c.parent_id
                FROM categories c
                JOIN ancestors a ON c.id = a.parent_id
            )
            SELECT EXISTS(SELECT 1 FROM ancestors WHERE id = NEW.id) INTO cycle_found;

            IF cycle_found THEN
                RAISE EXCEPTION 'category hierarchy cycle is not allowed';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_categories_prevent_cycle
        BEFORE INSERT OR UPDATE OF parent_id ON categories
        FOR EACH ROW EXECUTE FUNCTION readysafe_prevent_category_cycle();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_categories_prevent_cycle ON categories")
    op.execute("DROP FUNCTION IF EXISTS readysafe_prevent_category_cycle()")
    op.drop_table("assets")
    op.drop_index("ix_skus_product_id", table_name="skus")
    op.drop_index("ix_skus_code", table_name="skus")
    op.drop_table("skus")
    op.drop_index("ix_variants_product_id", table_name="variants")
    op.drop_table("variants")
    op.drop_index("ix_products_slug", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_table("categories")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
